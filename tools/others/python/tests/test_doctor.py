import subprocess

import pytest

from recordkit import doctor, publish


def _repo(tmp_path, config="", records=("2026-07-06_23-22.md",), layout="tools"):
    """A checkout: <root>/tools/hugo/hugo.yaml + a records dir with timestamp records."""
    hugo = (tmp_path / "tools" / "hugo") if layout == "tools" else (tmp_path / "hugo")
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text(config or "contentDir: ../../records\n", encoding="utf-8")
    if records is not None:
        rec = tmp_path / "records"
        rec.mkdir(parents=True, exist_ok=True)
        for name in records:
            (rec / name).write_text("---\ntitle: One\ndate: 2026-07-06T23:22:00+01:00\n---\n\n"
                                    "## Human\n\nhi\n", encoding="utf-8")
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "build.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    return tmp_path


class _Runner:
    """Stands in for doctor._run: canned hugo/git/pypdf answers, records argv."""

    def __init__(self, hugo="hugo v0.164.0+extended linux/amd64\n",
                 branch="main", remotes="origin\n", pypdf=False, git=True):
        self.calls = []
        self.hugo, self.branch, self.remotes, self.pypdf, self.git = \
            hugo, branch, remotes, pypdf, git

    def __call__(self, argv, cwd=None):
        self.calls.append(list(argv))
        if argv[0] == "hugo":
            return subprocess.CompletedProcess(argv, 0, stdout=self.hugo, stderr="")
        if argv[0] == "git":
            if not self.git:
                return subprocess.CompletedProcess(argv, 128, stdout="",
                                                   stderr="not a git repository")
            out = self.branch + "\n" if "rev-parse" in argv else self.remotes
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        if "import pypdf" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0 if self.pypdf else 1, stdout="", stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")


def _tools(*present):
    return lambda name: ("/usr/bin/" + name) if name in present else None


def _healthy(monkeypatch, runner=None, tools=("hugo", "rsync")):
    monkeypatch.setattr(doctor, "_run", runner or _Runner())
    monkeypatch.setattr(doctor, "_which", _tools(*tools))


def _check(result, name):
    return next(c for c in result["checks"] if c["name"] == name)


# --- the URL ladder, mirroring bin/build.sh -----------------------------------

def test_config_base_url_wins_over_env():
    rung, url = doctor.resolve_url("baseURL: https://example.org/site/\n",
                                   {"BASE_URL": "https://other/"})
    assert rung == "baseURL" and url == "https://example.org/site/"


def test_commented_base_url_is_not_set():
    rung, _ = doctor.resolve_url("# baseURL: https://example.org/\n", {})
    assert rung is None


def test_base_url_env_is_second_rung():
    assert doctor.resolve_url("", {"BASE_URL": "https://x/"}) == ("BASE_URL", "https://x/")


def test_pages_host_derivation():
    env = {"PAGES_HOST": "p.xil.no", "GITHUB_REPOSITORY": "blyant/records"}
    assert doctor.resolve_url("", env) == ("PAGES_HOST", "https://blyant.p.xil.no/records/")


def test_pages_host_repo_named_pages_serves_domain_root():
    env = {"PAGES_HOST": "codeberg.page", "GITHUB_REPOSITORY": "tb4/pages"}
    assert doctor.resolve_url("", env)[1] == "https://tb4.codeberg.page/"


def test_codeberg_derivation():
    env = {"GITHUB_REPOSITORY": "blyant/records", "GITHUB_SERVER_URL": "https://codeberg.org"}
    assert doctor.resolve_url("", env) == ("codeberg", "https://blyant.codeberg.page/records/")


def test_ci_pages_url_is_last_rung():
    assert doctor.resolve_url("", {"CI_PAGES_URL": "https://g/x"}) == ("CI_PAGES_URL",
                                                                       "https://g/x")


def test_no_rung_resolves():
    assert doctor.resolve_url("", {}) == (None, None)


# --- config discovery ---------------------------------------------------------

def test_missing_hugo_config_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    result = doctor.diagnose(tmp_path, env={"BASE_URL": "https://x/"})
    assert _check(result, "config")["level"] == "error"
    assert result["ok"] is False and result["errors"] >= 1


# gap 8: the report must not present an assumed records dir as a finding.
def test_doctor_says_the_records_dir_was_assumed(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    result = doctor.diagnose(tmp_path, env={"BASE_URL": "https://x/"})
    assert result["records_dir_source"] == "assumed"
    c = _check(result, "config")
    assert c["level"] == "error" and "is assumed, not found" in c["message"]
    assert str((tmp_path / "records").resolve()) in c["message"]


def test_doctor_says_the_records_dir_was_found_without_a_config(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    (tmp_path / "records").mkdir()
    result = doctor.diagnose(tmp_path, env={"BASE_URL": "https://x/"})
    assert result["records_dir_source"] == "discovered"
    c = _check(result, "config")
    assert c["level"] == "error" and "nothing configures it" in c["message"]


def test_doctor_calls_a_contentdir_answer_config(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\n")
    assert doctor.diagnose(repo, env={"BASE_URL": "https://x/"})["records_dir_source"] == "config"


def test_content_dir_pointing_nowhere_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../nowhere\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "config")
    assert c["level"] == "error" and "nowhere" in c["message"]


def test_healthy_checkout_has_no_errors(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nbaseURL: https://x/\n")
    result = doctor.diagnose(repo, env={})
    assert result["errors"] == 0 and result["ok"] is True
    assert _check(result, "config")["level"] == "ok"


# --- the URL check ------------------------------------------------------------

def test_unresolvable_url_without_ci_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    c = _check(doctor.diagnose(_repo(tmp_path), env={}), "url")
    assert c["level"] == "error" and c["remedy"]


def test_unresolvable_url_with_a_ci_workflow_is_a_warning(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path)
    (repo / ".forgejo" / "workflows").mkdir(parents=True)
    (repo / ".forgejo" / "workflows" / "pages.yml").write_text("name: x\n", encoding="utf-8")
    c = _check(doctor.diagnose(repo, env={}), "url")
    assert c["level"] == "warn" and "BASE_URL" in c["remedy"]


def test_url_check_names_the_winning_rung(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    c = _check(doctor.diagnose(_repo(tmp_path), env={"CI_PAGES_URL": "https://g/x"}), "url")
    assert c["level"] == "ok" and "CI_PAGES_URL" in c["message"]


# --- records ------------------------------------------------------------------

def test_empty_records_dir_warns_without_demo_mode(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, records=())
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "records")
    assert c["level"] == "warn"


def test_empty_records_dir_is_fine_with_demo_mode(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  demoMode: true\n",
                 records=())
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "records")
    assert c["level"] == "ok"


def test_unparseable_date_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path)
    (repo / "records" / "bad.md").write_text("---\ntitle: Bad\ndate: not-a-date\n---\n",
                                             encoding="utf-8")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "records")
    assert c["level"] == "error" and "bad.md" in c["message"]


def test_quoted_and_date_only_values_parse(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path)
    (repo / "records" / "a.md").write_text('---\ndate: "2026-07-06T23:22:00Z"\n---\n',
                                           encoding="utf-8")
    (repo / "records" / "b.md").write_text("---\ndate: 2026-07-06\n---\n", encoding="utf-8")
    assert _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}),
                  "records")["level"] == "ok"


def test_reserved_demo_key_in_a_record_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path)
    (repo / "records" / "d.md").write_text("---\ntitle: D\ndemo: true\n---\n", encoding="utf-8")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "records")
    assert c["level"] == "warn" and "demo" in c["message"]


# --- toolchain ----------------------------------------------------------------

def test_missing_hugo_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=())
    c = _check(doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"}), "hugo")
    assert c["level"] == "error" and "not found" in c["message"]


def test_hugo_older_than_the_theme_needs_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(hugo="hugo v0.140.2+extended linux/amd64\n"))
    c = _check(doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"}), "hugo")
    assert c["level"] == "error" and "0.158" in c["remedy"]


def test_current_hugo_is_ok(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    c = _check(doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"}), "hugo")
    assert c["level"] == "ok" and "0.164" in c["message"]


def test_book_params_without_pandoc_warn(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=("hugo",))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  pdf: x.pdf\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "books")
    assert c["level"] == "warn" and "pandoc" in c["message"] and "weasyprint" in c["message"]


def test_booklet_without_pypdf_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=("hugo", "pandoc", "weasyprint"))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  booklet: b.pdf\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "books")
    assert c["level"] == "warn" and "pypdf" in c["message"]


def test_book_toolchain_complete_is_ok(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(pypdf=True),
             tools=("hugo", "pandoc", "weasyprint"))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  booklet: b.pdf\n")
    assert _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}),
                  "books")["level"] == "ok"


def test_no_book_params_means_no_book_check(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=("hugo",))
    result = doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"})
    assert not [c for c in result["checks"] if c["name"] == "books"]


# --- publishing ---------------------------------------------------------------

def test_unknown_publish_target_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  publishTarget: ftp\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "error" and "ftp" in c["message"]


def test_rsync_target_without_dest_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  publishTarget: rsync\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "error" and "publishDest" in c["message"]


def test_rsync_dest_at_the_root_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  publishTarget: rsync\n  publishDest: user@host:/\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "error" and "--delete" in c["remedy"]


def test_rsync_target_without_the_rsync_binary_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=("hugo",))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  publishTarget: rsync\n  publishDest: /srv/www/x\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "rsync")
    assert c["level"] == "warn"


def test_pages_branch_without_the_remote_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(remotes="codeberg\n"))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  publishTarget: pages-branch\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "warn" and "origin" in c["message"]


def test_deploy_command_pointing_nowhere_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  deployCommand: ./deploy.sh\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "deploy")
    assert c["level"] == "warn" and "deploy.sh" in c["message"]


def test_deploy_command_that_exists_is_ok(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  deployCommand: ./deploy.sh\n")
    (repo / "deploy.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    assert _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}),
                  "deploy")["level"] == "ok"


def test_no_publish_path_at_all_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    c = _check(doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "warn" and "nothing publishes" in c["message"]


def test_a_ci_workflow_is_a_publish_path(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path)
    (repo / ".gitlab-ci.yml").write_text("pages:\n", encoding="utf-8")
    assert _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}),
                  "publish")["level"] == "ok"


# --- git (never an error: CI checks out detached) -----------------------------

def test_detached_head_only_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(branch="HEAD"))
    result = doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"})
    c = _check(result, "branch")
    assert c["level"] == "warn" and "detached" in c["message"] and result["errors"] == 0


def test_branch_other_than_repo_branch_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(branch="draft"))
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  repoBranch: main\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "branch")
    assert c["level"] == "warn" and "draft" in c["message"]


def test_no_remote_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(remotes="\n"))
    c = _check(doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"}), "git")
    assert c["level"] == "warn" and "remote" in c["message"]


def test_not_a_git_checkout_warns(tmp_path, monkeypatch):
    _healthy(monkeypatch, runner=_Runner(git=False))
    result = doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"})
    assert _check(result, "git")["level"] == "warn" and result["errors"] == 0


# --- output -------------------------------------------------------------------

def test_render_names_every_fault(tmp_path, monkeypatch):
    _healthy(monkeypatch, tools=())
    repo = _repo(tmp_path, config="contentDir: ../../nowhere\nparams:\n  publishTarget: ftp\n")
    text = doctor.render(doctor.diagnose(repo, env={}))
    for fragment in ("config", "nowhere", "url", "hugo", "publish", "ftp", "error"):
        assert fragment in text


def test_main_json_and_exit_codes(tmp_path, monkeypatch, capsys):
    import json
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nbaseURL: https://x/\n")
    assert doctor.main(["--repo", str(repo), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["checks"]

    broken = _repo(tmp_path / "broken", config="contentDir: ../../nowhere\n")
    assert doctor.main(["--repo", str(broken)]) == 1
    assert "error" in capsys.readouterr().out


def test_the_doctor_writes_nothing(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n  pdf: x.pdf\n")
    before = {p: (p.stat().st_mtime, p.stat().st_size) for p in sorted(repo.rglob("*"))}
    doctor.diagnose(repo, env={})
    after = {p: (p.stat().st_mtime, p.stat().st_size) for p in sorted(repo.rglob("*"))}
    assert before == after


def test_theme_directory_present_is_ok(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\ntheme: Fuglekasse\n")
    (repo / "tools" / "hugo" / "themes" / "Fuglekasse").mkdir(parents=True)
    result = doctor.diagnose(repo, env={"BASE_URL": "https://x/"})
    assert _check(result, "theme")["level"] == "ok"


def test_theme_typo_is_an_error(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\ntheme: postkasse\n")
    (repo / "tools" / "hugo" / "themes" / "Fuglekasse").mkdir(parents=True)
    (repo / "tools" / "hugo" / "themes" / "Postkasse").mkdir(parents=True)
    result = doctor.diagnose(repo, env={"BASE_URL": "https://x/"})
    c = _check(result, "theme")
    assert c["level"] == "error"
    assert "postkasse" in c["message"]
    assert "Postkasse" in c["remedy"] and "case-sensitive" in c["remedy"]
    assert result["ok"] is False


def test_no_theme_key_means_no_theme_check(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    result = doctor.diagnose(_repo(tmp_path), env={"BASE_URL": "https://x/"})
    assert not [c for c in result["checks"] if c["name"] == "theme"]


# gap 6: doctor and publish must agree — one judgement, two commands.
@pytest.mark.parametrize("dest", ["/home/tb4", "/srv", "~", "$HOME/www", "user@host:/home/tb4"])
def test_doctor_reports_every_dest_publish_refuses(tmp_path, monkeypatch, dest):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  f"  publishTarget: rsync\n  publishDest: {dest}\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "error" and dest in c["message"]
    with pytest.raises(RuntimeError):
        publish.check_publish_dest(dest)


def test_doctor_still_passes_a_legitimate_dest(tmp_path, monkeypatch):
    _healthy(monkeypatch)
    repo = _repo(tmp_path, config="contentDir: ../../records\nparams:\n"
                                  "  publishTarget: rsync\n  publishDest: user@host:/var/www/site\n")
    c = _check(doctor.diagnose(repo, env={"BASE_URL": "https://x/"}), "publish")
    assert c["level"] == "ok" and "rsync →" in c["message"]

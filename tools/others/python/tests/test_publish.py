import json
import subprocess

import pytest

from recordkit import cli, publish


def _repo(tmp_path, params="", layout="tools"):
    hugo = (tmp_path / "tools" / "hugo") if layout == "tools" else (tmp_path / "hugo")
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("params:\n" + params, encoding="utf-8")
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "build.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (tmp_path / "public").mkdir()
    (tmp_path / "public" / "index.html").write_text("<html></html>", encoding="utf-8")
    return tmp_path


class _Recorder:
    """Stands in for publish._run; records argv, optionally fails on a marker."""

    def __init__(self, fail=()):
        self.calls = []
        self.fail = fail

    def __call__(self, argv, cwd=None):
        self.calls.append(list(argv))
        rc = 1 if any(f in argv for f in self.fail) else 0
        out = "ssh://example/records.git\n" if "get-url" in argv else ""
        return subprocess.CompletedProcess(argv, rc, stdout=out, stderr="boom" if rc else "")


def test_pages_branch_push_sequence(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, yes=True)
    assert rec.calls[0][0] == "bash" and rec.calls[0][1].endswith("bin/build.sh")
    assert rec.calls[1] == ["git", "-C", str(repo), "remote", "get-url", "origin"]
    assert "init" in rec.calls[2] and "add" in rec.calls[3] and "commit" in rec.calls[4]
    assert "--force" in rec.calls[5]
    assert rec.calls[5][-2:] == ["ssh://example/records.git", "HEAD:refs/heads/pages"]
    assert (repo / "public" / ".nojekyll").exists()
    assert not (repo / "public" / ".git").exists()
    assert out["pushed"] is True and out["target"] == "pages-branch"
    assert out["remote_url"] == "ssh://example/records.git"


def test_pages_branch_custom_branch_and_remote(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n"
                           "  publishBranch: www\n  publishRemote: smoke\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, yes=True)
    assert rec.calls[1][-1] == "smoke"
    assert rec.calls[5][-1] == "HEAD:refs/heads/www"
    assert out["branch"] == "www" and out["remote"] == "smoke"


def test_pages_branch_dry_run(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, dry_run=True)
    assert len(rec.calls) == 2  # build + get-url, no git init/push
    assert out["pushed"] is False and out["dry_run"] is True and out["files"] == 1
    assert not (repo / "public" / ".nojekyll").exists()


def test_rsync_argv(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: rsync\n"
                           "  publishDest: user@host:/var/www/site/\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo)
    assert rec.calls[-1] == ["rsync", "-az", "--delete",
                             str(repo / "public") + "/", "user@host:/var/www/site/"]
    assert out["synced"] is True and out["target"] == "rsync"


def test_rsync_dry_run(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: rsync\n  publishDest: /srv/www/x\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, dry_run=True)
    assert "-n" in rec.calls[-1] and "--itemize-changes" in rec.calls[-1]
    assert out["synced"] is False and "changes" in out


def test_rsync_requires_dest(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: rsync\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    with pytest.raises(RuntimeError, match="publishDest"):
        publish.publish(repo)


def test_rsync_refuses_root_dest(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: rsync\n  publishDest: user@host:/\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    with pytest.raises(RuntimeError, match="refusing"):
        publish.publish(repo)


# ------------------------------------------------------------------ asking first

def _no(*a):
    return False


def _yes(*a):
    return True


class _Stdin:
    """A stdin that is or is not a terminal, and answers when asked."""

    def __init__(self, tty: bool, answer: str = ""):
        self._tty, self._answer = tty, answer

    def isatty(self):
        return self._tty

    def readline(self):
        return self._answer


def test_the_force_push_asks_first(tmp_path, monkeypatch):
    """The default is a question, not a push — this is the whole of gap 5."""
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    seen = []
    out = publish.publish(repo, confirm=lambda *a: seen.append(a) or True)
    assert seen == [("ssh://example/records.git", "pages", 1)]
    assert out["pushed"] is True


def test_a_declined_confirmation_pushes_nothing(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, confirm=_no)
    assert len(rec.calls) == 2  # build + get-url, and then it stopped
    assert out["pushed"] is False and out["cancelled"] is True
    assert out["files"] == 1  # it still says what it would have pushed
    assert not (repo / "public" / ".nojekyll").exists()


def test_yes_skips_the_question(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    asked = []
    out = publish.publish(repo, yes=True, confirm=lambda *a: asked.append(a) or False)
    assert asked == [] and out["pushed"] is True


def test_dry_run_never_asks(tmp_path, monkeypatch):
    """Nothing is delivered, so there is nothing to confirm."""
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    out = publish.publish(repo, dry_run=True, confirm=_no)
    assert out["pushed"] is False and "cancelled" not in out


def test_rsync_is_unchanged(tmp_path, monkeypatch):
    """gap 5 is about the force-push; the rsync target keeps its publishDest guard."""
    repo = _repo(tmp_path, "  publishTarget: rsync\n  publishDest: u@h:/var/www/s/\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo, confirm=_no)
    assert out["synced"] is True


# ------------------------------------------------------------------ ask(), the real prompt

def test_a_non_interactive_stdin_refuses(monkeypatch, capsys):
    """Never a silent yes — the rule redact.ask set, applied to the force-push."""
    monkeypatch.setattr(publish.sys, "stdin", _Stdin(tty=False))
    assert publish.ask("ssh://example/records.git", "pages", 42) is False
    err = capsys.readouterr().err
    assert "stdin is not a terminal" in err and "--yes" in err


def test_the_question_names_what_it_overwrites(monkeypatch, capsys):
    monkeypatch.setattr(publish.sys, "stdin", _Stdin(tty=True, answer="y\n"))
    assert publish.ask("ssh://example/records.git", "pages", 42) is True
    err = capsys.readouterr().err
    assert "ssh://example/records.git" in err and "pages" in err and "42" in err
    assert "replaces" in err


@pytest.mark.parametrize("answer, expected", [
    ("y\n", True), ("Y\n", True), ("yes\n", True), ("YES\n", True),
    ("n\n", False), ("\n", False), ("", False), ("maybe\n", False),
])
def test_only_yes_means_yes(monkeypatch, answer, expected):
    monkeypatch.setattr(publish.sys, "stdin", _Stdin(tty=True, answer=answer))
    assert publish.ask("ssh://e/r.git", "pages", 1) is expected


def test_a_non_interactive_publish_refuses_end_to_end(tmp_path, monkeypatch, capsys):
    """The path CI and /cpd take: no --yes, no terminal — it must refuse, not push."""
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    monkeypatch.setattr(publish.sys, "stdin", _Stdin(tty=False))
    out = publish.publish(repo)
    assert out["pushed"] is False and out["cancelled"] is True
    assert not any("--force" in c for c in rec.calls)
    assert "--yes" in capsys.readouterr().err


def test_unset_target_errors(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    monkeypatch.setattr(publish, "_run", _Recorder())
    with pytest.raises(RuntimeError, match="publishTarget unset"):
        publish.publish(repo)


def test_commented_target_is_unset(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  # publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    with pytest.raises(RuntimeError, match="publishTarget unset"):
        publish.publish(repo)


def test_unknown_target_errors(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: ftp\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    with pytest.raises(RuntimeError, match="unknown publishTarget"):
        publish.publish(repo)


def test_missing_remote_errors(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder(fail=("get-url",)))
    with pytest.raises(RuntimeError, match="not found"):
        publish.publish(repo)


def test_build_failure_stops(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    rec = _Recorder(fail=("bash",))
    monkeypatch.setattr(publish, "_run", rec)
    with pytest.raises(RuntimeError, match="boom"):
        publish.publish(repo)
    assert len(rec.calls) == 1


def test_no_config_errors(tmp_path):
    with pytest.raises(RuntimeError, match="hugo.yaml"):
        publish.publish(tmp_path)


def test_plain_hugo_layout_root(tmp_path, monkeypatch):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n", layout="plain")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    out = publish.publish(repo)
    assert out["repo"] == str(tmp_path)
    assert rec.calls[0][1] == str(tmp_path / "bin" / "build.sh")


def test_cli_publish_json(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    rc = cli.main(["publish", "--repo", str(repo), "--dry-run"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["dry_run"] is True and out["built"] is True


def test_cli_publish_yes(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    rc = cli.main(["publish", "--repo", str(repo), "--yes"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["pushed"] is True


def test_cli_publish_without_yes_refuses_off_a_terminal(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path, "  publishTarget: pages-branch\n")
    monkeypatch.setattr(publish, "_run", _Recorder())
    monkeypatch.setattr(publish.sys, "stdin", _Stdin(tty=False))
    rc = cli.main(["publish", "--repo", str(repo)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["pushed"] is False and out["cancelled"] is True


def test_cli_publish_error_json(tmp_path, capsys):
    rc = cli.main(["publish", "--repo", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and "error" in out


# --- gap 6: the `rsync --delete` destination guard -----------------------------
#
# The guard used to be one string comparison (`""`, `"/"`, `"~"` and trailing
# slashes). Everything in REFUSED below walked straight through it. Each form is
# asserted on its own so a regression names which one came back.

REFUSED = [
    ("/", "the filesystem root"),
    ("//", "the root, written twice"),
    (".", "the directory publish runs in"),
    ("~", "the home directory, bare"),
    ("~/", "the home directory with a trailing slash"),
    ("~/.", "the home directory, spelled the long way"),
    ("~/Documents/../..", "a climb back out of home"),
    ("..", "the parent of the working directory"),
    ("../..", "two levels up"),
    ("/home/tb4", "a Linux home directory written out"),
    ("/home/tb4/", "the same with a trailing slash"),
    ("/Users/tb4", "a macOS home directory"),
    ("/var/home/tb4", "an ostree home directory"),
    ("/usr/home/tb4", "a BSD home directory"),
    ("/var/home", "the parent of every ostree home"),
    ("/home", "the parent of every home"),
    ("/root", "root's home, and a top-level directory"),
    ("/srv", "a top-level directory, one above a webroot"),
    ("/srv/www/../..", "a webroot that normalises back to the root"),
    ("$HOME/www", "an unexpanded variable"),
    ("${HOME}/www", "the braced form"),
    ("user@host:", "a remote login directory"),
    ("user@host:/", "the remote root"),
    ("user@host:~", "the remote home"),
    ("user@host:/home/tb4", "a remote home written out"),
    ("user@host:~/../other", "a climb out of the remote home"),
    ("user@host:$HOME/www", "an unexpanded variable on a remote"),
    ("user@host:/srv", "a remote top-level directory"),
]

ACCEPTED = [
    "user@host:/var/www/site/",
    "user@host:/srv/www/records",
    "user@host:~/public_html",
    "user@host:~tb4/public_html",
    "/srv/www/x",
    "/var/www/localhost/htdocs",
    "/home/tb4/www",
]


@pytest.mark.parametrize("dest,why", REFUSED, ids=[d for d, _ in REFUSED])
def test_publish_dest_refused(dest, why):
    assert publish.publish_dest_problem(dest) is not None, why


@pytest.mark.parametrize("dest", ACCEPTED)
def test_publish_dest_accepted(dest):
    assert publish.publish_dest_problem(dest) is None


def test_publish_dest_refuses_empty_and_blank():
    assert publish.publish_dest_problem("") is not None
    assert publish.publish_dest_problem("   ") is not None


def test_publish_dest_accepts_a_real_local_directory(tmp_path):
    """A legitimate local webroot must still pass, symlinks resolved and all."""
    webroot = tmp_path / "srv" / "www"
    webroot.mkdir(parents=True)
    assert publish.publish_dest_problem(str(webroot)) is None


def test_publish_dest_refuses_a_symlink_into_a_home(tmp_path, monkeypatch):
    """The string says /srv/www; the filesystem says $HOME. Only a local check sees it."""
    home = tmp_path / "home" / "tb4"
    home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    link = tmp_path / "webroot"
    link.symlink_to(home, target_is_directory=True)
    assert publish.publish_dest_problem(str(link)) is not None


def test_publish_dest_judges_a_remote_path_as_a_string_only(tmp_path, monkeypatch):
    """A remote path that happens to exist locally is not resolved against this machine."""
    home = tmp_path / "home" / "tb4"
    home.mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    link = tmp_path / "webroot"
    link.symlink_to(home, target_is_directory=True)
    assert publish.publish_dest_problem(f"user@host:{link}") is None


@pytest.mark.parametrize("dest", ["/home/tb4", "~", "/srv", "user@host:$HOME/www"])
def test_rsync_refuses_through_publish(tmp_path, monkeypatch, dest):
    repo = _repo(tmp_path, f"  publishTarget: rsync\n  publishDest: {dest}\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    with pytest.raises(RuntimeError, match="refusing publishDest"):
        publish.publish(repo)
    assert not any(c[0] == "rsync" for c in rec.calls)


@pytest.mark.parametrize("dest", ["/home/tb4", "~", "/srv", "user@host:$HOME/www"])
def test_rsync_dry_run_refuses_exactly_what_a_real_run_refuses(tmp_path, monkeypatch, dest):
    repo = _repo(tmp_path, f"  publishTarget: rsync\n  publishDest: {dest}\n")
    rec = _Recorder()
    monkeypatch.setattr(publish, "_run", rec)
    with pytest.raises(RuntimeError, match="refusing publishDest"):
        publish.publish(repo, dry_run=True)
    assert not any(c[0] == "rsync" for c in rec.calls)

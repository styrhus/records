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
    out = publish.publish(repo)
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
    out = publish.publish(repo)
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


def test_cli_publish_error_json(tmp_path, capsys):
    rc = cli.main(["publish", "--repo", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and "error" in out

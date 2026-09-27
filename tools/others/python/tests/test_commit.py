# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import subprocess

from recordkit import commit


def _cfg(tmp_path, params=""):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("params:\n" + params, encoding="utf-8")
    return tmp_path


def test_deploy_command_runs(tmp_path, monkeypatch):
    _cfg(tmp_path, "  deployCommand: echo hi\n")
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="hi\n", stderr="")

    monkeypatch.setattr(commit.subprocess, "run", fake_run)
    out = commit._deploy(tmp_path)
    assert out["method"] == "deployCommand" and out["ran"] is True
    assert seen["cmd"] == "echo hi"


def test_deploy_command_beats_workflow(tmp_path, monkeypatch):
    _cfg(tmp_path, "  deployCommand: echo hi\n")
    wf = tmp_path / ".forgejo" / "workflows"
    wf.mkdir(parents=True)
    (wf / "pages.yml").write_text("name: x\n")
    monkeypatch.setattr(commit.subprocess, "run",
                        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "", ""))
    assert commit._deploy(tmp_path)["method"] == "deployCommand"


def test_commented_deploy_command_ignored(tmp_path):
    _cfg(tmp_path, "  # deployCommand: echo hi\n")
    assert commit._deploy(tmp_path)["method"] is None


def test_workflow_dir_forgejo(tmp_path):
    _cfg(tmp_path)
    wf = tmp_path / ".forgejo" / "workflows"
    wf.mkdir(parents=True)
    (wf / "pages.yml").write_text("name: x\n")
    out = commit._deploy(tmp_path)
    assert out["method"] == "workflow" and ".forgejo/workflows" in out["note"]


def test_workflow_dir_github(tmp_path):
    _cfg(tmp_path)
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "pages.yml").write_text("name: x\n")
    out = commit._deploy(tmp_path)
    assert out["method"] == "workflow" and ".github/workflows" in out["note"]


def test_gitlab_ci_file(tmp_path):
    _cfg(tmp_path)
    (tmp_path / ".gitlab-ci.yml").write_text("pages:\n")
    out = commit._deploy(tmp_path)
    assert out["method"] == "workflow" and ".gitlab-ci.yml" in out["note"]


def test_empty_workflow_dir_falls_through(tmp_path):
    _cfg(tmp_path)
    (tmp_path / ".forgejo" / "workflows").mkdir(parents=True)
    assert commit._deploy(tmp_path)["method"] is None


def test_no_method(tmp_path):
    _cfg(tmp_path)
    assert commit._deploy(tmp_path)["method"] is None

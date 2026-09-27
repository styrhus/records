# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import subprocess

from recordkit import watch


def _repo(tmp_path, records=("2026-07-06_23-22.md",)):
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("contentDir: ../../records\n", encoding="utf-8")
    rec = tmp_path / "records"
    rec.mkdir()
    for name in records:
        (rec / name).write_text("---\ntitle: One\n---\n", encoding="utf-8")
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "build.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    return tmp_path


class _Runner:
    """Stands in for watch._run; records argv (and env), fails when asked."""

    def __init__(self, fail=False):
        self.calls, self.envs, self.fail = [], [], fail

    def __call__(self, argv, cwd=None, env=None):
        self.calls.append(list(argv))
        self.envs.append(env)
        return subprocess.CompletedProcess(argv, 1 if self.fail else 0,
                                           stdout="", stderr="build failed: boom" if self.fail else "")


class _Sleeper:
    """An injected sleep that mutates the tree on the given poll numbers."""

    def __init__(self, actions=None):
        self.count, self.actions = 0, actions or {}

    def __call__(self, _seconds):
        self.count += 1
        action = self.actions.get(self.count)
        if action:
            action()


def _touch(path, text="---\ntitle: New\n---\n"):
    return lambda: path.write_text(text, encoding="utf-8")


def _run_watch(repo, monkeypatch, runner=None, sleeper=None, **kw):
    runner = runner or _Runner()
    monkeypatch.setattr(watch, "_run", runner)
    events = []
    watch.watch(repo, interval=0, once=True, sleep=sleeper or _Sleeper(),
                emit=events.append, **kw)
    return runner, events


# --- snapshot / diff ----------------------------------------------------------

def test_snapshot_sees_every_record(tmp_path):
    repo = _repo(tmp_path, records=("a.md", "b.md"))
    assert set(watch.snapshot(repo / "records")) == {"a.md", "b.md"}


def test_snapshot_prunes_dot_dirs(tmp_path):
    repo = _repo(tmp_path, records=("a.md",))
    (repo / "records" / ".git").mkdir()
    (repo / "records" / ".git" / "HEAD").write_text("ref\n", encoding="utf-8")
    assert set(watch.snapshot(repo / "records")) == {"a.md"}


def test_snapshot_of_a_missing_dir_is_empty(tmp_path):
    assert watch.snapshot(tmp_path / "gone") == {}


def test_diff_reports_added_changed_and_removed():
    old = {"a.md": (1.0, 10), "b.md": (1.0, 10)}
    new = {"a.md": (2.0, 12), "c.md": (1.0, 5)}
    assert watch.diff(old, new) == {"added": ["c.md"], "changed": ["a.md"], "removed": ["b.md"]}


# --- the loop -----------------------------------------------------------------

def test_a_change_triggers_exactly_one_build(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    runner, events = _run_watch(repo, monkeypatch, sleeper=sleeper)
    builds = [c for c in runner.calls if "build.sh" in " ".join(c)]
    assert len(builds) == 1
    assert events[-1]["ok"] is True and events[-1]["changed"]["added"] == ["new.md"]


def test_a_burst_of_saves_debounces_into_one_build(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "one.md"),
                        2: _touch(repo / "records" / "two.md"),
                        3: _touch(repo / "records" / "three.md")})
    runner, events = _run_watch(repo, monkeypatch, sleeper=sleeper)
    assert len([c for c in runner.calls if "build.sh" in " ".join(c)]) == 1
    assert sorted(events[-1]["changed"]["added"]) == ["one.md", "three.md", "two.md"]


def test_no_change_means_no_build(tmp_path, monkeypatch):
    runner, events = _run_watch(_repo(tmp_path), monkeypatch)
    assert runner.calls == [] and events == []


def test_a_deleted_record_is_a_change(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: lambda: (repo / "records" / "2026-07-06_23-22.md").unlink()})
    _, events = _run_watch(repo, monkeypatch, sleeper=sleeper)
    assert events[-1]["changed"]["removed"] == ["2026-07-06_23-22.md"]


def test_a_broken_build_is_reported_not_fatal(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    _, events = _run_watch(repo, monkeypatch, runner=_Runner(fail=True), sleeper=sleeper)
    assert events[-1]["ok"] is False and "boom" in events[-1]["output"]


def test_a_vanished_records_dir_is_survived(tmp_path, monkeypatch):
    import shutil
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: lambda: shutil.rmtree(repo / "records")})
    runner, events = _run_watch(repo, monkeypatch, sleeper=sleeper)
    assert events[-1]["event"] == "missing" and runner.calls == []


def test_ctrl_c_exits_clean(tmp_path, monkeypatch):
    repo = _repo(tmp_path)

    def interrupt(_seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(watch, "_run", _Runner())
    result = watch.watch(repo, interval=0, sleep=interrupt, emit=lambda e: None)
    assert result["stopped"] is True and result["builds"] == 0


def test_base_url_and_outdir_reach_the_one_build_path(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    runner, _ = _run_watch(repo, monkeypatch, sleeper=sleeper,
                           base_url="https://x/", outdir=str(tmp_path / "out"))
    build = [c for c in runner.calls if "build.sh" in " ".join(c)][0]
    assert build[0] == "bash" and build[1].endswith("bin/build.sh")
    assert build[2] == str(tmp_path / "out")
    assert runner.envs[0]["BASE_URL"] == "https://x/"


def test_the_watcher_never_commits_pushes_or_publishes(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    runner, _ = _run_watch(repo, monkeypatch, runner=_Runner(fail=True), sleeper=sleeper,
                           notify_mode="all")
    for argv in runner.calls:
        assert not {"commit", "push", "publish"} & set(argv)


# --- the bark -----------------------------------------------------------------

def test_a_failed_build_barks_once(tmp_path, monkeypatch):
    barks = []
    monkeypatch.setattr(watch, "notify", lambda title, body: barks.append((title, body)))
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    _run_watch(repo, monkeypatch, runner=_Runner(fail=True), sleeper=sleeper)
    assert len(barks) == 1


def test_success_is_quiet_by_default(tmp_path, monkeypatch):
    barks = []
    monkeypatch.setattr(watch, "notify", lambda title, body: barks.append(title))
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    _run_watch(repo, monkeypatch, sleeper=sleeper)
    assert barks == []


def test_notify_all_barks_on_success(tmp_path, monkeypatch):
    barks = []
    monkeypatch.setattr(watch, "notify", lambda title, body: barks.append(title))
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    _run_watch(repo, monkeypatch, sleeper=sleeper, notify_mode="all")
    assert len(barks) == 1


def test_notify_none_stays_silent_on_failure(tmp_path, monkeypatch):
    barks = []
    monkeypatch.setattr(watch, "notify", lambda title, body: barks.append(title))
    repo = _repo(tmp_path)
    sleeper = _Sleeper({1: _touch(repo / "records" / "new.md")})
    _run_watch(repo, monkeypatch, runner=_Runner(fail=True), sleeper=sleeper,
               notify_mode="none")
    assert barks == []


def test_notify_uses_notify_send_when_present(monkeypatch):
    runner = _Runner()
    monkeypatch.setattr(watch, "_run", runner)
    monkeypatch.setattr(watch, "_which", lambda name: "/usr/bin/" + name)
    assert watch.notify("records", "build failed") is True
    assert runner.calls[0][0] == "notify-send" and "build failed" in runner.calls[0]


def test_notify_without_notify_send_is_a_silent_no_op(monkeypatch):
    runner = _Runner()
    monkeypatch.setattr(watch, "_run", runner)
    monkeypatch.setattr(watch, "_which", lambda _name: None)
    assert watch.notify("records", "build failed") is False
    assert runner.calls == []


# --- CLI ----------------------------------------------------------------------

def test_main_once_emits_json_and_exit_codes(tmp_path, monkeypatch, capsys):
    repo = _repo(tmp_path)
    runner = _Runner(fail=True)
    monkeypatch.setattr(watch, "_run", runner)
    monkeypatch.setattr(watch.time, "sleep", _Sleeper({1: _touch(repo / "records" / "n.md")}))
    rc = watch.main(["--repo", str(repo), "--once", "--json", "--interval", "0",
                     "--notify", "none"])
    event = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert rc == 1 and event["ok"] is False and event["event"] == "build"

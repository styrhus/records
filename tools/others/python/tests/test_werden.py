import json

import pytest

from recordkit import werden


def _repo(tmp_path, current=None):
    naming = tmp_path / "tools" / "others" / "naming"
    naming.mkdir(parents=True)
    (naming / "dyr.json").write_text(json.dumps(["flue", "beetle", "cricket"]), encoding="utf-8")
    (naming / "strukturer.json").write_text(json.dumps(["fuglekasse", "postkasse"]),
                                            encoding="utf-8")
    if current is not None:
        (tmp_path / "CURRENT").write_text(current, encoding="utf-8")
    return tmp_path


def test_bump_advances_animal(tmp_path):
    repo = _repo(tmp_path, "0.1.1 fuglekasse-flue\n")
    out = werden.cycle(repo)
    assert out["old"] == "0.1.1 fuglekasse-flue"
    assert out["new"] == "0.1.2 fuglekasse-beetle"
    assert (repo / "CURRENT").read_text() == "0.1.2 fuglekasse-beetle\n"
    assert not out["stamp_only"]


def test_new_structure_resets_animal(tmp_path):
    repo = _repo(tmp_path, "0.1.3 fuglekasse-cricket\n")
    out = werden.cycle(repo, "postkasse")
    assert out["new"] == "0.2.1 postkasse-flue"


def test_offlist_structure_warns_major_zero(tmp_path):
    repo = _repo(tmp_path, "0.1.1 fuglekasse-flue\n")
    out = werden.cycle(repo, "romstasjon")
    assert out["new"] == "0.0.1 romstasjon-flue"
    assert any("strukturer.json" in w for w in out["warnings"])


def test_stamp_keeps_name(tmp_path):
    repo = _repo(tmp_path, "0.1.2 fuglekasse-beetle\n")
    out = werden.cycle(repo, stamp=True)
    assert out["new"] == "0.1.2 fuglekasse-beetle"
    assert out["stamp_only"]


def test_stamp_without_current_errors(tmp_path):
    with pytest.raises(ValueError, match="--stamp"):
        werden.cycle(_repo(tmp_path), stamp=True)


def test_epoch_preserved_verbatim(tmp_path):
    repo = _repo(tmp_path, "3.1.2 fuglekasse-beetle\n")
    assert werden.cycle(repo)["new"] == "3.1.3 fuglekasse-cricket"


def test_legacy_name_only_reads_epoch_zero(tmp_path):
    repo = _repo(tmp_path, "fuglekasse-flue\n")
    assert werden.cycle(repo)["new"] == "0.1.2 fuglekasse-beetle"


def test_missing_current_seeds_first(tmp_path):
    repo = _repo(tmp_path)
    assert werden.cycle(repo)["new"] == "0.1.1 fuglekasse-flue"


def test_last_animal_errors(tmp_path):
    repo = _repo(tmp_path, "0.1.3 fuglekasse-cricket\n")
    with pytest.raises(ValueError, match="last animal"):
        werden.cycle(repo)


def test_unknown_animal_errors(tmp_path):
    repo = _repo(tmp_path, "0.1.9 fuglekasse-drage\n")
    with pytest.raises(ValueError, match="not found"):
        werden.cycle(repo)


def test_stamps_markers_and_skips_exempt_paths(tmp_path):
    repo = _repo(tmp_path, "0.1.1 fuglekasse-flue\n")
    marker = "<!-- werden: 0.1.1 fuglekasse-flue -->"
    (repo / "README.md").write_text("# t\n\n> Fase — 0.1.1 fuglekasse-flue\n")
    docs = repo / "tools" / "others" / "README.md"
    docs.write_text(f"# o\n{marker}\n")
    mirror = repo / "tools" / "others" / "python" / "README.md"
    mirror.parent.mkdir(parents=True)
    mirror.write_text(f"literal {marker}\n")
    skill = repo / ".ai" / "skills" / "werden"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"literal {marker}\n")
    nm = repo / "node_modules"
    nm.mkdir()
    (nm / "x.md").write_text(marker)
    (repo / "blob.bin").write_bytes(b"\0" + marker.encode())

    out = werden.cycle(repo)
    assert out["markers_updated"] == ["tools/others/README.md"]
    assert "<!-- werden: 0.1.2 fuglekasse-beetle -->" in docs.read_text()
    assert marker in (skill / "SKILL.md").read_text()
    assert marker in mirror.read_text()
    assert marker in (nm / "x.md").read_text()
    assert marker.encode() in (repo / "blob.bin").read_bytes()
    assert out["fase_line"]
    assert "> Fase — 0.1.2 fuglekasse-beetle" in (repo / "README.md").read_text()


def test_no_markers_reports_empty(tmp_path):
    repo = _repo(tmp_path, "0.1.1 fuglekasse-flue\n")
    out = werden.cycle(repo)
    assert out["markers_updated"] == []
    assert not out["fase_line"]

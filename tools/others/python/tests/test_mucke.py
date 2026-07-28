import pytest

from recordkit import mucke


def test_stamp_appends_div(tmp_path, monkeypatch):
    monkeypatch.setattr(mucke, "now_playing", lambda: ("Song", "Band"))
    f = tmp_path / "r.md"
    f.write_text("body\n")
    r = mucke.stamp(f)
    assert (r["title"], r["artist"]) == ("Song", "Band")
    text = f.read_text()
    assert text.startswith('body\n\n<div style="text-align:right">')
    assert "Song • Band</div>\n" in text


def test_stamp_nothing_playing(tmp_path, monkeypatch):
    monkeypatch.setattr(mucke, "now_playing", lambda: None)
    f = tmp_path / "r.md"
    f.write_text("body\n")
    with pytest.raises(RuntimeError):
        mucke.stamp(f)

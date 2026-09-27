# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

import pytest

from recordkit import card, turns

RECORD = """---
title: 2026-07-06_23-22
date: 2026-07-06T23:22:58+02:00
---

## Human

Hey! Can you tell me the story of Adam and Eve?

## Assistant

Sure! Adam and Eve are the first humans in Genesis.

— claude-opus-4-8
"""

SITE_CONFIG = """baseURL: https://blyant.codeberg.page/records/
title: blyant records
params:
  dateTitleFormat: "02. January 2006"
  datePostFormat: "02. January 2006 15:04"
  style:
    font: Architects Daughter
    light: { bg: "#111111", fg: "#222222", dim: "#333333", accent: "#444444", surface: "#555555", card: "#666666" }
"""


def _record(tmp_path, text=RECORD, name="2026-07-06_23-22.md"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------- turn parsing

def test_split_keeps_label_name_and_model():
    text = "## Human (Ada)\n\nhi\n\n## Assistant\n\nyo\n\n— qwen2.5:14b\n"
    assert turns.split(text) == [
        {"role": "user", "label": "Human (Ada)", "name": "Ada", "content": "hi", "model": None},
        {"role": "assistant", "label": "Assistant", "name": None, "content": "yo",
         "model": "qwen2.5:14b"},
    ]


def test_split_matches_parse_turns():
    text = "## User\n\nlegacy heading\n\n## Assistant\n\nreply\n\n— m\n"
    assert turns.parse_turns(text) == [
        {"role": "user", "content": "legacy heading"},
        {"role": "assistant", "content": "reply"},
    ]


# ---------------------------------------------------------------- palette

def test_palette_defaults_to_fuglekasse():
    assert card.palette("") == card.LIGHT


def test_palette_reads_inline_flow_map():
    assert card.palette(SITE_CONFIG)["accent"] == "#444444"


def test_palette_reads_indented_block():
    cfg = "params:\n  style:\n    light:\n      accent: \"#abcdef\"\n      bg: '#fedcba'\n"
    p = card.palette(cfg)
    assert (p["accent"], p["bg"], p["fg"]) == ("#abcdef", "#fedcba", card.LIGHT["fg"])


def test_palette_ignores_commented_config():
    cfg = "params:\n  # style:\n  #   light: { accent: \"#000000\" }\n"
    assert card.palette(cfg) == card.LIGHT


def test_palette_ignores_a_light_key_outside_style():
    cfg = "params:\n  someOther:\n    light: { accent: \"#000000\" }\n"
    assert card.palette(cfg) == card.LIGHT


# ---------------------------------------------------------------- titles, dates

def test_go_format_site_formats():
    when = datetime(2026, 7, 6, 23, 22, 58)
    assert card.go_format("02. January 2006", when) == "06. July 2026"
    assert card.go_format("02. January 2006 15:04", when) == "06. July 2026 23:22"
    assert card.go_format("Mon 2 Jan 06 3:04 pm", when) == "Mon 6 Jul 26 11:22 pm"


def test_display_title_prefers_handwritten():
    meta = {"title": "Assembler for the people"}
    assert card.display_title("assembler", meta, None, "") == "Assembler for the people"


def test_display_title_formats_timestamp_fallback():
    when = datetime(2026, 7, 6, 23, 22)
    meta = {"title": "2026-07-06_23-22"}
    assert card.display_title("2026-07-06_23-22", meta, when, "02. January 2006") == "06. July 2026"


def test_record_date_falls_back_to_filename():
    assert card.record_date({}, "2026-07-06_23-22") == datetime(2026, 7, 6, 23, 22)
    assert card.record_date({}, "not-a-stamp") is None


# ---------------------------------------------------------------- wrapping

def test_wrap_keeps_hard_breaks_and_paragraphs():
    lines, truncated = card.wrap_lines("one\n\ntwo")
    assert (lines, truncated) == (["one", "", "two"], False)


def test_wrap_truncates_with_an_ellipsis():
    lines, truncated = card.wrap_lines("\n".join(f"line {n}" for n in range(20)), max_lines=3)
    assert truncated is True
    assert len(lines) == 3
    assert lines[-1].endswith("…")


def test_wrap_respects_the_column_budget():
    lines, _ = card.wrap_lines("word " * 60, cols=20)
    assert max(len(ln) for ln in lines) <= 20


# ---------------------------------------------------------------- build

def test_build_defaults_to_the_first_human_turn(tmp_path):
    r = card.build(_record(tmp_path), out=tmp_path / "c.svg", repo=tmp_path)
    assert (r["turn"], r["role"], r["speaker"], r["truncated"]) == (1, "user", "Human", False)
    assert "Adam and Eve" in (tmp_path / "c.svg").read_text(encoding="utf-8")


def test_build_selects_a_turn_and_labels_it_with_the_model(tmp_path):
    r = card.build(_record(tmp_path), turn=2, out=tmp_path / "c.svg", repo=tmp_path)
    assert (r["turn"], r["role"], r["speaker"]) == (2, "assistant", "claude-opus-4-8")
    svg = (tmp_path / "c.svg").read_text(encoding="utf-8")
    assert "CLAUDE-OPUS-4-8" in svg
    assert "— claude-opus-4-8" not in svg  # the signature is stripped from the quote


def test_build_rejects_an_out_of_range_turn(tmp_path):
    with pytest.raises(RuntimeError, match="out of range"):
        card.build(_record(tmp_path), turn=9, out=tmp_path / "c.svg", repo=tmp_path)


def test_build_needs_turns(tmp_path):
    plain = _record(tmp_path, "---\ntitle: x\n---\n\njust a note\n", "plain.md")
    with pytest.raises(RuntimeError, match="no ## Human"):
        card.build(plain, out=tmp_path / "c.svg", repo=tmp_path)


def test_build_output_is_well_formed_svg(tmp_path):
    card.build(_record(tmp_path), out=tmp_path / "c.svg", repo=tmp_path)
    root = ElementTree.parse(tmp_path / "c.svg").getroot()
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.get("width") == str(card.WIDTH)


def test_build_escapes_markup_in_the_turn(tmp_path):
    text = RECORD.replace("Hey!", "<script>alert(1)</script> & co")
    out = tmp_path / "c.svg"
    card.build(_record(tmp_path, text), out=out, repo=tmp_path)
    svg = out.read_text(encoding="utf-8")
    assert "<script>" not in svg and "&lt;script&gt;" in svg
    ElementTree.fromstring(svg)  # still parses


def test_build_uses_the_site_palette_title_and_url(tmp_path):
    (tmp_path / "tools" / "hugo").mkdir(parents=True)
    (tmp_path / "tools" / "hugo" / "hugo.yaml").write_text(SITE_CONFIG, encoding="utf-8")
    out = tmp_path / "c.svg"
    card.build(_record(tmp_path), out=out, repo=tmp_path)
    svg = out.read_text(encoding="utf-8")
    assert "#444444" in svg and "#666666" in svg          # accent + card from the site config
    assert "06. July 2026" in svg                          # dateTitleFormat
    assert "https://blyant.codeberg.page/records/2026-07-06_23-22/" in svg


def test_build_omits_the_url_when_baseurl_is_commented_out(tmp_path):
    out = tmp_path / "c.svg"
    card.build(_record(tmp_path), out=out, repo=tmp_path)
    assert "http" not in out.read_text(encoding="utf-8").replace(
        'xmlns="http://www.w3.org/2000/svg"', "")


def test_build_default_out_is_beside_the_cwd_not_the_record(tmp_path, monkeypatch):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    r = card.build(_record(tmp_path), repo=tmp_path)
    assert Path(r["out"]) == cwd / "2026-07-06_23-22-card.svg"
    assert Path(r["out"]).is_file()

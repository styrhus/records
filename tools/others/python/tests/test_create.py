# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import re
from datetime import datetime
from pathlib import Path

from recordkit import create


def test_new_record_with_tags_and_title(tmp_path):
    r = create.new_record(tmp_path, arguments="#linux #hw How To")
    p = Path(r["path"])
    assert p == tmp_path / "linux" / "how-to.md"
    text = p.read_text()
    assert text.startswith("---\ntitle: How To\ndate: ")
    assert "tags: [linux, hw]\n" in text
    assert text.endswith("---\n")


def test_new_record_draft(tmp_path):
    r = create.new_record(tmp_path, arguments="Some Title", draft=True)
    assert "draft: true\n" in Path(r["path"]).read_text()


def test_new_record_date_fallback(tmp_path):
    r = create.new_record(tmp_path, arguments="")
    p = Path(r["path"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.md", p.name)
    assert f"title: {p.stem}\n" in p.read_text()


def test_new_record_unique_suffix(tmp_path):
    a = create.new_record(tmp_path, title="Dup")
    b = create.new_record(tmp_path, title="Dup")
    assert Path(a["path"]).name == "dup.md"
    assert Path(b["path"]).name == "dup-1.md"


def test_explicit_tags_override_arguments(tmp_path):
    r = create.new_record(tmp_path, arguments="#parsed Title", tags=["forced"])
    assert Path(r["path"]).parent == tmp_path / "forced"


def test_when_sets_date_and_timestamp_name(tmp_path):
    when = datetime(2019, 3, 4, 5, 6, 7).astimezone()
    r = create.new_record(tmp_path, when=when)
    p = Path(r["path"])
    assert p.name == "2019-03-04_05-06.md"
    assert f"date: {when.isoformat(timespec='seconds')}\n" in p.read_text()


def test_target_path_creates_nothing(tmp_path):
    p = create.target_path(tmp_path, title="Some Title", tags=["linux"])
    assert p == tmp_path / "linux" / "some-title.md"
    assert not p.parent.exists()


def test_target_path_avoids_an_existing_name(tmp_path):
    create.new_record(tmp_path, title="Dup")
    assert create.target_path(tmp_path, title="Dup").name == "dup-1.md"


def test_extra_frontmatter_keys(tmp_path):
    r = create.new_record(tmp_path, title="X", extra={"source": "llm", "sourceId": "01x"})
    assert "\nsource: llm\nsourceId: 01x\n---\n" in Path(r["path"]).read_text()

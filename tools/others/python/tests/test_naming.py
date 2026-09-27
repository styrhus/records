# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

import re

from recordkit import naming


def test_extract_tags_title_examples():
    assert naming.extract_tags_title("#linux #hardware How to do it right") == (
        ["linux", "hardware"], "How to do it right")
    assert naming.extract_tags_title("#linux") == (["linux"], "")
    assert naming.extract_tags_title("How to do it right") == ([], "How to do it right")


def test_hash_after_tags_belongs_to_title():
    assert naming.extract_tags_title("#a Title #b") == (["a"], "Title #b")


def test_clean_tag_drops_punctuation_and_lowercases():
    assert naming.extract_tags_title("#C++ x") == (["c"], "x")


def test_slugify():
    assert naming.slugify("How To Do It") == "how-to-do-it"
    assert naming.slugify("  spaced   out ") == "spaced-out"


def test_ensure_md():
    assert naming.ensure_md("x") == "x.md"
    assert naming.ensure_md("x.md") == "x.md"


def test_unique_path(tmp_path):
    (tmp_path / "a.md").write_text("x")
    assert naming.unique_path(tmp_path, "a.md").name == "a-1.md"
    (tmp_path / "a-1.md").write_text("x")
    assert naming.unique_path(tmp_path, "a.md").name == "a-2.md"


def test_now_stamp_format():
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", naming.now_stamp())

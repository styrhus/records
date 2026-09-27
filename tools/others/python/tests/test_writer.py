# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

from recordkit import writer


def test_append_user_blank_line_separated(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("---\ntitle: X\n---\n")
    writer.append_user(f, "hello")
    assert f.read_text() == "---\ntitle: X\n---\n\nhello\n"


def test_append_turn_shape(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("head\n")
    writer.append_turn(f, "hi", "yo", "qwen2.5:14b")
    assert f.read_text() == "head\n\n## Human\n\nhi\n\n## Assistant\n\nyo\n\n— qwen2.5:14b\n"


def test_append_turn_named(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("head\n")
    writer.append_turn(f, "hi", "yo", "qwen2.5:14b", name="Ada")
    assert f.read_text() == "head\n\n## Human (Ada)\n\nhi\n\n## Assistant\n\nyo\n\n— qwen2.5:14b\n"


def test_append_human_alone(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("head\n")
    writer.append_human(f, "hi")
    assert f.read_text() == "head\n\n## Human\n\nhi\n"


def test_append_assistant_without_model_has_no_signature(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("head\n")
    writer.append_assistant(f, "yo")
    assert f.read_text() == "head\n\n## Assistant\n\nyo\n"


def test_split_appends_are_byte_identical_to_append_turn(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text("head\n")
    b.write_text("head\n")
    writer.append_turn(a, "hi", "yo", "qwen2.5:14b", name="Ada")
    writer.append_human(b, "hi", name="Ada")
    writer.append_assistant(b, "yo", model="qwen2.5:14b")
    assert b.read_text() == a.read_text()

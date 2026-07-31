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

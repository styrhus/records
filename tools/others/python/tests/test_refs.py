from recordkit import refs


def test_markdown_images_and_raw_tags():
    text = (
        "![a photo](photo.jpg)\n"
        '<img src="shot.png" alt="x">\n'
        '<video src="clip.mp4" controls></video>\n'
        "![remote](https://example.com/x.png)\n"
        "![absolute](/fuglekasse.svg)\n"
        "![data](data:image/png;base64,AAAA)\n"
    )
    assert refs.asset_references(text) == ["photo.jpg", "shot.png", "clip.mp4"]


def test_links_are_not_assets():
    """[see](2026-07-06_23-21) is a site URL, not a file — verify must not cry wolf."""
    assert refs.asset_references("[see](2026-07-06_23-21) and [b](other.md)") == []


def test_titles_and_duplicates():
    text = '![x](photo.jpg "A title")\n![y](photo.jpg)\n![z](<sp aced.png>)\n'
    assert refs.asset_references(text) == ["photo.jpg", "sp aced.png"]


def test_links_returns_label_and_target():
    assert refs.links("see [the site](https://x.example) now") == [("the site", "https://x.example")]
    assert refs.links("![img](a.png)") == []


def test_resolve_search_order(tmp_path):
    records = tmp_path / "records"
    (records / "sub").mkdir(parents=True)
    record = records / "sub" / "r.md"
    record.write_text("x")
    beside = records / "sub" / "photo.jpg"
    beside.write_bytes(b"1")
    (records / "photo.jpg").write_bytes(b"2")
    assert refs.resolve("photo.jpg", record, records, tmp_path) == beside.resolve()
    beside.unlink()
    assert refs.resolve("photo.jpg", record, records, tmp_path) == (records / "photo.jpg").resolve()


def test_resolve_theme_static(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    record = records / "r.md"
    record.write_text("x")
    static = tmp_path / "tools" / "hugo" / "themes" / "Fuglekasse" / "static"
    static.mkdir(parents=True)
    (static / "logo.svg").write_bytes(b"<svg/>")
    assert refs.resolve("logo.svg", record, records, tmp_path) == (static / "logo.svg").resolve()


def test_resolve_missing_and_fragments(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    record = records / "r.md"
    record.write_text("x")
    (records / "a b.png").write_bytes(b"1")
    assert refs.resolve("nope.png", record, records, tmp_path) is None
    assert refs.resolve("a%20b.png", record, records, tmp_path) == (records / "a b.png").resolve()

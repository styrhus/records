from recordkit import frontmatter


def test_build_basic():
    assert frontmatter.build("T", "2026-07-21T14:35:00+02:00") == (
        "---\ntitle: T\ndate: 2026-07-21T14:35:00+02:00\n---\n")


def test_build_with_tags():
    assert frontmatter.build("T", "D", tags=["linux", "hw"]) == (
        "---\ntitle: T\ndate: D\ntags: [linux, hw]\n---\n")


def test_build_draft_before_tags():
    assert frontmatter.build("T", "D", tags=["a"], draft=True) == (
        "---\ntitle: T\ndate: D\ndraft: true\ntags: [a]\n---\n")


def test_feature_adds_featured_and_unsets_draft():
    out = frontmatter.feature("---\ntitle: T\ndate: D\ndraft: true\n---\n\nbody\n")
    assert "draft: true" not in out
    assert "featured: true" in out
    assert out.endswith("\nbody\n")


def test_feature_is_idempotent():
    out = frontmatter.feature("---\ntitle: T\nfeatured: true\n---\nbody\n")
    assert out.count("featured: true") == 1

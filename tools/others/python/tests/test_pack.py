import hashlib
import json

import pytest

from recordkit import pack

BASE = "https://example.invalid/records/"


def _site(tmp_path, body, *, files=None, params="", head="", mode="single", sitemap=True):
    """A built one-page site: checkout config plus a public/ Hugo could have produced."""
    hugo = tmp_path / "tools" / "hugo"
    hugo.mkdir(parents=True)
    (hugo / "hugo.yaml").write_text("params:\n" + params, encoding="utf-8")
    (tmp_path / "CURRENT").write_text("0.12.1 badstu-flue\n", encoding="utf-8")
    out = tmp_path / "public"
    out.mkdir()
    main = f'<main class=mode-{mode}>{body}</main>' if mode else f"<main>{body}</main>"
    (out / "index.html").write_text(
        f"<!doctype html><html><head>{head}</head><body>{main}</body></html>", encoding="utf-8")
    if sitemap:
        (out / "sitemap.xml").write_text(
            f"<urlset><url><loc>{BASE}</loc></url>"
            f"<url><loc>{BASE}a-record/</loc></url></urlset>", encoding="utf-8")
    for name, content in (files or {}).items():
        f = out / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return tmp_path


def _packed(tmp_path, **kw):
    result = pack.pack(tmp_path, **kw)
    return result, (tmp_path / "pack" / "index.html").read_text(encoding="utf-8")


# -- what it refuses ---------------------------------------------------------

def test_refuses_a_multi_page_site(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", mode="")
    with pytest.raises(RuntimeError, match="multi-page site"):
        pack.pack(repo)


def test_the_build_decides_the_mode_not_the_config(tmp_path):
    """A build made with HUGO_PARAMS_PAGEMODE=single packs, config comment or not."""
    repo = _site(tmp_path, "<p>hei</p>", params="  # pageMode: single\n")
    result, _ = _packed(repo)
    assert result["page_mode"] == "single"


def test_config_mode_used_when_the_build_carries_no_class(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", mode="", params="  pageMode: single-flowing\n")
    result, _ = _packed(repo)
    assert result["page_mode"] == "single-flowing"


def test_missing_build_points_at_build_sh(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>")
    (repo / "public" / "index.html").unlink()
    with pytest.raises(RuntimeError, match="bin/build.sh"):
        pack.pack(repo)


def test_no_config_errors(tmp_path):
    with pytest.raises(RuntimeError, match="hugo.yaml"):
        pack.pack(tmp_path)


# -- inlining ----------------------------------------------------------------

def test_stylesheet_is_inlined(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", head='<link rel=stylesheet href=/records/s.css>',
                 files={"s.css": "body{color:red}"})
    result, html = _packed(repo)
    assert "<style>body{color:red}</style>" in html
    assert "<link rel" not in html and result["styles_inlined"] == 1


def test_script_is_inlined_and_its_end_tag_dropped(tmp_path):
    repo = _site(tmp_path, '<script src=/records/a.js></script><p>after</p>',
                 files={"a.js": "var x = 1 < 2;"})
    result, html = _packed(repo)
    assert "<script>var x = 1 < 2;</script><p>after</p>" in html
    assert html.count("</script>") == 1 and result["scripts_inlined"] == 1


def test_font_url_in_inline_css_becomes_a_data_uri(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", files={"fonts/f.woff2": b"\x00font"},
                 head="<style>@font-face{src:url(/records/fonts/f.woff2) format('woff2')}</style>")
    result, html = _packed(repo)
    assert 'url("data:font/woff2;base64,AGZvbnQ=")' in html
    assert result["assets_inlined"] == 1


def test_image_becomes_a_data_uri(tmp_path):
    repo = _site(tmp_path, '<img src=/records/logo.svg alt=logo>',
                 files={"logo.svg": "<svg/>"})
    result, html = _packed(repo)
    assert 'src="data:image/svg+xml;base64,' in html and result["assets_inlined"] == 1


def test_favicon_travels_even_without_images(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", head='<link rel=icon href=/records/i.svg>',
                 files={"i.svg": "<svg/>"})
    _, html = _packed(repo, images=False)
    assert 'href="data:image/svg+xml;base64,' in html


def test_no_images_keeps_the_alt_text_and_fetches_nothing(tmp_path):
    repo = _site(tmp_path, '<img src=/records/logo.svg alt="a bird">',
                 files={"logo.svg": "<svg/>"})
    result, html = _packed(repo, images=False)
    assert 'alt="a bird"' in html and "src=" not in html
    assert 'data-packed-omitted="/records/logo.svg"' in html
    assert result["assets_omitted"] == 1


def test_relative_asset_paths_resolve_too(tmp_path):
    repo = _site(tmp_path, '<img src=logo.svg alt=x>', files={"logo.svg": "<svg/>"})
    result, _ = _packed(repo)
    assert result["assets_inlined"] == 1


# -- what would fetch --------------------------------------------------------

def test_external_iframe_is_removed_and_reported(tmp_path):
    repo = _site(tmp_path, '<p>hei</p><iframe src="https://open.spotify.com/x"></iframe>')
    result, html = _packed(repo)
    assert "iframe" not in html and "spotify" not in html
    assert result["removed"] == [{"tag": "iframe", "url": "https://open.spotify.com/x",
                                  "reason": "external"}]


def test_a_control_with_nothing_left_behind_it_is_dropped(tmp_path):
    """The Spotify popper: summary plus a body that was entirely network-fetched."""
    repo = _site(tmp_path, '<details class=spotify><summary>play</summary>'
                           '<div class=spotify-body><iframe data-src="https://open.spotify.com/x">'
                           '</iframe></div></details><p>kept</p>')
    _, html = _packed(repo)
    assert "<details" not in html and "play" not in html and "<p>kept</p>" in html


def test_a_control_with_real_content_survives(tmp_path):
    repo = _site(tmp_path, '<details><summary>toc</summary><div><a href="#x">x</a></div></details>')
    _, html = _packed(repo)
    assert "<details>" in html and 'href="#x"' in html


def test_external_css_url_is_neutralised(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>",
                 head="<style>body{background:url(https://cdn.example/bg.png)}</style>")
    result, html = _packed(repo)
    assert 'url("data:,")' in html and "cdn.example" not in html
    assert result["removed"][0]["reason"] == "external"


def test_external_script_is_removed(tmp_path):
    repo = _site(tmp_path, '<script src="https://cdn.example/a.js"></script><p>hei</p>')
    result, html = _packed(repo)
    assert "cdn.example" not in html
    assert result["removed"][0]["tag"] == "script"


def test_outbound_anchors_are_left_alone(tmp_path):
    """A link a human clicks is not a fetch."""
    repo = _site(tmp_path, '<a href="https://codeberg.org/blyant/records">repo</a>')
    _, html = _packed(repo)
    assert 'href="https://codeberg.org/blyant/records"' in html


# -- links -------------------------------------------------------------------

def test_internal_link_becomes_an_in_page_anchor(tmp_path):
    repo = _site(tmp_path, '<article id=a-record>x</article>'
                           '<a href=/records/a-record/>go</a><a href=/records/>home</a>')
    result, html = _packed(repo)
    assert 'href="#a-record"' in html and 'href="#"' in html
    assert result["links_rewritten"] == 2 and result["links_unresolved"] == []


def test_a_link_with_no_anchor_is_reported_not_rewritten(tmp_path):
    repo = _site(tmp_path, '<a href=/records/elsewhere/>go</a>')
    result, html = _packed(repo)
    assert "href=/records/elsewhere/" in html
    assert result["links_unresolved"] == ["/records/elsewhere/"]
    assert "not resolve offline" in result["warnings"][0]


def test_base_path_comes_from_the_sitemap(tmp_path):
    repo = _site(tmp_path, '<article id=a-record>x</article><a href=/records/a-record/>go</a>')
    result, _ = _packed(repo)
    assert result["base_path"] == "/records/"


def test_site_at_the_domain_root(tmp_path):
    repo = _site(tmp_path, '<article id=a-record>x</article><a href=/a-record/>go</a>',
                 sitemap=False, params="  baseURL: https://example.invalid/\n")
    result, html = _packed(repo)
    assert result["base_path"] == "/" and 'href="#a-record"' in html


# -- fidelity ----------------------------------------------------------------

def test_entities_and_code_blocks_survive_verbatim(tmp_path):
    repo = _site(tmp_path, "<pre><code>if a &lt; b &amp;&amp; c &gt; d:</code></pre>")
    _, html = _packed(repo)
    assert "if a &lt; b &amp;&amp; c &gt; d:" in html


def test_untouched_markup_keeps_its_minified_form(tmp_path):
    repo = _site(tmp_path, '<section class=user><h2 id=x>Human</h2></section>')
    _, html = _packed(repo)
    assert '<section class=user><h2 id=x>Human</h2></section>' in html


def test_output_is_one_file_and_its_size_is_reported(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>")
    result, html = _packed(repo)
    assert result["bytes"] == len(html.encode("utf-8"))
    assert list(p.name for p in (tmp_path / "pack").iterdir()) == ["index.html"]


def test_out_overrides_the_destination(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>")
    target = tmp_path / "stick" / "records.html"
    result = pack.pack(repo, out=target)
    assert result["out"] == str(target) and target.is_file()


# -- books travel too --------------------------------------------------------

def test_with_books_copies_them_and_rewrites_the_footer_links(tmp_path):
    repo = _site(tmp_path, '<a href=/records/b.pdf>Get PDF</a><a href=/records/b.epub>Get EPUB</a>',
                 params="  pdf: b.pdf\n  epub: b.epub\n",
                 files={"b.pdf": b"%PDF-1.7", "b.epub": b"PK epub"})
    result, html = _packed(repo, with_books=True)
    assert 'href="b.pdf"' in html and 'href="b.epub"' in html
    assert result["books"] == ["b.epub", "b.pdf"]
    assert (tmp_path / "pack" / "b.pdf").read_bytes() == b"%PDF-1.7"


def test_with_books_writes_a_manifest_with_checksums(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", params="  pdf: b.pdf\n", files={"b.pdf": b"%PDF-1.7"})
    result, _ = _packed(repo, with_books=True)
    manifest = json.loads((tmp_path / "pack" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["werden"] == "0.12.1 badstu-flue"
    names = [e["name"] for e in manifest["files"]]
    assert names == ["b.pdf", "index.html"]
    assert manifest["files"][0]["sha256"] == hashlib.sha256(b"%PDF-1.7").hexdigest()
    assert result["manifest"].endswith("manifest.json")


def test_with_books_skips_what_was_never_built(tmp_path):
    repo = _site(tmp_path, "<p>hei</p>", params="  pdf: b.pdf\n  booklet: bl.pdf\n",
                 files={"b.pdf": b"%PDF-1.7"})
    result, _ = _packed(repo, with_books=True)
    assert result["books"] == ["b.pdf"]
    assert len(result["books_skipped"]) == 1 and "bl.pdf" in result["books_skipped"][0]


def test_book_links_are_unresolved_without_with_books(tmp_path):
    repo = _site(tmp_path, '<a href=/records/b.pdf>Get PDF</a>', params="  pdf: b.pdf\n",
                 files={"b.pdf": b"%PDF-1.7"})
    result, _ = _packed(repo)
    assert result["links_unresolved"] == ["/records/b.pdf"]
    assert not (tmp_path / "pack" / "b.pdf").exists()

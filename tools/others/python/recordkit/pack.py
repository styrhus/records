"""Collapse a built site into one self-contained HTML file — `records pack`.

Post-processes what bin/build.sh produced: stylesheets and scripts inlined,
images and fonts as data: URIs, internal links turned into in-page anchors,
and everything that would fetch removed. It never builds a site itself — one
build path — and it needs a one-page site (pageMode single or single-flowing),
because the site you pack is the site you publish.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from .config import find_hugo_configs
from .publish import _checkout_root, _param
from .werden import _read_state

_PACKABLE = ("single", "single-flowing")
_BOOK_PARAMS = ("pdf", "epub", "booklet")
_MEDIA = {"iframe", "embed", "object", "video", "audio", "source", "track"}
_URL_ATTRS = ("src", "href", "data", "poster", "data-src")
_CONTAINERS = {"details", "div", "noscript"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
         "meta", "param", "source", "track", "wbr"}
_SIZE_WARN = 8 * 1024 * 1024  # data URIs run ~33 % over the bytes they carry
_CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.DOTALL)
_MODE_CLASS = re.compile(r"<main[^>]*\bclass=[\"']?mode-([a-z-]+)")


# ---------------------------------------------------------------- tokenizing

class _Tokenizer(HTMLParser):
    """The document as a flat token list, each token keeping its source text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)  # entities must survive verbatim
        self.tokens: list[tuple] = []
        self._css = 0

    def _add(self, kind: str, tag: str, attrs: dict, raw: str) -> None:
        self.tokens.append((kind, tag, attrs, raw))

    def handle_starttag(self, tag, attrs):
        self._add("start", tag, dict(attrs), self.get_starttag_text())
        if tag == "style":
            self._css += 1

    def handle_startendtag(self, tag, attrs):
        self._add("startend", tag, dict(attrs), self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag == "style":
            self._css = max(0, self._css - 1)
        self._add("end", tag, {}, f"</{tag}>")

    def handle_data(self, data):
        self._add("css" if self._css else "text", "", {}, data)

    def handle_entityref(self, name):
        self._add("text", "", {}, f"&{name};")

    def handle_charref(self, name):
        self._add("text", "", {}, f"&#{name};")

    def handle_comment(self, data):
        self._add("text", "", {}, f"<!--{data}-->")

    def handle_decl(self, decl):
        self._add("text", "", {}, f"<!{decl}>")

    def handle_pi(self, data):
        self._add("text", "", {}, f"<?{data}>")

    def unknown_decl(self, data):
        self._add("text", "", {}, f"<![{data}]>")


def _render_start(tag: str, attrs: dict, self_closing: bool = False) -> str:
    """Rebuild a start tag — only used for tags we actually changed."""
    parts = [tag]
    for k, v in attrs.items():
        parts.append(k if v is None else f'{k}="{escape(v, quote=True)}"')
    return f"<{' '.join(parts)}{'/' if self_closing else ''}>"


# ------------------------------------------------------------------- assets

def _local_path(url: str, outdir: Path, base_path: str) -> Path | None:
    """The file a URL points at inside the built site, or None if it is not local."""
    if not url or url.startswith(("#", "data:", "//", "mailto:", "javascript:")):
        return None
    split = urlsplit(url)
    if split.scheme:
        return None
    path = unquote(split.path)
    if not path:
        return None
    if base_path != "/" and path.startswith(base_path):
        path = path[len(base_path):]
    rel = path.lstrip("/")
    if not rel:
        return None
    candidate = (outdir / rel).resolve()
    try:
        candidate.relative_to(outdir.resolve())
    except ValueError:  # never read outside the built site
        return None
    return candidate if candidate.is_file() else None


def _site_base(built: Path, text: str) -> str:
    """The path the site was built at — the sitemap knows, the config only maybe."""
    sitemap = built / "sitemap.xml"
    if sitemap.is_file():
        locs = re.findall(r"<loc>\s*(.*?)\s*</loc>",
                          sitemap.read_text(encoding="utf-8", errors="replace"))
        paths = [urlsplit(u).path for u in locs if urlsplit(u).path]
        if paths:
            return _slashed(min(paths, key=len))  # the shortest URL is the home page
    return _slashed(urlsplit(_param(text, "baseURL")).path or "/")


def _slashed(path: str) -> str:
    return path if path.endswith("/") else path + "/"


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _is_external(url: str) -> bool:
    return bool(url) and (url.startswith("//") or urlsplit(url).scheme not in ("", "data"))


# ---------------------------------------------------------------- the packer

class _Packer:
    def __init__(self, outdir: Path, base_path: str, images: bool, books: dict) -> None:
        self.outdir = outdir
        self.base_path = base_path
        self.images = images
        self.books = books  # built book filename -> name it gets beside the pack
        self.ids: set[str] = set()
        self.report = {"styles_inlined": 0, "scripts_inlined": 0, "assets_inlined": 0,
                       "assets_omitted": 0, "removed": [], "links_rewritten": 0,
                       "links_unresolved": []}

    # -- css ---------------------------------------------------------------

    def _css(self, text: str) -> str:
        def repl(m: re.Match) -> str:
            url = m.group(2).strip()
            if url.startswith("data:"):
                return m.group(0)
            if _is_external(url):
                self.report["removed"].append({"tag": "css-url", "url": url,
                                               "reason": "external"})
                return 'url("data:,")'  # a URL that fetches nothing
            path = _local_path(url, self.outdir, self.base_path)
            if path is None:
                return m.group(0)
            if not self.images and path.suffix.lower() not in (".woff2", ".woff", ".ttf", ".otf"):
                self.report["assets_omitted"] += 1
                return 'url("data:,")'
            self.report["assets_inlined"] += 1
            return f'url("{_data_uri(path)}")'
        return _CSS_URL.sub(repl, text)

    # -- links -------------------------------------------------------------

    def _rewrite_href(self, url: str) -> str | None:
        """Internal page link -> in-page anchor; None leaves the href alone."""
        split = urlsplit(url)
        if split.scheme or url.startswith(("//", "#")):
            return None
        path = unquote(split.path)
        if not path:
            return None
        if self.base_path != "/" and path.startswith(self.base_path):
            rest = path[len(self.base_path):]
        elif path.startswith("/"):
            rest = path[1:]
        else:
            rest = path
        if not rest.strip("/"):
            self.report["links_rewritten"] += 1
            return "#"
        name = Path(rest).name
        if name in self.books:  # a book travelling beside us
            self.report["links_rewritten"] += 1
            return self.books[name]
        slug = rest.strip("/").split("/")[-1]
        if slug in self.ids:
            self.report["links_rewritten"] += 1
            return f"#{slug}"
        if url not in self.report["links_unresolved"]:
            self.report["links_unresolved"].append(url)
        return None

    # -- tokens ------------------------------------------------------------

    def _drop(self, tag: str, url: str, reason: str) -> tuple:
        self.report["removed"].append({"tag": tag, "url": url, "reason": reason})
        return ("gone", tag, {}, "")

    def _start(self, kind: str, tag: str, attrs: dict, raw: str) -> list[tuple] | None:
        """Rewrite one start tag; None means 'keep the source text as it is'."""
        changed = False

        if tag == "link":
            rel = (attrs.get("rel") or "").lower()
            href = attrs.get("href") or ""
            if "stylesheet" in rel:
                path = _local_path(href, self.outdir, self.base_path)
                if path is not None:
                    self.report["styles_inlined"] += 1
                    css = self._css(path.read_text(encoding="utf-8", errors="replace"))
                    return [("text", "", {}, f"<style>{css}</style>")]
                return [self._drop("link", href, "external")] if _is_external(href) else None
            if "icon" in rel:
                path = _local_path(href, self.outdir, self.base_path)
                if path is not None:  # the tab icon travels even in a text-only pack
                    attrs["href"] = _data_uri(path)
                    self.report["assets_inlined"] += 1
                    changed = True
                elif _is_external(href):
                    return [self._drop("link", href, "external")]

        elif tag == "script":
            src = attrs.get("src")
            if src:
                path = _local_path(src, self.outdir, self.base_path)
                if path is not None:
                    self.report["scripts_inlined"] += 1
                    js = path.read_text(encoding="utf-8", errors="replace")
                    return [("inlined-script", tag, {}, f"<script>{js}</script>")]
                return [self._drop("script", src, "external")]

        elif tag == "img":
            src = attrs.get("src") or ""
            if _is_external(src):
                return [self._drop("img", src, "external")]
            path = _local_path(src, self.outdir, self.base_path)
            if path is not None:
                attrs.pop("srcset", None)
                if self.images:
                    attrs["src"] = _data_uri(path)
                    self.report["assets_inlined"] += 1
                else:
                    attrs.pop("src", None)
                    attrs["data-packed-omitted"] = src
                    self.report["assets_omitted"] += 1
                changed = True

        elif tag in _MEDIA:
            for attr in _URL_ATTRS:
                url = attrs.get(attr)
                if url and (_is_external(url) or _local_path(url, self.outdir, self.base_path)):
                    return [self._drop(tag, url, "external" if _is_external(url) else "unpackable")]

        elif tag == "a":
            href = attrs.get("href")
            if href:
                new = self._rewrite_href(href)
                if new is not None:
                    attrs["href"] = new
                    changed = True

        if "style" in attrs and attrs["style"] and "url(" in attrs["style"]:
            attrs["style"] = self._css(attrs["style"])
            changed = True

        if not changed:
            return None
        return [(kind, tag, attrs, _render_start(tag, attrs, kind == "startend"))]

    def run(self, html: str) -> str:
        parser = _Tokenizer()
        parser.feed(html)
        parser.close()
        tokens = parser.tokens
        self.ids = {a["id"] for k, _, a, _ in tokens if k.startswith("start") and a.get("id")}

        out: list[tuple] = []
        skip_until: str | None = None
        depth = 0
        swallow_end: str | None = None
        for kind, tag, attrs, raw in tokens:
            if skip_until:  # inside a dropped subtree
                if kind == "start" and tag == skip_until:
                    depth += 1
                elif kind == "end" and tag == skip_until:
                    depth -= 1
                    if depth == 0:
                        skip_until = None
                continue
            if swallow_end:  # the element we inlined still has its own end tag coming
                if kind == "end" and tag == swallow_end:
                    swallow_end = None
                    continue
                if kind in ("text", "css") and not raw.strip():
                    continue
                swallow_end = None
            if kind == "css":
                out.append(("text", "", {}, self._css(raw)))
                continue
            if kind in ("start", "startend"):
                replacement = self._start(kind, tag, attrs, raw)
                if replacement is not None:
                    dropped = replacement[0][0] == "gone"
                    if kind == "start" and tag not in _VOID:
                        if dropped:
                            skip_until, depth = tag, 1
                        elif replacement[0][0] not in ("start", "startend"):
                            swallow_end = tag  # replaced by inlined content, end tag is stale
                    out.extend(replacement)
                    continue
            out.append((kind, tag, attrs, raw))

        out = _prune_empty_containers(out)
        return "".join(raw for kind, _, _, raw in out if kind != "gone")


def _matching_end(tokens: list[tuple], start: int) -> int | None:
    tag, depth = tokens[start][1], 0
    for i in range(start, len(tokens)):
        kind, t = tokens[i][0], tokens[i][1]
        if kind == "start" and t == tag:
            depth += 1
        elif kind == "end" and t == tag:
            depth -= 1
            if depth == 0:
                return i
    return None


def _body_only_removals(tokens: list[tuple], start: int, end: int) -> bool:
    """True when the span holds a removal and nothing a reader would miss."""
    saw_removal, summary = False, 0
    for kind, tag, _, raw in tokens[start:end]:
        if kind == "gone":
            saw_removal = True
        elif kind == "start" and tag == "summary":
            summary += 1
        elif kind == "end" and tag == "summary":
            summary -= 1
        elif summary > 0:
            continue
        elif kind in ("start", "startend", "inlined-script"):
            if tag not in _CONTAINERS:
                return False
        elif kind in ("text", "css") and raw.strip():
            return False
    return saw_removal


def _prune_empty_containers(tokens: list[tuple]) -> list[tuple]:
    """Drop a control whose whole body was removed — an opener with nothing behind it."""
    for _ in range(3):  # nested containers need another sweep
        result, i, dropped = [], 0, False
        while i < len(tokens):
            if tokens[i][0] == "start" and tokens[i][1] in _CONTAINERS:
                end = _matching_end(tokens, i)
                if end is not None and _body_only_removals(tokens, i + 1, end):
                    result.append(("gone", tokens[i][1], {}, ""))
                    i = end + 1
                    dropped = True
                    continue
            result.append(tokens[i])
            i += 1
        tokens = result
        if not dropped:
            break
    return tokens


# ------------------------------------------------------------------ gather

def _book_files(text: str, outdir: Path) -> tuple[dict, list[str]]:
    """Book params that actually produced a file, and a note for each that did not."""
    found, skipped = {}, []
    for param in _BOOK_PARAMS:
        name = _param(text, param)
        if not name:
            continue
        if (outdir / name).is_file():
            found[name] = name
        else:
            skipped.append(f"params.{param}: {name} not in {outdir} — build it first")
    return found, skipped


def _manifest(root: Path, files: list[Path]) -> dict:
    entries = []
    for f in sorted(files):
        raw = f.read_bytes()
        entries.append({"name": f.name, "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()})
    return {"generated_by": "records pack", "werden": " ".join(_read_state(root / "CURRENT")).strip(),
            "files": entries}


# -------------------------------------------------------------------- entry

def pack(repo: Path, out: Path | None = None, images: bool = True,
         with_books: bool = False, outdir: Path | None = None) -> dict:
    """Pack the built site into one file. Requires a build; never makes one."""
    configs = find_hugo_configs(Path(repo))
    if not configs:
        raise RuntimeError(f"no */hugo/hugo.yaml under {repo} — nothing to pack")
    cfg = configs[0]
    text = cfg.read_text(encoding="utf-8")
    root = _checkout_root(cfg).resolve()
    built = (Path(outdir) if outdir else root / "public").resolve()
    index = built / "index.html"
    if not index.is_file():
        raise RuntimeError(f"{index} not found — run bin/build.sh first, records pack "
                           "post-processes the build, it never makes one")

    source = index.read_text(encoding="utf-8", errors="replace")
    # The build is the truth: baseof stamps <main class="mode-…">, env overrides included.
    stamped = _MODE_CLASS.search(source)
    mode = stamped.group(1) if stamped else (_param(text, "pageMode") or "basic")
    if mode not in _PACKABLE:
        raise RuntimeError(f"pageMode {mode!r} is a multi-page site — records pack needs "
                           f"pageMode: single or single-flowing in {cfg}")

    target = Path(out).resolve() if out else (root / "pack" / "index.html").resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    base_path = _site_base(built, text)
    books, skipped = _book_files(text, built) if with_books else ({}, [])
    packer = _Packer(built, base_path, images, books)
    target.write_text(packer.run(source), encoding="utf-8")

    result = {"out": str(target), "bytes": target.stat().st_size, "page_mode": mode,
              "base_path": base_path, "images": images, "with_books": with_books}
    result.update(packer.report)

    carried = [target]
    if with_books:
        for name in books:
            dest = target.parent / name
            dest.write_bytes((built / name).read_bytes())
            carried.append(dest)
        manifest = target.parent / "manifest.json"
        manifest.write_text(json.dumps(_manifest(root, carried), indent=2) + "\n",
                            encoding="utf-8")
        result["books"] = sorted(books)
        result["books_skipped"] = skipped
        result["manifest"] = str(manifest)

    warnings = []
    if result["bytes"] > _SIZE_WARN:
        warnings.append(f"{result['bytes'] // 1024} KiB is a lot to carry — "
                        "try --no-images for a text-only pack")
    if packer.report["links_unresolved"]:
        warnings.append(f"{len(packer.report['links_unresolved'])} link(s) point outside "
                        "the packed page and will not resolve offline")
    if warnings:
        result["warnings"] = warnings
    return result


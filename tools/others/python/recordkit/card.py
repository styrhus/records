"""One turn of a record as a shareable SVG quote card, drawn in the site's own palette.

Stdlib only: the SVG is a template string, text metrics are a monospace assumption.
No PNG conversion — anyone can convert an SVG, a converter would be a dependency.
"""

from __future__ import annotations

import re
import textwrap
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from . import turns as turns_mod
from .config import find_hugo_configs

WIDTH, HEIGHT = 1200, 630  # Open Graph size, so booth item 4 can reuse the card as-is
PAD = 64
BAR_X, TEXT_X = 56, 80
BODY_SIZE, LINE_H = 22, 32
COLS = 80        # monospace advance ~0.6em: (WIDTH - TEXT_X - PAD) / (BODY_SIZE * 0.6)
MAX_LINES = 11
LABEL_GAP = 68   # label baseline to the first body line
REGION_TOP, REGION_BOTTOM = 60, 500
RULE_Y = 524

# Fuglekasse's light palette; the site config overrides any subset (as book.lua does).
LIGHT = {"bg": "#d5d6db", "fg": "#343b58", "dim": "#5a5d67",
         "accent": "#34548a", "surface": "#e5e6ea", "card": "#f5f5f7"}

MONO = "DejaVu Sans Mono, Menlo, Consolas, monospace"
SANS = "system-ui, sans-serif"

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$")
_MONTHS = ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------------------------------------------------------------ site config

def site_config(repo: Path = Path(".")) -> str:
    configs = find_hugo_configs(Path(repo))
    return configs[0].read_text(encoding="utf-8") if configs else ""


def _param(text: str, name: str, default: str = "") -> str:
    """First uncommented 'name: value' line, quotes and trailing comment stripped."""
    rx = re.compile(r"^\s*" + name + r":\s*(.*?)\s*(?:#.*)?$")
    for line in text.splitlines():
        m = rx.match(line)
        if m and m.group(1):
            return m.group(1).strip().strip('"').strip("'")
    return default


def _light_block(text: str) -> str:
    """params.style.light as raw text — the inline flow map or the indented block form."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)light:\s*(.*)$", line)
        if not m or not _under_style(lines, i, len(m.group(1))):
            continue
        rest = m.group(2).strip()
        if rest.startswith("{"):
            return rest
        indent, block = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            if len(nxt) - len(nxt.lstrip()) <= indent:
                break
            block.append(nxt)
        return "\n".join(block)
    return ""


def _under_style(lines: list[str], i: int, indent: int) -> bool:
    """True when the nearest shallower key above line i is `style:`."""
    for prev in reversed(lines[:i]):
        if not prev.strip() or prev.lstrip().startswith("#"):
            continue
        if len(prev) - len(prev.lstrip()) < indent:
            return prev.strip().startswith("style:")
    return False


def palette(config_text: str) -> dict:
    """Fuglekasse's light values, overridden by params.style.light in the site config."""
    out = dict(LIGHT)
    block = _light_block(config_text)
    for key in out:
        m = re.search(key + r":\s*[\"']?(#[0-9A-Fa-f]{3,8}|[a-zA-Z]+)[\"']?", block)
        if m:
            out[key] = m.group(1)
    return out


# ------------------------------------------------------------------ record meta

def _meta(text: str) -> dict:
    """Top-level frontmatter fields as strings (title and date are all the card needs)."""
    m = _FRONTMATTER.match(text)
    fields: dict = {}
    if not m:
        return fields
    for line in m.group(1).splitlines():
        if line[:1].isspace() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def record_date(meta: dict, stem: str) -> datetime | None:
    """The explicit date: field, else the filename timestamp — the site's own priority."""
    raw = meta.get("date", "")
    if raw:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    try:
        return datetime.strptime(stem, "%Y-%m-%d_%H-%M")
    except ValueError:
        return None


def go_format(layout: str, when: datetime) -> str:
    """Go reference-date layout → string; the token subset book.lua supports."""
    h12 = when.hour % 12 or 12
    tokens = [
        ("2006", "%04d" % when.year),
        ("January", _MONTHS[when.month - 1]),
        ("Monday", _DAYS[when.weekday()]),
        ("Jan", _MONTHS[when.month - 1][:3]),
        ("Mon", _DAYS[when.weekday()][:3]),
        ("15", "%02d" % when.hour),
        ("06", "%02d" % (when.year % 100)),
        ("05", "%02d" % when.second),
        ("04", "%02d" % when.minute),
        ("03", "%02d" % h12),
        ("02", "%02d" % when.day),
        ("01", "%02d" % when.month),
        ("PM", "AM" if when.hour < 12 else "PM"),
        ("pm", "am" if when.hour < 12 else "pm"),
        ("5", str(when.second)),
        ("4", str(when.minute)),
        ("3", str(h12)),
        ("2", str(when.day)),
        ("1", str(when.month)),
    ]
    out, i = [], 0
    while i < len(layout):
        for token, value in tokens:
            if layout.startswith(token, i):
                out.append(value)
                i += len(token)
                break
        else:
            out.append(layout[i])
            i += 1
    return "".join(out)


def handwritten(stem: str, meta: dict) -> bool:
    """A real title, not create.py's timestamp echo — the rule record-title.html applies."""
    title = meta.get("title", "")
    return bool(title) and not (_STAMP.match(stem) and title == stem)


def display_title(stem: str, meta: dict, when: datetime | None, date_format: str) -> str:
    """Hand-written title:, else the date — the rule record-title.html and book.lua share."""
    if handwritten(stem, meta):
        return meta["title"]
    if when:
        return go_format(date_format, when) if date_format else when.strftime("%Y-%m-%d %H:%M")
    return stem


def speaker(turn: dict) -> str:
    """Who said it: the /myname name or Human, and the signing model or Assistant."""
    if turn["role"] == "user":
        return turn["name"] or "Human"
    return turn["model"] or "Assistant"


# ------------------------------------------------------------------ layout

def wrap_lines(content: str, cols: int = COLS, max_lines: int = MAX_LINES) -> tuple[list, bool]:
    """Wrap to `cols`, keep hard breaks, and say so with an ellipsis rather than cut silently."""
    lines: list[str] = []
    for raw in content.splitlines():
        lines.extend(textwrap.wrap(raw, cols) if raw.strip() else [""])
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[:max_lines]
        last = lines[-1].rstrip()
        if len(last) + 2 > cols:  # the ellipsis has to fit inside the column budget too
            last = last[:max(0, cols - 2)].rstrip()
        lines[-1] = last + " …"
    return lines, truncated


def _text(x: int, y: int, size: int, fill: str, value: str, family: str = SANS,
          extra: str = "") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}"{extra}>{escape(value)}</text>')


def render(lines: list, quote_speaker: str, role: str, title: str, date: str, url: str,
           colours: dict, truncated: bool) -> str:
    """The card itself: site palette, accent bar on Human turns, monospace body."""
    # The label + quote sit as one block, centred between the card top and the footer rule.
    rows = len(lines) + (1 if truncated else 0)
    block = LABEL_GAP + rows * LINE_H
    top = REGION_TOP + max(0, (REGION_BOTTOM - REGION_TOP - block) // 2)
    label_y, body_top = top + 20, top + LABEL_GAP

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{colours["bg"]}"/>',
        f'<rect x="16" y="16" width="{WIDTH - 32}" height="{HEIGHT - 32}" rx="8" '
        f'fill="{colours["card"]}" stroke="{colours["surface"]}" stroke-width="2"/>',
    ]
    if role == "user":  # mirrors section.user's accent left border
        parts.append(f'<rect x="{BAR_X}" y="{top}" width="5" height="{block}" '
                     f'fill="{colours["accent"]}"/>')
    label_fill = colours["accent"] if role == "user" else colours["fg"]
    parts.append(_text(TEXT_X, label_y, 17, label_fill, quote_speaker.upper(),
                       extra=' letter-spacing="1.6" font-weight="600"'))

    body = [f'<text x="{TEXT_X}" y="{body_top}" font-family="{MONO}" '
            f'font-size="{BODY_SIZE}" fill="{colours["fg"]}" xml:space="preserve">']
    for n, line in enumerate(lines):
        dy = 0 if n == 0 else LINE_H
        body.append(f'<tspan x="{TEXT_X}" dy="{dy}">{escape(line) or " "}</tspan>')
    body.append("</text>")
    parts.append("".join(body))

    if truncated:
        parts.append(_text(TEXT_X, body_top + len(lines) * LINE_H, 16, colours["dim"],
                           "(turn truncated)", extra=' font-style="italic"'))
    parts.append(f'<line x1="{TEXT_X}" y1="{RULE_Y}" x2="{WIDTH - PAD}" y2="{RULE_Y}" '
                 f'stroke="{colours["surface"]}" stroke-width="2"/>')
    foot = " · ".join(p for p in (title, date) if p)
    if foot:
        parts.append(_text(TEXT_X, RULE_Y + 36, 17, colours["dim"], textwrap.shorten(foot, 110)))
    if url:
        parts.append(_text(TEXT_X, RULE_Y + 64, 17, colours["accent"],
                           textwrap.shorten(url, 110)))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _pick(items: list, turn: int | None) -> int:
    """1-based --turn over all turns in document order; default the first Human turn."""
    if turn is None:
        return next((i for i, t in enumerate(items) if t["role"] == "user"), 0)
    if not 1 <= turn <= len(items):
        raise RuntimeError(f"--turn {turn} out of range: the record has {len(items)} turns")
    return turn - 1


# ------------------------------------------------------------------ command

def build(record: Path, turn: int | None = None, out: Path | None = None,
          url: str | None = None, repo: Path = Path(".")) -> dict:
    """Render one turn as an SVG card next to the site's own look."""
    path = Path(record)
    text = path.read_text(encoding="utf-8")
    items = turns_mod.split(text)
    if not items:
        raise RuntimeError(f"{path} has no ## Human/## Assistant turns to card")

    index = _pick(items, turn)
    chosen = items[index]
    config_text = site_config(repo)
    meta = _meta(text)
    when = record_date(meta, path.stem)
    title = display_title(path.stem, meta, when, _param(config_text, "dateTitleFormat"))

    date_format = _param(config_text, "datePostFormat")
    date = ""
    if when:
        date = go_format(date_format, when) if date_format else when.strftime("%Y-%m-%d %H:%M")
    if date and not handwritten(path.stem, meta):
        title = ""  # the title is only a formatted date; the date line says it once, better

    if url is None:
        base = _param(config_text, "baseURL")
        url = base.rstrip("/") + "/" + path.stem + "/" if base else ""

    lines, truncated = wrap_lines(chosen["content"])
    svg = render(lines, speaker(chosen), chosen["role"], title, date, url,
                 palette(config_text), truncated)

    out_path = Path(out) if out else Path.cwd() / f"{path.stem}-card.svg"
    out_path.write_text(svg, encoding="utf-8")
    return {"file": str(path), "out": str(out_path), "turn": index + 1,
            "role": chosen["role"], "speaker": speaker(chosen), "truncated": truncated,
            "width": WIDTH, "height": HEIGHT}

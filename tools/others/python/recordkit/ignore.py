"""`.recordsignore` — a friendlier front end to Hugo's `ignoreFiles`, not a second mechanism.

The build already has exactly one exclusion path: `ignoreFiles` in the site config. Hugo matches
those regexes against each file's **absolute** path; `book.lua` re-reads the same list raw from the
config text and matches it against each record's path **relative** to the records dir, through a
small documented regex subset (literals, `\\`-escapes, `^`, `$` — no classes, no `*`, no
alternation). Both matchers are unanchored substring searches.

So this module translates and nothing else: gitignore-shaped lines in `<records>/.recordsignore`
become regexes inside a marked, generated `ignoreFiles:` block in the site config. Hugo reads it,
`book.lua` reads it, the PDF and the EPUB follow, and neither of them learned anything new.

Because the two matchers see different strings, one rule usually emits two regexes — a
root-anchored one for `book.lua` (`^private/`) and a slash-led one for Hugo's absolute paths
(`/private/`). Each is harmless to the other matcher.

`records ignore --check` reports drift without writing, which is what CI should run: the block is
generated, so a stale one is a lie about what the site publishes.

"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .config import find_hugo_configs, read_content_dir, resolve_records_dir

IGNORE_FILE = ".recordsignore"
_BEGIN = "# records-ignore:begin"
_END = "# records-ignore:end"
_KEY = re.compile(r"^\s*ignoreFiles\s*:")
_ITEM = re.compile(r"^\s*-\s*(.+?)\s*$")
_TOPKEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*\s*:")
_CONTENTDIR = re.compile(r"^contentDir\s*:")
# Regex metacharacters that must be escaped to stay literal in both Go's RE2 and book.lua's subset.
_META = set(".+*?()[]{}^$|\\")
# Rejected outright: expressing them needs regex features book.lua does not implement.
_UNSUPPORTED = {"?": "single-character wildcards", "[": "character classes",
                "]": "character classes", "'": "single quotes"}


class PatternError(ValueError):
    """An unsupported .recordsignore line, with the reason a human needs."""


def _escape(text: str) -> str:
    return "".join("\\" + c if c in _META else c for c in text)


def translate(pattern: str) -> list[str]:
    """One gitignore-shaped line → the regexes that mean it to Hugo *and* to book.lua."""
    pat = pattern.strip()
    if pat.startswith("re:"):
        raw = pat[3:].strip()
        if not raw:
            raise PatternError("empty re: pattern")
        return [raw]                       # verbatim escape hatch; the writer owns the subset
    if pat.startswith("!"):
        raise PatternError("negation is not supported — ignoreFiles is a block list, "
                           "so there is nothing to negate back into")
    if pat.startswith("/"):
        raise PatternError("a leading / would mean 'only at the records root', and Hugo matches "
                           "ignoreFiles against absolute paths, so it cannot be expressed — "
                           "drop the slash (it then matches at any depth)")
    for char, why in _UNSUPPORTED.items():
        if char in pat:
            raise PatternError(f"{why} are not supported ({char!r}) — "
                               f"book.lua's regex subset has no way to match them; "
                               f"use a re: line if you know what Hugo and book.lua will do")
    if "*" in pat[1:]:
        raise PatternError("* is only supported at the start of a line, as a suffix rule "
                           "like *.env — anything else needs .* , which book.lua cannot match")
    if pat.startswith("*"):
        rest = pat[1:]
        if not rest:
            raise PatternError("* on its own would ignore everything")
        return [_escape(rest) + "$"]
    if pat.endswith("/"):
        name = pat[:-1]
        if not name:
            raise PatternError("empty directory pattern")
        return ["^" + _escape(name) + "/", "/" + _escape(name) + "/"]
    return ["^" + _escape(pat) + "$", "/" + _escape(pat) + "$"]


def read_ignore_file(path: Path) -> list[tuple[int, str]]:
    """Non-blank, non-comment lines of a .recordsignore, with their line numbers."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for lineno, raw in enumerate(text.split("\n"), start=1):
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append((lineno, line))
    return out


def to_regexes(lines: list[tuple[int, str]]) -> tuple[list[str], list[dict]]:
    """Translate every line; collect problems rather than stopping at the first."""
    regexes: list[str] = []
    problems: list[dict] = []
    for lineno, line in lines:
        try:
            for rx in translate(line):
                if rx not in regexes:
                    regexes.append(rx)
        except PatternError as e:
            problems.append({"line": lineno, "pattern": line, "problem": str(e)})
    return regexes, problems


def render_block(regexes: list[str], source: str) -> str:
    """The generated `ignoreFiles:` block. Empty patterns render as no block at all."""
    if not regexes:
        return ""
    lines = [f"{_BEGIN} — GENERATED from {source} by `records ignore`.",
             "# Edit that file and re-run; hand edits between the markers are overwritten.",
             "# Hugo matches these against absolute paths, book.lua against records-relative",
             "# ones, which is why one rule can produce two regexes.",
             "ignoreFiles:"]
    lines += [f"  - '{rx}'" for rx in regexes]
    lines.append(_END)
    return "\n".join(lines) + "\n"


def _strip_block(text: str) -> tuple[str, str | None]:
    """Remove a previously generated block; return the rest and the block that was there."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.startswith(_BEGIN)), None)
    if start is None:
        return text, None
    end = next((i for i in range(start, len(lines)) if lines[i].startswith(_END)), None)
    if end is None:
        return text, None
    block = "\n".join(lines[start:end + 1]) + "\n"
    rest = lines[:start] + lines[end + 1:]
    return "\n".join(rest), block


def _find_handwritten(text: str) -> tuple[int, int, list[str]] | None:
    """A bare `ignoreFiles:` key outside the markers: its span and its raw items."""
    lines = text.split("\n")
    key = next((i for i, ln in enumerate(lines) if _KEY.match(ln)), None)
    if key is None:
        return None
    items, end = [], key
    for i in range(key + 1, len(lines)):
        stripped = lines[i].strip()
        m = _ITEM.match(lines[i])
        if m:
            value = m.group(1)
            if value.startswith("'") and value.endswith("'") and len(value) > 1:
                value = value[1:-1].replace("''", "'")
            elif value.startswith('"') and value.endswith('"') and len(value) > 1:
                value = re.sub(r"\\(.)", r"\1", value[1:-1])
            items.append(value)
            end = i
        elif not stripped or stripped.startswith("#"):
            continue
        else:
            break
    return key, end, items


def _insert(text: str, block: str) -> str:
    """Put the block just after the contentDir stanza — where exclusion belongs conceptually."""
    lines = text.split("\n")
    anchor = next((i for i, ln in enumerate(lines) if _CONTENTDIR.match(ln)), None)
    if anchor is None:
        body = text if text.endswith("\n") else text + "\n"
        return body + "\n" + block
    at = len(lines)
    for i in range(anchor + 1, len(lines)):
        if _TOPKEY.match(lines[i]):
            at = i
            break
    # A comment block directly above a key documents that key — go in above it, not between.
    while at > anchor + 1 and lines[at - 1].lstrip().startswith("#"):
        at -= 1
    head = lines[:at]
    while head and not head[-1].strip():
        head.pop()
    return "\n".join(head + [""] + block.rstrip("\n").split("\n") + [""] + lines[at:])


def _resolve(repo: Path) -> tuple[Path | None, Path]:
    configs = find_hugo_configs(Path(repo))
    if not configs:
        return None, resolve_records_dir(Path(repo))
    cfg = configs[0]
    return cfg, (cfg.parent / read_content_dir(cfg)).resolve()


def hugo_ignored(abs_path: str, regexes: list[str]) -> bool:
    """What Hugo does: unanchored search of each regex against the absolute path."""
    return any(re.search(rx, abs_path) for rx in regexes)


def book_ignored(rel_path: str, regexes: list[str]) -> bool:
    """What book.lua does: the same search against the records-relative path."""
    return any(re.search(rx, rel_path) for rx in regexes)


def excluded(records_dir: Path, regexes: list[str]) -> tuple[list[str], list[str]]:
    """Records the block excludes, and any the two matchers disagree about (a translation bug)."""
    out, disagree = [], []
    if not Path(records_dir).is_dir():
        return out, disagree
    for f in sorted(Path(records_dir).rglob("*.md")):
        rel = str(f.relative_to(records_dir))
        h, b = hugo_ignored(str(f.resolve()), regexes), book_ignored(rel, regexes)
        if h or b:
            out.append(rel)
        if h != b:
            disagree.append(rel)
    return out, disagree


def sync(repo: Path = Path("."), check: bool = False, adopt: bool = False) -> dict:
    """Regenerate the config's ignoreFiles block from .recordsignore. --check writes nothing."""
    cfg, records_dir = _resolve(Path(repo))
    ignore_path = records_dir / IGNORE_FILE
    result: dict = {"config": str(cfg) if cfg else None, "records_dir": str(records_dir),
                    "ignore_file": str(ignore_path), "written": False}
    if cfg is None:
        return {**result, "ok": False,
                "problems": [{"problem": f"no */hugo/hugo.yaml under {Path(repo).resolve()}"}]}

    lines = read_ignore_file(ignore_path)
    regexes, problems = to_regexes(lines)
    source = f"{records_dir.name}/{IGNORE_FILE}"
    result |= {"patterns": [line for _, line in lines], "regexes": regexes,
               "problems": problems}
    if problems:
        return {**result, "ok": False}

    text = cfg.read_text(encoding="utf-8")
    rest, existing = _strip_block(text)
    hand = _find_handwritten(rest)
    if hand and not adopt:
        _, _, items = hand
        return {**result, "ok": False,
                "problems": [{"problem":
                              f"{cfg} already has a hand-written ignoreFiles: "
                              f"({', '.join(items) or 'empty'}). YAML allows one key, so the "
                              f"generated block cannot sit beside it — move those patterns into "
                              f"{source} as `re:` lines, or run with --adopt to do that for you."}]}
    adopted: list[str] = []
    if hand and adopt:
        key, end, items = hand
        adopted = items
        rest_lines = rest.split("\n")
        rest = "\n".join(rest_lines[:key] + rest_lines[end + 1:])
        regexes = [i for i in items if i not in regexes] + regexes

    block = render_block(regexes, source)
    updated = _insert(rest, block) if block else rest
    result["regexes"] = regexes
    ignored, disagree = excluded(records_dir, regexes)
    result |= {"ignored": ignored, "disagree": disagree, "adopted": adopted}
    if updated == text:
        return {**result, "ok": True, "drift": False}
    if check:
        return {**result, "ok": False, "drift": True,
                "problems": [{"problem": f"{cfg}'s ignoreFiles block does not match {source} — "
                                         f"run `records ignore`"}]}
    if adopt and adopted:
        header = f"# adopted from {cfg.name}'s hand-written ignoreFiles\n"
        body = "".join(f"re: {item}\n" for item in adopted)
        prior = ignore_path.read_text(encoding="utf-8") if ignore_path.exists() else ""
        ignore_path.parent.mkdir(parents=True, exist_ok=True)
        ignore_path.write_text(header + body + prior, encoding="utf-8")
    cfg.write_text(updated, encoding="utf-8")
    return {**result, "ok": True, "drift": True, "written": True}


def render(result: dict) -> str:
    lines = [f"records ignore — {result.get('config')}", ""]
    for p in result.get("problems", []):
        where = f"{result['ignore_file']}:{p['line']}  {p['pattern']}\n      ↳ " \
            if "line" in p else ""
        lines.append(f"  error  {where}{p['problem']}")
    for pattern in result.get("patterns", []):
        lines.append(f"  pattern  {pattern}")
    for rx in result.get("regexes", []):
        lines.append(f"  regex    {rx}")
    for rel in result.get("ignored", []):
        lines.append(f"  excluded {rel}")
    for rel in result.get("disagree", []):
        lines.append(f"  MISMATCH {rel} — site and book disagree; please report this")
    state = "written" if result.get("written") else \
        ("drift" if result.get("drift") else "up to date")
    lines += ["", f"  {state}"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="records ignore",
        description="Regenerate the site config's ignoreFiles block from .recordsignore.")
    p.add_argument("--repo", default=".")
    p.add_argument("--check", action="store_true", help="report drift, write nothing")
    p.add_argument("--adopt", action="store_true",
                   help="move a hand-written ignoreFiles into .recordsignore as re: lines")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)
    result = sync(Path(args.repo), check=args.check, adopt=args.adopt)
    print(json.dumps(result) if args.json else render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

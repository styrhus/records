"""Grep the records tree for things that look like credentials — heuristic, and it says so.

The doctor's sibling: findings with remedies, reporting only, never fixing. What it finds is a
*candidate*, not a verdict; what it misses is not proof of a clean tree. Two rule families:
named shapes (`-----BEGIN … PRIVATE KEY-----`, `sk-`/`ghp_`-style prefixes, JWTs, credentials in
URLs, `.env`-shaped assignments) and one entropy heuristic for the tokens nobody prefixed.

Matches are never printed in full. A scan report that quotes the secret has made a second copy of
it, in a terminal, a scrollback buffer and possibly a CI log; every finding shows the first few
characters, the length, and where to look.

`.recordsignore` and `draft: true` are deliberately not honoured here. Neither keeps a file out of
git, and git is what leaks. See docs/oops.md for what to do when this finds something — the first
step is not in this file, and it is to rotate the credential.

"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from .config import resolve_records_dir

_MAX_BYTES = 2 * 1024 * 1024   # bigger than this is an asset, not a transcript
_MAX_LINE = 4000               # minified/base64 blobs: scan the head, do not choke on the rest
_ENTROPY_MIN_LEN = 32
_ENTROPY_BITS = 4.0            # lowercase hex tops out at 4.0, so shas stay quiet

_ROTATE = "rotate the credential first, then read docs/oops.md"

# name, pattern, level, remedy. Order matters only for reporting.
_RULES: tuple[tuple[str, re.Pattern, str, str], ...] = (
    ("private-key",
     re.compile(r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----"),
     "error",
     f"a private key block is in the tree — {_ROTATE}"),
    ("token-prefix",
     re.compile(r"\b(?:sk-ant-[A-Za-z0-9_\-]{16,}|sk-[A-Za-z0-9]{20,}"
                r"|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                r"|glpat-[A-Za-z0-9_\-]{16,}|xox[baprs]-[A-Za-z0-9\-]{10,}"
                r"|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|AIza[A-Za-z0-9_\-]{35}"
                r"|hf_[A-Za-z0-9]{20,}|dop_v1_[a-f0-9]{32,}|npm_[A-Za-z0-9]{30,}"
                r"|SG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,})"),
     "error",
     f"the prefix names the issuer, so this is a real token shape — {_ROTATE}"),
    ("jwt",
     re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
     "error",
     f"a signed JWT — session tokens are credentials too; {_ROTATE}"),
    ("url-credentials",
     re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s/:@]+:[^\s/@]+@[^\s/]+"),
     "error",
     f"a password inside a URL — {_ROTATE}"),
    # Shell assignment shape on purpose: no spaces around the =, so `_KEY = re.compile(…)`
    # and other source lines stay out of the report.
    ("env-line",
     re.compile(r"^\s*(?:export\s+)?[A-Z][A-Z0-9_]*"
                r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PASS|CREDENTIALS?|AUTH)="
                r"[\"']?([^\s\"']{8,})"),
     "warn",
     "an .env-shaped assignment — if the value is real, rotate it; "
     "if it is an example, make it obviously fake (put0YourKeyHere)"),
)

# Entropy candidates: base64/base64url/hex runs long enough to be a key.
_CANDIDATE = re.compile(r"[A-Za-z0-9+/=_\-]{%d,}" % _ENTROPY_MIN_LEN)
_HEXISH = re.compile(r"\A[0-9a-f]+\Z")          # git shas, checksums — never flagged
_DECIMAL = re.compile(r"\A[0-9._\-]+\Z")
_URL = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s)>\"'\]]+")


def _url_spans(line: str) -> list[tuple[int, int]]:
    """Host and path of every URL on the line. A long path is not a key; a query value can be,
    so the span stops at the first `?`."""
    spans = []
    for m in _URL.finditer(line):
        cut = m.group(0).find("?")
        spans.append((m.start(), m.start() + (cut if cut != -1 else len(m.group(0)))))
    return spans


def _entropy(text: str) -> float:
    """Shannon entropy in bits per character."""
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _mask(text: str) -> str:
    """Enough to recognise it in the file, never enough to use it."""
    head = text[:4]
    return f"{head}… ({len(text)} chars)"


def _finding(path: str, line: int, rule: str, level: str, sample: str, remedy: str) -> dict:
    return {"path": path, "line": line, "rule": rule, "level": level,
            "sample": _mask(sample), "remedy": remedy}


def _is_text(data: bytes) -> bool:
    return b"\x00" not in data[:8192]


def _looks_random(token: str) -> bool:
    """A conservative reading of 'this is not prose and not a hash'."""
    if len(token) < _ENTROPY_MIN_LEN or _HEXISH.match(token) or _DECIMAL.match(token):
        return False
    # Every character distinct over this length is an alphabet or a permutation, never a draw.
    if len(set(token)) == len(token) and len(token) >= 24:
        return False
    # Letters and digits both: a 32-char random string with no digit is a one-in-300 event,
    # while identifier paths (--vscode-editor-background, ../../docs/records/…) have none.
    if not (any(c.isdigit() for c in token) and any(c.isalpha() for c in token)):
        return False
    return _entropy(token) >= _ENTROPY_BITS


def scan_text(text: str, path: str = "<text>") -> list[dict]:
    """Every finding in one file's contents, in line order."""
    out: list[dict] = []
    for lineno, raw in enumerate(text.split("\n"), start=1):
        line = raw[:_MAX_LINE]
        claimed: list[tuple[int, int]] = []
        for name, pattern, level, remedy in _RULES:
            for m in pattern.finditer(line):
                # env-line reports its value, not the whole assignment.
                group = 1 if (name == "env-line" and m.group(1)) else 0
                start, end = m.span(group)
                if any(start < c_end and c_start < end for c_start, c_end in claimed):
                    continue           # an earlier, more specific rule already named this text
                out.append(_finding(path, lineno, name, level, m.group(group), remedy))
                claimed.append((start, end))
        quiet = claimed + _url_spans(line)
        for m in _CANDIDATE.finditer(line):
            if any(m.start() < end and start < m.end() for start, end in quiet):
                continue                       # a named rule said it, or it is a URL path
            if _looks_random(m.group(0)):
                out.append(_finding(
                    path, lineno, "high-entropy", "warn", m.group(0),
                    "a long random-looking string — a key, a hash or a base64 blob; "
                    "if it is a key, rotate it (docs/oops.md)"))
    return out


def _files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*"))
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(root).parts)]


def scan(target: Path = Path(".")) -> dict:
    """Scan a records directory (or any directory, or a single file). Reads only."""
    target = Path(target)
    if target.is_file():
        root, files = target.parent, [target]
    else:
        root = target
        if not (target / "_index.md").exists() and target.name != "records":
            resolved = resolve_records_dir(target)     # a checkout: find its records dir
            if resolved.is_dir():
                root = resolved
        files = _files(root) if root.is_dir() else []

    findings: list[dict] = []
    scanned = skipped = 0
    for f in files:
        try:
            data = f.read_bytes()
        except OSError:
            continue
        if len(data) > _MAX_BYTES or not _is_text(data):
            skipped += 1
            continue
        scanned += 1
        findings.extend(scan_text(data.decode("utf-8", errors="replace"),
                                  str(f.relative_to(root))))

    errors = sum(1 for f in findings if f["level"] == "error")
    return {"root": str(root), "scanned": scanned, "skipped": skipped,
            "findings": findings, "errors": errors,
            "warnings": len(findings) - errors, "ok": not findings}


def render(result: dict) -> str:
    """The human-readable report; --json prints the dict instead."""
    lines = [f"records scan — {result['root']}", ""]
    for f in result["findings"]:
        lines.append(f"  {f['level']:<5}  {f['rule']:<13}  "
                     f"{f['path']}:{f['line']}  {f['sample']}")
        lines.append(f"{'':<23}↳ {f['remedy']}")
    if not result["findings"]:
        lines.append("  nothing matched.")
    warnings, errors = result["warnings"], result["errors"]
    lines += ["", f"  {result['scanned']} file(s) read · "
                  f"{warnings} warning{'' if warnings == 1 else 's'}"
                  f" · {errors} error{'' if errors == 1 else 's'}",
              "",
              "  Heuristic. It misses secrets it has no shape for, and it flags strings",
              "  that are not secrets. A clean scan is not a promise.",
              "  If one of these is real: rotate it first, then read docs/oops.md."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="records scan",
                                description="Look for credential-shaped strings in the records.")
    p.add_argument("path", nargs="?", default=".",
                   help="records dir, checkout, or a single file (default: resolve from here)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)
    result = scan(Path(args.path))
    print(json.dumps(result) if args.json else render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

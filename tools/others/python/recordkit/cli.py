"""records CLI — deterministic, no-AI record operations, JSON on stdout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import commit as commit_mod
from . import config, create, mucke, myname, ollama, stick, werden, writer


def _stdin_or(value: str) -> str:
    """'-' means read the whole message from stdin; otherwise the value is used verbatim."""
    return sys.stdin.read() if value == "-" else value


def _emit(obj: dict) -> None:
    json.dump(obj, sys.stdout)
    sys.stdout.write("\n")


def _records_dir(args: argparse.Namespace) -> Path:
    return Path(args.dir) if args.dir else config.resolve_records_dir(Path("."))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="records",
                                description="Run the mechanical records skills without AI.")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new", help="create a record with Hugo frontmatter (/record, /all, /me)")
    n.add_argument("arguments", nargs="*", default=[], help="'#tags title' as typed to the skill")
    n.add_argument("--dir")
    n.add_argument("--tags", help="comma-separated; overrides tags parsed from arguments")
    n.add_argument("--title", help="overrides the title parsed from arguments")
    n.add_argument("--draft", action="store_true", help="mark draft (kept off the site) — /me")

    ap = sub.add_parser("append", help="append a verbatim user message (/all, /me)")
    ap.add_argument("--file", required=True)
    ap.add_argument("--text", required=True, help="message text, or '-' to read stdin")

    at = sub.add_parser("append-turn", help="append a Human/Assistant turn (Ollama-backed /record)")
    at.add_argument("--file", required=True)
    at.add_argument("--human", required=True, help="text, or '-' to read stdin")
    at.add_argument("--assistant", required=True, help="text, or '-' to read stdin")
    at.add_argument("--model", required=True, help="model tag for the signature line")

    ol = sub.add_parser("ollama-reply", help="two-sided /record turn via a local Ollama model")
    ol.add_argument("--endpoint", required=True, help="Ollama base URL, e.g. http://localhost:11434")
    ol.add_argument("--model", required=True, help="model tag, e.g. mistral:latest")
    ol.add_argument("--file", required=True)
    ol.add_argument("--human", required=True, help="text, or '-' to read stdin")
    ol.add_argument("--timeout", type=float, default=ollama.DEFAULT_TIMEOUT)
    ol.add_argument("--context-file", action="append", default=[], dest="context_files",
                    help="file whose contents go to the model only, never the record (repeatable)")
    ol.add_argument("--context-dir", action="append", default=[], dest="context_dirs",
                    help="directory whose file listing goes to the model only (repeatable)")

    oc = sub.add_parser("ollama-chat", help="ephemeral chat turn via a local Ollama model — no file")
    oc.add_argument("--endpoint", required=True, help="Ollama base URL, e.g. http://localhost:11434")
    oc.add_argument("--model", required=True, help="model tag, e.g. mistral:latest")
    oc.add_argument("--human", required=True, help="text, or '-' to read stdin")
    oc.add_argument("--history", default="[]",
                    help="prior turns as a JSON array of {role, content}, or '-' to read stdin")
    oc.add_argument("--timeout", type=float, default=ollama.DEFAULT_TIMEOUT)
    oc.add_argument("--context-file", action="append", default=[], dest="context_files",
                    help="file whose contents go to the model only (repeatable)")
    oc.add_argument("--context-dir", action="append", default=[], dest="context_dirs",
                    help="directory whose file listing goes to the model only (repeatable)")

    st = sub.add_parser("stick", help="feature a record (/stick)")
    grp = st.add_mutually_exclusive_group(required=True)
    grp.add_argument("--file")
    grp.add_argument("--slug", help="slugified name to search for under the records dir")
    st.add_argument("--dir")

    cm = sub.add_parser("commit", help="commit / push / deploy (/gc, /gcp, /cpd)")
    cm.add_argument("-m", "--message")
    cm.add_argument("--push", action="store_true")
    cm.add_argument("--deploy", action="store_true")
    cm.add_argument("--repo", default=".")

    mn = sub.add_parser("myname", help="save the user's name (/myname)")
    mn.add_argument("name")
    mn.add_argument("--memory-dir")

    mk = sub.add_parser("mucke", help="stamp the now-playing track (/mucke)")
    mk.add_argument("--file", required=True)

    wd = sub.add_parser("werden", help="advance the werden cycle (/werden — verse stays AI-only)")
    wd.add_argument("structure", nargs="?", help="start a new structure (major step)")
    wd.add_argument("--stamp", action="store_true",
                    help="keep the current name; re-derive the number and re-stamp the docs")
    wd.add_argument("--repo", default=".")

    cf = sub.add_parser("config", help="print the resolved records directory")
    cf.add_argument("--dir")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "new":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
            _emit(create.new_record(_records_dir(args), arguments=" ".join(args.arguments),
                                    draft=args.draft, tags=tags, title=args.title))
        elif args.cmd == "append":
            writer.append_user(Path(args.file), _stdin_or(args.text))
            _emit({"file": args.file, "appended": True})
        elif args.cmd == "append-turn":
            writer.append_turn(Path(args.file), _stdin_or(args.human),
                               _stdin_or(args.assistant), args.model)
            _emit({"file": args.file, "appended": True})
        elif args.cmd == "ollama-reply":
            context = ollama.build_context([Path(p) for p in args.context_files],
                                           [Path(p) for p in args.context_dirs])
            _emit(ollama.reply(Path(args.file), args.endpoint, args.model,
                               _stdin_or(args.human), timeout=args.timeout,
                               context=context or None))
        elif args.cmd == "ollama-chat":
            context = ollama.build_context([Path(p) for p in args.context_files],
                                           [Path(p) for p in args.context_dirs])
            try:
                history = json.loads(_stdin_or(args.history))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"invalid history JSON: {e}") from e
            _emit(ollama.ephemeral_reply(args.endpoint, args.model, _stdin_or(args.human),
                                         history, timeout=args.timeout,
                                         context=context or None))
        elif args.cmd == "stick":
            if args.file:
                _emit(stick.feature_file(Path(args.file)))
            else:
                d = Path(args.dir) if args.dir else config.resolve_records_dir(Path("."))
                matches = [str(m) for m in stick.find_record(d, args.slug)]
                if not matches:
                    _emit({"error": "not found", "slug": args.slug})
                    return 1
                if len(matches) > 1:
                    _emit({"error": "ambiguous", "matches": matches})
                    return 1
                _emit(stick.feature_file(Path(matches[0])))
        elif args.cmd == "commit":
            _emit(commit_mod.commit(Path(args.repo), args.message,
                                    push=args.push, deploy=args.deploy))
        elif args.cmd == "myname":
            _emit(myname.save(args.name, Path(args.memory_dir) if args.memory_dir else None))
        elif args.cmd == "mucke":
            _emit(mucke.stamp(Path(args.file)))
        elif args.cmd == "werden":
            _emit(werden.cycle(Path(args.repo), args.structure, stamp=args.stamp))
        elif args.cmd == "config":
            _emit({"records_dir": str(_records_dir(args))})
    except Exception as e:  # surface as JSON so the plugins can render it
        _emit({"error": str(e)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

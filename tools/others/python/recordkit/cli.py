"""records CLI — deterministic, no-AI record operations, JSON on stdout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import archive as archive_mod
from . import commit as commit_mod
from . import export as export_mod
from . import pack as pack_mod
from . import airtime, attach, booth, card, config, create, doctor, ignore, importer, mucke, myname
from . import ollama
from . import publish, redact, scan, stick, unpublish, verify, watch, werden, writer


# own parser, own output — not JSON-on-stdout
_PASSTHROUGH = {"doctor": doctor, "watch": watch, "scan": scan, "ignore": ignore}


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
    # The werden cycle number — same one CURRENT carries.
    p.add_argument("--version", action="version", version=f"recordkit {__version__}")
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
    at.add_argument("--name", help="human name for the heading; default: the saved /myname name")

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
    ol.add_argument("--preset", help="voice preset name (recordkit/presets/<name>.txt); "
                    "composed as a system message ahead of --context-*")
    ol.add_argument("--name", help="human name for the heading; default: the saved /myname name")

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
    oc.add_argument("--preset", help="voice preset name (recordkit/presets/<name>.txt); "
                    "composed as a system message ahead of --context-*")

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

    pb = sub.add_parser("publish", help="build and deliver the site per params.publishTarget")
    pb.add_argument("--repo", default=".")
    pb.add_argument("--dry-run", action="store_true", help="build, then report without delivering")

    mn = sub.add_parser("myname", help="save the user's name (/myname)")
    mn.add_argument("name")
    mn.add_argument("--memory-dir")

    mk = sub.add_parser("mucke", help="stamp the now-playing track (/mucke)")
    mk.add_argument("--file", required=True)

    ai = sub.add_parser("airtime", help="Human vs Assistant token share (/airtime)")
    src = ai.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="a record — its ## Human/## Assistant turns are measured")
    src.add_argument("--history", help="a chat as a JSON array of {role, content}, or '-' to read stdin")

    wd = sub.add_parser("werden", help="advance the werden cycle (/werden — verse stays AI-only)")
    wd.add_argument("structure", nargs="?", help="start a new structure (major step)")
    wd.add_argument("--stamp", action="store_true",
                    help="keep the current name; re-derive the number and re-stamp the docs")
    wd.add_argument("--repo", default=".")

    cf = sub.add_parser("config", help="print the resolved records directory")
    cf.add_argument("--dir")

    im = sub.add_parser("import", help="import conversations from an export into records")
    im.add_argument("--source", required=True, help="claude-code | llm | markdown")
    im.add_argument("--path", required=True, help="the export file or directory")
    im.add_argument("--dir")
    im.add_argument("--tags", help="comma-separated; routes every record into the first tag")
    im.add_argument("--dry-run", action="store_true", help="report what would land, write nothing")
    im.add_argument("--name", help="human name for the headings; default: the saved /myname name")

    ar = sub.add_parser("archive", help="bundle records, assets, config and a checksum manifest")
    ar.add_argument("--repo", default=".")
    ar.add_argument("--out", help="archive path; default ./records-<timestamp>.zip")
    ar.add_argument("--dry-run", action="store_true", help="list what would go in, and what would not")
    ar.add_argument("--check", action="store_true", help="cron mode: silent unless something is wrong")

    vf = sub.add_parser("verify", help="check an archive's checksums, or a checkout's references")
    vf.add_argument("archive", nargs="?", help="archive to check; omit to check a checkout")
    vf.add_argument("--repo", default=".")

    ex = sub.add_parser("export", help="write the whole corpus as plain text")
    ex.add_argument("--repo", default=".")
    ex.add_argument("--format", default="text", choices=["text"])
    ex.add_argument("--out", required=True, help="directory for the tree, or the file with --single")
    ex.add_argument("--single", action="store_true", help="one concatenated file with a contents list")

    an = sub.add_parser("attach", help="attach files to a record, converting it to a bundle")
    an.add_argument("record", help="the record's .md path, or its bundle folder")
    an.add_argument("files", nargs="+")
    an.add_argument("--title", help="link text; default: the attachment's name")
    an.add_argument("--append", action="store_true", help="write the links into the record")
    an.add_argument("--dry-run", action="store_true", help="show the conversion and the copies")

    pk = sub.add_parser("pack", help="collapse the built site into one offline HTML file")
    pk.add_argument("--repo", default=".")
    pk.add_argument("--out")
    pk.add_argument("--no-images", action="store_true")
    pk.add_argument("--with-books", action="store_true")
    pk.add_argument("--outdir", help="built site to post-process (default: <repo>/public)")

    cd = sub.add_parser("card", help="render one turn as an SVG quote card")
    cd.add_argument("record", help="the record to draw from")
    cd.add_argument("--turn", type=int, help="1-based turn number; default: the last assistant turn")
    cd.add_argument("--out", help="SVG path; default: next to the record")
    cd.add_argument("--url", help="footer URL; default: derived from the site's baseURL")
    cd.add_argument("--repo", default=".")

    bo = sub.add_parser("booth", help="open the composing screen (curses; no model required)")
    bo.add_argument("arguments", nargs="*", default=[], help="'#tags title' as typed to /record")
    bo.add_argument("--dir")
    bo.add_argument("--draft", action="store_true")
    bo.add_argument("--file", help="continue an existing record instead of creating one")
    bo.add_argument("--endpoint", help="Ollama base URL; omit for a user-only booth")
    bo.add_argument("--model", help="model tag; omit for a user-only booth")
    bo.add_argument("--timeout", type=float, default=ollama.DEFAULT_TIMEOUT)
    bo.add_argument("--name", help="human name for the headings; default: the saved /myname name")

    rd = sub.add_parser("redact", help="rewrite one turn in place, leaving a visible seam")
    rd.add_argument("record", help="the record's .md path, or its bundle folder")
    rd.add_argument("--turn", type=int, required=True,
                    help="1-based turn number in document order (as `records card --turn`)")
    rdm = rd.add_mutually_exclusive_group(required=True)
    rdm.add_argument("--replace", help="text to stand in for the turn; the [redacted] seam is kept too")
    rdm.add_argument("--remove", action="store_true", help="leave the [redacted] marker alone")
    rd.add_argument("--dry-run", action="store_true", help="show the diff, write nothing")
    rd.add_argument("--yes", action="store_true", help="skip the confirmation prompt")

    up = sub.add_parser("unpublish",
                        help="take a record out of the site, the books and the pages branch")
    up.add_argument("record", help="the record's path, its bundle folder, or its slug")
    upm = up.add_mutually_exclusive_group()
    upm.add_argument("--tombstone", action="store_true", help="leave a stub at the old URL")
    upm.add_argument("--restore", action="store_true", help="put an unpublished record back")
    up.add_argument("--dir")
    up.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")

    # Registered for the help listing only — main() hands these straight to their own module,
    # which owns its flags and its human-readable rendering (see _PASSTHROUGH).
    for name, helptext in (("doctor", "report what will fail in this checkout"),
                           ("watch", "rebuild when a record changes — never commits or publishes"),
                           ("scan", "look for credential-shaped strings in the records"),
                           ("ignore", "regenerate ignoreFiles from records/.recordsignore")):
        sub.add_parser(name, help=helptext, add_help=False)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in _PASSTHROUGH:
        return _PASSTHROUGH[argv[0]].main(argv[1:])  # their flags, their rendering, their exit code
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
                               _stdin_or(args.assistant), args.model,
                               name=args.name or myname.load())
            _emit({"file": args.file, "appended": True})
        elif args.cmd == "ollama-reply":
            context = ollama.build_context([Path(p) for p in args.context_files],
                                           [Path(p) for p in args.context_dirs])
            preset = ollama.load_preset(args.preset) if args.preset else None
            _emit(ollama.reply(Path(args.file), args.endpoint, args.model,
                               _stdin_or(args.human), timeout=args.timeout,
                               context=context or None, preset=preset,
                               name=args.name or myname.load()))
        elif args.cmd == "ollama-chat":
            context = ollama.build_context([Path(p) for p in args.context_files],
                                           [Path(p) for p in args.context_dirs])
            try:
                history = json.loads(_stdin_or(args.history))
            except json.JSONDecodeError as e:
                raise RuntimeError(f"invalid history JSON: {e}") from e
            preset = ollama.load_preset(args.preset) if args.preset else None
            _emit(ollama.ephemeral_reply(args.endpoint, args.model, _stdin_or(args.human),
                                         history, timeout=args.timeout,
                                         context=context or None, preset=preset))
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
        elif args.cmd == "publish":
            _emit(publish.publish(Path(args.repo), dry_run=args.dry_run))
        elif args.cmd == "myname":
            _emit(myname.save(args.name, Path(args.memory_dir) if args.memory_dir else None))
        elif args.cmd == "mucke":
            _emit(mucke.stamp(Path(args.file)))
        elif args.cmd == "airtime":
            if args.file:
                _emit(airtime.measure_file(Path(args.file)))
            else:
                try:
                    history = json.loads(_stdin_or(args.history))
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"invalid history JSON: {e}") from e
                _emit(airtime.measure_history(history))
        elif args.cmd == "werden":
            _emit(werden.cycle(Path(args.repo), args.structure, stamp=args.stamp))
        elif args.cmd == "config":
            _emit({"records_dir": str(_records_dir(args))})
        elif args.cmd == "import":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
            _emit(importer.run(args.source, Path(args.path), _records_dir(args), tags=tags,
                               name=args.name or myname.load(), dry_run=args.dry_run))
        elif args.cmd == "archive":
            if args.check:
                report = archive_mod.check(Path(args.repo), Path(args.out) if args.out else None)
                if not report["ok"]:
                    _emit(report)
                    return 1
                return 0                  # deliberate silence — cron mails what it prints
            _emit(archive_mod.archive(Path(args.repo), Path(args.out) if args.out else None,
                                      dry_run=args.dry_run))
        elif args.cmd == "verify":
            report = (verify.verify_archive(Path(args.archive)) if args.archive
                      else verify.verify_repo(Path(args.repo)))
            _emit(report)
            return 0 if report["ok"] else 1
        elif args.cmd == "export":
            _emit(export_mod.export(Path(args.repo), Path(args.out), single=args.single))
        elif args.cmd == "attach":
            _emit(attach.attach(Path(args.record), [Path(f) for f in args.files],
                                title=args.title, append=args.append, dry_run=args.dry_run))
        elif args.cmd == "pack":
            _emit(pack_mod.pack(Path(args.repo), Path(args.out) if args.out else None,
                                images=not args.no_images, with_books=args.with_books,
                                outdir=Path(args.outdir) if args.outdir else None))
        elif args.cmd == "card":
            _emit(card.build(Path(args.record), turn=args.turn,
                             out=Path(args.out) if args.out else None,
                             url=args.url, repo=Path(args.repo)))
        elif args.cmd == "booth":
            _emit(booth.run(_records_dir(args), arguments=" ".join(args.arguments),
                            draft=args.draft, file=Path(args.file) if args.file else None,
                            endpoint=args.endpoint, model=args.model, timeout=args.timeout,
                            name=args.name or myname.load()))
        elif args.cmd == "redact":
            out = redact.redact(Path(args.record), args.turn, replace=args.replace,
                                remove=args.remove, dry_run=args.dry_run, yes=args.yes)
            _emit(out)
            return 0 if (out["written"] or args.dry_run) else 1  # a declined prompt is not success
        elif args.cmd == "unpublish":
            d = _records_dir(args)
            if args.restore:
                _emit(unpublish.restore(args.record, records_dir=d, dry_run=args.dry_run))
            else:
                _emit(unpublish.unpublish(args.record, tombstone=args.tombstone,
                                          records_dir=d, dry_run=args.dry_run))
    except Exception as e:  # surface as JSON so the plugins can render it
        _emit({"error": str(e)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

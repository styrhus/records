"""Entry point baked into records.pyz — reports the stamped version, else runs the CLI.

build-pyz.sh stages this as the archive's root __main__.py; it is not part of the
installed package, so `records version` inside the zipapp needs no cli.py change.
"""

import json
import sys


def _version() -> int:
    from recordkit import __version__
    try:
        from recordkit._pyz import WERDEN  # stamped from CURRENT at build time
    except ImportError:
        WERDEN = ""
    json.dump({"recordkit": __version__, "werden": WERDEN,
               "python": ".".join(str(n) for n in sys.version_info[:3]),
               "zipapp": True}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def _main() -> int:
    if sys.argv[1:2] in (["version"], ["--version"]):
        return _version()
    from recordkit.cli import main
    return main()


if __name__ == "__main__":
    raise SystemExit(_main())

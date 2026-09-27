# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The engine's half of the phone app's byte contract.

tools/pwa/record.js reimplements record creation in the browser, and
tools/pwa/fixtures.json is what the two implementations agree on. This asserts
recordkit produces every fixture byte for byte; tools/pwa/selftest.html asserts
the same of record.js. A change to either side that skips the fixture fails here.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import pytest

from recordkit import create, naming, writer

FIXTURES = Path(__file__).resolve().parents[3] / "pwa" / "fixtures.json"
DATA = json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def pinned_timezone():
    """The fixtures carry real offsets (+01:00 and +02:00 across the DST line), so the
    zone has to be pinned rather than inherited from whatever machine is running this."""
    before = os.environ.get("TZ")
    os.environ["TZ"] = DATA["timezone"]
    time.tzset()
    yield
    if before is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = before
    time.tzset()


def _when(wall: dict) -> datetime:
    return datetime(wall["y"], wall["mo"], wall["d"], wall["h"], wall["mi"], wall["s"])


@pytest.mark.parametrize("case", DATA["cases"], ids=lambda c: c["name"])
def test_new_record_matches_fixture(tmp_path, case):
    when = _when(case["wall"])

    # Guard the fixture itself: if its offset and its wall-clock disagree, every
    # expected `date:` below is wrong and the failure should say so plainly.
    offset = naming.now_iso(when)[-6:]
    sign = "+" if case["wall"]["offsetMinutes"] >= 0 else "-"
    magnitude = abs(case["wall"]["offsetMinutes"])
    assert offset == f"{sign}{magnitude // 60:02d}:{magnitude % 60:02d}", (
        f"fixture offset disagrees with {DATA['timezone']} on this date")

    for existing in case.get("existing", []):
        path = tmp_path / existing
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("taken", encoding="utf-8")

    result = create.new_record(
        tmp_path,
        arguments=case["argumentString"],
        draft=case.get("draft", False),
        when=when,
    )

    expect = case["expect"]
    written = Path(result["path"])
    assert written.relative_to(tmp_path).as_posix() == expect["path"]
    assert result["title"] == expect["title"]
    assert result["tags"] == expect["tags"]
    assert written.read_text(encoding="utf-8") == expect["text"]


@pytest.mark.parametrize("case", DATA["appends"], ids=lambda c: c["name"])
def test_append_matches_fixture(tmp_path, case):
    record = tmp_path / "r.md"
    record.write_text(case["before"], encoding="utf-8")

    if case["kind"] == "human":
        writer.append_human(record, case["message"], name=case.get("who"))
    else:
        writer.append_user(record, case["message"])

    assert record.read_text(encoding="utf-8") == case["expect"]


def test_fixture_file_is_reachable_from_the_app():
    """selftest.html fetches this by relative path; if it moves, only this notices."""
    assert FIXTURES.is_file()
    assert (FIXTURES.parent / "record.js").is_file()
    assert (FIXTURES.parent / "selftest.html").is_file()

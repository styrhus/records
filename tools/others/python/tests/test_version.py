# SPDX-FileCopyrightText: 2026 tb4
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The one version number: recordkit.__version__ must equal the werden cycle in CURRENT."""

from pathlib import Path

import pytest

import recordkit


def _current() -> Path:
    """Repo-root CURRENT, walking up from this test file."""
    for parent in Path(__file__).resolve().parents:
        state = parent / "CURRENT"
        if state.is_file():
            return state
    return Path("CURRENT")  # not found; the test skips


def test_version_matches_current():
    state = _current()
    if not state.is_file():
        pytest.skip("no repo-root CURRENT — installed package, nothing to compare against")
    number = state.read_text(encoding="utf-8").split()[0]
    assert recordkit.__version__ == number


def test_version_is_a_werden_number():
    parts = recordkit.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)

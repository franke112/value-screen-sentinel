"""Vendor price data is not in the repository -- see tests/fixtures/VENDOR-DATA.json."""
from pathlib import Path

import pytest

HINT = ("vendor price data, not redistributed -- fetch your own copy with "
        "`.venv/bin/python tools/fetch_test_fixtures.py`")


def need(path) -> None:
    """Skip the calling test, saying why, when a vendor file is absent."""
    if not Path(path).exists():
        pytest.skip(f"needs {Path(path).name}: {HINT}")

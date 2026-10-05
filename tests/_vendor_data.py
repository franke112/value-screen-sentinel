"""Vendor price data is not in the repository -- see tests/fixtures/VENDOR-DATA.json."""
from pathlib import Path

import pytest

HINT = ("vendor price data, not redistributed -- fetch your own copy with "
        "`.venv/bin/python tools/fetch_test_fixtures.py`")


def need(path) -> None:
    """Skip the calling test, saying why, when a vendor file is absent."""
    if not Path(path).exists():
        pytest.skip(f"needs {Path(path).name}: {HINT}")


def need_exact(path) -> None:
    """Skip unless the file is byte-for-byte the owner's copy. For tests built
    on a VENDOR ARTEFACT (MNST's phantom halving): a refetched series that
    Yahoo has since corrected no longer carries it, and the test has nothing
    to catch."""
    import hashlib
    import json
    need(path)
    manifest = json.loads((Path(__file__).parent / "fixtures" / "VENDOR-DATA.json")
                          .read_text(encoding="utf-8"))
    rel = Path(path).as_posix().split("tests/fixtures/")[-1]
    want = next((f.get("sha256") for f in manifest["files"]
                 if f["path"].endswith(rel)), None)
    if want and hashlib.sha256(Path(path).read_bytes()).hexdigest() != want:
        pytest.skip(f"{Path(path).name} is not the owner's copy -- this test "
                    f"needs the vendor artefact it was built on, which Yahoo "
                    f"has since corrected")

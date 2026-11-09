"""tools/master_list.py: the four groups and the short block."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import master_list as ML  # noqa: E402


def _r(status, ratio=None):
    return {"status": status, "ratio": ratio}


def test_every_status_lands_in_one_of_the_four_groups():
    assert ML.group(_r("HELD")) == "ÄGDA"
    assert ML.group(_r("CANDIDATE")) == "KANDIDATER"
    assert ML.group(_r("WATCH-GATED")) == "BEVAKAS"
    assert ML.group(_r("WATCH-PRICED")) == "BEVAKAS"
    for s in ("PIPELINE", "INTAKE", "CONDITIONAL"):
        assert ML.group(_r(s)) == "ATT GRANSKA"
    assert ML.group(_r("OFF-WATCHLIST", 1.30)) == "ATT GRANSKA"   # valued, cheap, not yet walked
    assert ML.group(_r("OFF-WATCHLIST", 1.05)) == "NEJ"
    assert ML.group(_r("DROPPED")) == "NEJ"
    assert ML.group(_r("OUT")) == "NEJ"


def test_the_list_builds_from_the_repository_files_without_writing():
    short = ML.build(write=False)
    assert short.startswith("HUVUDLISTAN ")
    assert "ÄGDA:" in short

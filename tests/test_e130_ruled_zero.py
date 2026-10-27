"""E130: an unstated figure taken as ZERO by the owner's ruling, named as
generous. The case: GNTX's net interest, which Gentex never states."""
from pathlib import Path

import pytest

from vss import manual as M

STORE = Path("config/manual")


def test_gntx_carries_the_ruled_zero():
    gntx = M.load_manual("GNTX", directory=STORE)
    fy = [a for a in gntx.annual if str(a.period_end) == "2025-12-31"][0]
    fig = fy.figures["net_interest_paid"]
    assert fig.value == 0 and fig.zero_basis == M.ZERO_RULED
    assert "generous" in fig.page.lower()


def _store(tmp_path, page):
    src = (STORE / "GNTX.yaml").read_text()
    old = src.split("        zero_basis: ruled\n", 1)[1].split("\n", 2)[1]
    assert old.lstrip().startswith("page:")
    (tmp_path / "GNTX.yaml").write_text(src.replace(old, f'        page: "{page}"', 1))
    return tmp_path


@pytest.mark.parametrize("page, words", [
    ("ruled by the owner 2026-10-12, a generous zero", "E130"),
    ("E130, ruled by the owner, a generous zero", "DATE"),
    ("E130, ruled by the owner 2026-10-12", "generous"),
])
def test_a_ruled_zero_is_refused_without_its_three_marks(tmp_path, page, words):
    with pytest.raises(M.ManualError, match=words):
        M.load_manual("GNTX", directory=_store(tmp_path, page))

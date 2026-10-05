"""`vss watch --read` -- the shadow reader behind the SEC arm (2026-10-05)."""
import io
import json
from dataclasses import dataclass
from pathlib import Path

from vss import autoread as AR
from vss import secwatch as SW

REPO = Path(__file__).resolve().parents[1]


@dataclass
class Filing:
    form: str
    accession: str
    filed: str
    period_end: str = ""
    items: str = ""
    document: str = "primary.htm"


@dataclass
class Decision:
    ticker: str
    filing: Filing


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _opener(pages):
    def opener(request, timeout=None):
        return _Resp(pages[request.full_url])
    return opener


def test_an_8K_is_read_from_its_press_release_exhibit_not_its_cover():
    base = "https://www.sec.gov/Archives/edgar/data/1467373/000146737326000037"
    index = {"directory": {"item": [{"name": "acn-20261001.htm"},
                                    {"name": "q4fy26earnings8-kexhibit.htm"}]}}
    f = Filing("8-K", "000146737326000037", "2026-10-01", items="2.02,9.01")
    url = AR.document_url(1467373, f, "x y@z",
                          _opener({f"{base}/index.json": json.dumps(index).encode()}))
    assert url == f"{base}/q4fy26earnings8-kexhibit.htm"


def test_a_10Q_is_read_from_its_primary_document():
    f = Filing("10-Q", "0000822416-26-000036", "2026-07-22")
    assert AR.document_url(822416, f, "x y@z").endswith(
        "/000082241626000036/primary.htm")


def test_every_reading_is_SHADOW_and_COMPARED_and_writes_only_under_out_dir(tmp_path):
    calls = []

    def runner(**kw):
        calls.append(kw)
        return 0, "# alert"

    f = Filing("10-Q", "0000822416-26-000036", "2026-07-22")
    url = "https://www.sec.gov/Archives/edgar/data/822416/000082241626000036/primary.htm"
    out = AR.read_passed([(Decision("PHM", f), 822416)], out_dir=tmp_path,
                         contact="x y@z", opener=_opener({url: b"<html>10-Q</html>"}),
                         runner=runner)
    assert calls and calls[0]["shadow"] is True and calls[0]["compare"] is True
    assert "SENT NOWHERE" in out and "read (exit 0)" in out
    assert {p.suffix for p in tmp_path.iterdir()} == {".htm", ".md"}


def test_a_failed_reading_is_named_and_never_raised(tmp_path):
    def runner(**kw):
        raise RuntimeError("model down")

    f = Filing("10-Q", "0000822416-26-000036", "2026-07-22")
    url = "https://www.sec.gov/Archives/edgar/data/822416/000082241626000036/primary.htm"
    out = AR.read_passed([(Decision("PHM", f), 822416)], out_dir=tmp_path,
                         contact="x y@z", opener=_opener({url: b"x"}), runner=runner)
    assert "NOT READ -- RuntimeError: model down" in out


def test_the_reader_runs_AFTER_the_post_and_cannot_cost_it(tmp_path):
    """The notification is the point; a reader that blows up must leave it
    sent and the cursor saved."""
    f1 = Filing("10-Q", "a1", "2026-07-22")
    state = tmp_path / "state.json"
    SW.run_secwatch(watchlist_path=REPO / "config" / "watchlist.yaml",
                    state_path=state, poster=lambda l, url=None: "x",
                    now="2026-10-05T00:00:00+00:00", fetch=lambda cik: [])
    sent = {}

    def poster(lines, url=None):
        sent["lines"] = list(lines)
        return "sent"

    def reader(items):
        raise RuntimeError("boom")

    code, report = SW.run_secwatch(
        watchlist_path=REPO / "config" / "watchlist.yaml", state_path=state,
        poster=poster, now="2026-10-05T01:00:00+00:00",
        fetch=lambda cik: [f1], reader=reader)
    assert code == 0 and sent["lines"]
    assert "AUTO-READ FAILED -- RuntimeError: boom" in report
    assert "a1" in json.loads(state.read_text())["sec"]["CTSH"]["accessions"]

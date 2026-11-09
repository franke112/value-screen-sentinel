# HANDOFF 2026-11-09 PM -- START HERE

**BOTH TODOs BELOW ARE DONE (2026-11-09, evening).** What is left is the
owner's: `bash ~/stocks/tools/mirror_public.sh`, review, commit, then push
both repos (the public push also publishes the book on GitHub Pages).
Next work is the calendar under "Upcoming events": Proact's CMD 2026-11-11.

Written at the end of a long session for the next one, which will run on a
newer model. The owner's word (2026-11-09): "gör allt du sa ... fixa allt".
Everything below is the session's plan, agreed; do it without asking again
(E141), commit per step, the owner pushes.

## State (everything committed; private ~/stocks and public ~/vss-public both pushed except bca0697 below)

- **Nordic sift done** (`reference/screens/NORDIC-SIFT-2026-11-09.md` + `.yaml`,
  PRIVATE). the screen's machine names -> CANDIDATES Proact (PACT.ST) and Stillfront
  (SF.ST); EVO WATCH at the line (look 843); PHM and Sinch NO; the rest out.
  Reviews in `reference/reviews/{AFRY.ST,PACT.ST,EVO.ST,PHM,SF.ST,SINCH.ST}/`.
- **Screen data rules** (10ead96): lease charge 0.35 x lease liability, capex
  gap refusal, EODHD empty debt total read from its parts (logged in
  `reference/backtest/ATTEMPTS.md`; #26 runs fixed).
- **Master list** `tools/master_list.py` -> `reports/HUVUDLISTA.md`, nightly
  via `vss queue`; SessionStart hook in `.claude/settings.json` prints the
  short block. **CLAUDE.md: the session's first output is that block.**
- **Nightly reading** (7c15a21): `vss/reportread.py` reads every queue name's
  new report (EDGAR / Nasdaq Nordic / Oslo) twice via `vss earnings`;
  `vss/outlook.py` re-values on four quarters and sends `UTSIKT` only on a
  change. RAPPORT is no longer sent. Tested end to end and as the systemd
  service. Queue unit timeout 60 min (installed + deploy/).
- **Public README** rewritten (14dbe6f). **The book** brought up to date in en
  + sv (public **bca0697 -- check it is pushed**: `cd ~/vss-public && git status -sb`).
- EODHD rule: vendor figures never in public, not even in comments (6053055).

## Upcoming events (the outlook check reads the reports by itself)

- **2026-11-11**: Proact CMD -> build `config/manual/PACT.ST.yaml`, strike,
  verdict (open checks in `reference/reviews/PACT.ST/2026-11-09-sift-review.md`).
  Scandinavian Tobacco Q3 and Lundbeck Q3 -> review STG (CONDITIONAL).
- **2026-11-17**: ZZ-B Q3 -> full review (rough value only so far).
- **2026-11-20**: MMS FY2026 10-K -> review.
- **2027-02-01**: ACAD owner override expires (Q2 report). **2027-02-04**: EVO year-end.
- Stillfront CANDIDATE needs a store + strike before any buy.

## TODO 1 -- DONE 2026-11-09 (evening session, Fable 5.2)

Private commits 873af37, ddc3fde, 1e23ca4, aa591c5, f7b5374; public c95f573
(NOT pushed). What was done, against the audit below:

- **Code side.** The report and the overview no longer claim a stop is
  checked; E162(3) had already ruled the column stays as the owner's note,
  so it is labelled `Stop (note)`, prints `none`, and left the ACTIONS
  table. `vss screen --help`, the usage text and the PIPELINE note say
  seeded order (E167). Every tool that takes arguments has `build_parser()`
  with help text. `config/watchlist.example.yaml`'s header was stale too
  (old cushions, a NO STOP DEFINED flag, four statuses) and is corrected.
- **`docs/REFERENCE.md` is generated** by `tools/build_manual_reference.py`
  (25 subcommands, 18 tools, timers off deploy/, env vars, files, modules)
  and `tests/test_manual_reference.py` holds it equal; CLAUDE.md has the
  same-commit rule; the mirror script regenerates the public page (step 5b).
  The facts were checked by RUNNING each harmless form and listing touched
  files: `vss xbrl` logs every run, `vss queue --dry-run` still reads a new
  report into data/autoread/, `vss strike` exits 2 on an events ledger older
  than 7 days.
- **Public docs:** MANUAL.md in four parts (775 lines, was 1552),
  EXPLANATION.md (the design passages moved, corrected), CHANGELOG.md,
  AGENTS.md, llms.txt; CLAUDE.md / SETUP.md / reference/README.md / Makefile
  no longer point at the playbook. 154 relative links and anchors checked.
- **LEFT FOR THE OWNER:** `bash ~/stocks/tools/mirror_public.sh` (brings the
  code the pages describe and regenerates the public REFERENCE.md with the
  one public-only tool), review, commit, push both repos.

### The audit it answered (kept as the record)

Audit (2026-11-09, against the code) found:

**Wrong:**
- L763 queue table says `KÖPLINJE`; the code sends `UNDER MBP` (queue.py ~507). The table also lacks `RÄTTELSE`, `RAPPORTKONTROLL FELADE`, `SÄLJ EJ UTFÖRD`, the weekly size-ceiling line; `RAPPORT` row must go (now `UTSIKT`).
- L1360-1369 staleness: 3 **trading** days (rules.py `MAX_CLOSE_AGE_TRADING_DAYS`, calendars.py), and 1 session for HELD / names with an MBP (`..._LEVEL = 1`); not calendar days.
- L181-195 exit codes of `vss run`: add 1 (coverage gate) and 3 (`EXIT_STALE_DRY_RUN`: a dry run refuses when a level-carrying close is > 1 session old).
- Stop remnants vs E162: L1338 "distance to stop", L1175 overview "a stop breached"; the code still has `pct_to_stop` (runner.py ~351), a Stop column and "The stop is LIVE" in report.py (~513, ~624) -> decide: remove from code or label information; make manual and report agree.
- L1315-1325 watchlist schema: add INTAKE; keys cik, fv_bull, fv_void, dd_at_entry, peak_date, quarters, exec_changes, fx, mbp_basis, run_record, sales, growth (config.py ~59, rules.py ~166/173); stop_price optional (`none`).
- L1158 `tools/backfill_shadow_book_2026_09_08.py` does not exist.
- L1546-1551 "nothing reads run_metrics back" is false (strike.py ~182, rules.py ~550).
- L1486-1488 tests text cites stop / band / RSI edge cases that are no longer verdicts -- check tests/.
- L1493-1536 layout lists ~22 of ~70 modules; tools/ described as build-time only.
- L1447-1450 timers: missing vss-watch (13:00, 23:30), vss-newsdrop (Mon-Fri 23:00), vss-nordic-screen (Sat 08:00), vss-eodhd (01:30 UTC), vss-eodhd-reminder (15 Apr), vss-overview, vss-failure@; give each ExecStart.
- L1012 editorial leftover ("The rest of this paragraph...") contradicting the seeded draw; `vss screen --help` still says "dislocation band" and "two-component ranking key (E6)" -> fix the CLI help text in vss/screen.py too (private first, then mirror).
- L797 says `.claude/settings.json` SessionStart hook -- not shipped in public; say how to add it.
- L100-111 "What changed 2026-11-08" changelog in the middle -> move to a CHANGELOG section/file.

**Undocumented:** subcommands newsdrop, watch (flags --read --no-send --cron --sec-only --nordic-only --state --ntfy-url), refresh, checkin, backfill-vendor-strings, reference-figures, briefing, prepare, strike, review, history (--xbrl --check --dir --cik); many flags (queue --asof --only --dry-run; screen --weekly --keep --no-notify --sec-shadow --top --tier ...; xbrl --annual --write --force ...; sales --reconcile --since; shadow --book; overview --output; ...); tools rough_fv.py (no argparse -- `--help` is read as a ticker: add argparse), quotecheck.py (no argparse), rule_impact.py, cross_verify.py, nordic_screen.py --notify, master_list.py, build_queue.py; files config/queue.yaml schema, data/outlook_state.json, data/queue_state.json, data/autoread/, reports/*.

**Plan (Diátaxis):** 1 Getting started (install + first run, once) · 2 How-to tasks (add a name, strike, read a report, Nordic report, screen, queue) · 3 Reference: ONE table per command (purpose, inputs, flags, reads, writes, network, notifies, exit codes), env-var table (VSS_SEC_CONTACT, VSS_OPENROUTER_KEY/_MODEL, NTFY_TOPIC, VSS_NTFY_URL, EODHD_API_KEY, BT_WORKERS), timer table, file table · 4 Explanation (DATA MISSING, provenance, rulings) moved out of the command sections · CHANGELOG.
**Generate the command reference from argparse** (a tool, e.g. `tools/build_manual_reference.py`, writing `docs/REFERENCE.md`) **and a test that holds it equal**, like `config/review/SCHEMA.md`. Add `AGENTS.md` (+ optional `llms.txt`) at the repo root: exact, safe-vs-writing-vs-notifying commands for an AI. Use `.venv/bin/python` consistently. Do the code-side fixes (screen --help text, rough_fv/quotecheck argparse, stop remnants) in ~/stocks, run the suite, then the owner mirrors (`bash ~/stocks/tools/mirror_public.sh`). MANUAL.md, README, docs/ are PUBLIC-ONLY files: edit them in ~/vss-public directly.

## TODO 2 -- the book `~/vss-public/docs/the-method/` (en + sv, `_build/content*.py`, `python3 build.py`)

Verdict: prose is good; order and form are the problem. Plan:
1. **New order:** a prologue with the test story (26 attempts, most rules died, no proven edge, why we go on); Part One = the method as it is now; the tests chapter in the middle; Part Two cut from nine chapters (13-21) to about three (how the machine reads, how it watches, the limits). Chapter numbering and `build.py`/index counts follow.
2. **One company through the book: CENTA** (bought 2026-10-26 at 39.33, the method check, the E142/acquisition trap, the Burpee estimate, sold 146 of 148 on 10-27/28) -- a box "CENTA at this step" per chapter. Facts: memory files centa-*, lessons-centa-e140, reference/CENTA-STRIKE-*.md, watchlist CENTA notes. Figures from the issuer's filings only (public).
3. **Interactive figures, inline HTML/JS, no external deps** (diagrams.py pattern): reverse DCF slider (price -> implied growth; the book's core idea, do first), the funnel with real counts, the rules graveyard (rule / test / why it died), the shadow book against the index.
4. **"The bug museum"** chapter: AUTO.L pence/pound +12,791 %, COH.US (a reused ticker; its percentage stays in the private review), the debt-free names (in words, no EODHD figures), the seven restart notifications, the queue crash on 2026-11-09.
5. **Fixed chapter template:** the claim in one sentence, a story, the rule, what the test said, "try it" (one command), three-line summary. Two reading routes (investor / builder) beside the ten-minute route.
Models named to the owner: Greenblatt (Little Book), Damodaran (Narrative and Numbers), Buffett letters / Marks memos (mistakes admitted), Annie Duke (Thinking in Bets), Housel (Psychology of Money), explorable explanations (Bret Victor, Nicky Case, Ciechanowski), Julia Evans zines. The owner may want sourced research first (deep-research skill) -- offer it once, then build.
Keep the EODHD rule in every figure (verdicts in words).

## Rules that bind the next session
- CLAUDE.md (cost discipline, subagents Sonnet <= medium for fetch/read only, commit per step).
- Memory: master-list-first, nordic-sift-2026-11-09, public-repo (EODHD rule, mirror by the owner's script), stop-the-review-loop, e141-session-decides.

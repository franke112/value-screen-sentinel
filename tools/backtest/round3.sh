#!/usr/bin/env bash
# ROUND 3 on the VPS (owner 2026-11-08, sweep E18): ATTEMPTS #23 and #24.
# Builds what wrez-devour held and this machine lacks, then runs both tests.
# Every step is RESUMABLE: a step whose output exists is skipped, so after a
# failure the same command is run again. Log: reports/attempts/round3.log
#
#   systemd-run --user --unit=vss-round3 --property=Nice=19 \
#       --working-directory=~/vss tools/backtest/round3.sh
#   journalctl --user -u vss-round3 -f        # or: tail -f reports/attempts/round3.log
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=reports/attempts
mkdir -p "$OUT"
exec >>"$OUT/round3.log" 2>&1
export BT_WORKERS=2                 # 2 cores, 4 GB: never devour's 17-22
PY=".venv/bin/python"
BT=data/backtest
step() { echo; echo "=== $(date -Is) $*"; }

step "1/7 Nordic engine -> nordic-m7 (quarter-start fix, cleaned prices)"
if [ ! -f "$BT/nordic-m7/2021-04-30.jsonl" ]; then
  $PY -m tools.backtest.nordic --out "$BT/nordic-m7"
fi
# fscore_accruals reads the Nordic rows as nordic-m6 when DEVOUR_LB is unset;
# m7's valuations equal m6's on every row (ATTEMPTS #17), and only assets are read
[ -e "$BT/nordic-m6" ] || ln -s nordic-m7 "$BT/nordic-m6"

step "2/7 F-score signals (Nordic assets for the E43 key) -> devour-fscore-m6"
if [ ! -f "$BT/devour-fscore-m6/signals-nordic.jsonl" ]; then
  $PY -m tools.backtest.fscore_accruals --signals --workers "$BT_WORKERS"
fi

step "3/7 US cleaned twins -> run-eodhd-bust-m5-clean, run-eodhd-m5-clean"
if [ ! -f "$BT/run-eodhd-bust-m5-clean/2020-04-30.jsonl" ]; then
  $PY -m tools.backtest.nolb --mode clean
fi

step "4/7 US engine rows 2021-2025 for #23's realised windows -> data/backtest/run"
for y in 2021 2022 2023 2024 2025; do
  # the candidate universe of the date first (EDGAR index + frames), then the rows
  [ -f "$BT/universe/$y-04-30.json" ] || $PY -m tools.backtest.universe --date "$y-04-30"
  [ -f "$BT/run/$y-04-30.jsonl" ] || $PY -m tools.backtest.run --date "$y-04-30" --workers "$BT_WORKERS"
done

step "5/7 Round-2 signals with #24's rev_declines and inv_growth -> devour-fundsig-r2"
if [ ! -f "$BT/devour-fundsig-r2/us-bust.jsonl" ]; then
  DEVOUR_LB=clean $PY -m tools.backtest.fundsig
fi

step "6/7 ATTEMPT #23"
$PY -m tools.backtest.a23_growth > "$OUT/A23-RESULT.md"

step "7/7 ATTEMPT #24"
DEVOUR_LB=clean $PY -m tools.backtest.a24_deciles > "$OUT/A24-RESULT.md"

step "DONE -- results in $OUT/A23-RESULT.md and $OUT/A24-RESULT.md"

#!/bin/sh
# THE DEAD MAN'S SWITCH, leg 2: systemd tells the phone that a unit failed.
#
# Invoked by `vss-failure@.service`, which every vss unit names in its
# `OnFailure=`. It fires the moment a run exits non-zero or hits its
# `TimeoutStartSec=` -- the only leg that reports an outage WHILE IT IS
# HAPPENING rather than after a later run notices the gap.
#
# WHY THIS IS A SHELL SCRIPT AND NOT `python -m vss ...`. The failure being
# reported may BE the Python: a broken venv, an unimportable module, a
# corrupt sqlite. A notifier that shares its dependencies with the thing it
# watches goes silent for exactly the failures worth paging about. This
# needs `/bin/sh` and `curl` and nothing else -- no venv, no package, no
# database.
#
# E92's rules apply unchanged: OUTBOUND ONLY, an unset topic is SILENCE and
# never an error, and a failed POST is never itself an error. THIS SCRIPT
# ALWAYS EXITS 0. A failure notifier that can fail is a second thing to
# monitor.
#
# Usage: vss-notify-failure.sh <unit-name>

set -u

unit="${1:-an unnamed vss unit}"
host="$(hostname 2>/dev/null || echo unknown-host)"
when="$(date '+%Y-%m-%d %H:%M:%S %Z' 2>/dev/null || echo 'unknown time')"

# An unset topic is silence, not an error (E92).
if [ -z "${NTFY_TOPIC:-}" ]; then
    echo "NTFY_TOPIC is not set: no notification sent (E92: silence, not an error)" >&2
    exit 0
fi

case "$NTFY_TOPIC" in
    http://*|https://*) url="$NTFY_TOPIC" ;;
    *)                  url="https://ntfy.sh/${NTFY_TOPIC#/}" ;;
esac

# The last few journal lines for the unit that died. This is the difference
# between "something broke" and a pointer you can act on without opening a
# terminal. Bounded hard: a lock screen is not a log viewer, and a unit that
# failed by emitting ten thousand lines must not push a ten-thousand-line
# body at ntfy.
tail_lines=""
if command -v journalctl >/dev/null 2>&1; then
    tail_lines="$(journalctl --user -u "$unit" -n 8 --no-pager -o cat 2>/dev/null \
                  | cut -c1-160 | tail -n 8)"
fi

# WHAT STOPPED depends on WHICH unit died (backlog B-13). vss-failure@.service
# passes the failing unit's own name in (%n -> %I), and until 2026-09-13 every
# unit was given the nightly run's sentence -- "no report was written for this
# date" -- which was false for vss-overview.service on the day it looped, and
# is false for any unit that is not a run. The run units keep that sentence;
# every other unit says what it is, and an unknown one says only that.
case "$unit" in
    vss.service|vss-screen.service)
        what="The run did not complete. Nothing downstream of it has run: no report was
written for this date, and no pointer it would have sent will arrive." ;;
    vss-overview.service)
        what="The overview page server stopped and systemd could not keep it up, so the
page is not being served until it is back. The nightly run, its report and
its alerting are unaffected: they do not depend on this unit." ;;
    vss-checkin.service)
        what="The dead man's switch check-in did not complete, so this run of it checked
nothing. It reads and posts; no report or pointer depends on it." ;;
    *)
        what="$unit is not a run unit. No report or pointer depends on it; what has
stopped is whatever $unit provides. Read the journal." ;;
esac

body="$unit FAILED on $host at $when.

$what

  journalctl --user -u $unit -n 100 --no-pager

Last lines:
${tail_lines:-(no journal lines available)}"

# --max-time so a hung ntfy cannot hold a systemd job open; the trailing
# `|| true` because a notifier may never be the reason anything fails.
printf '%s' "$body" | curl -fsS --max-time 10 \
    -H "Title: vss: $unit FAILED" \
    -H "Priority: high" \
    -H "Tags: rotating_light" \
    --data-binary @- \
    "$url" >/dev/null 2>&1 || \
    echo "ntfy POST failed; the failure is still in the journal" >&2

exit 0

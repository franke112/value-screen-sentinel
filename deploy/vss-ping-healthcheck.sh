#!/bin/sh
# THE DEAD MAN'S SWITCH, leg 4: the OUTSIDE observer.
#
# Legs 1-3 all run on this machine, so none of them can report this machine's
# absence: a powered-off VPS, a network that is down, a user manager that
# never started after a reboot -- all three legs are silent, and the silence
# is indistinguishable from a quiet week. That is structural and no amount of
# local code closes it.
#
# THIS CLOSES IT BY INVERTING THE SIGNAL. The nightly run pings a URL when it
# SUCCEEDS; the service at the far end alarms when a ping DOES NOT ARRIVE. So
# the thing that pages is the absence, and the absence is exactly what a dead
# box produces. Nothing here has to work for the alarm to fire -- that is the
# whole point of it.
#
# WHAT LEAVES THE MACHINE: one HTTP GET to an opaque UUID. No ticker, no
# price, no report, no hostname, no body. The far end learns that something
# it knows only as a UUID is alive, and nothing else. (Owner, 2026-09-01:
# "a dead VPS is exactly the case I want covered and no ping leaves data.")
#
# E92's rules apply unchanged: an unset URL is SILENCE and never an error,
# and a failed ping is never itself an error -- the report on disk is the
# record, and a network blip must not turn a good run into a failed unit.
# THIS SCRIPT ALWAYS EXITS 0.
#
# Usage: vss-ping-healthcheck.sh [/fail]

set -u

suffix="${1:-}"

if [ -z "${HEALTHCHECK_URL:-}" ]; then
    echo "HEALTHCHECK_URL is not set: no ping sent (E92: silence, not an error)" >&2
    exit 0
fi

# --retry so a single dropped packet does not read as a dead machine at the
# far end; --max-time so a hung endpoint cannot hold a systemd job open.
curl -fsS --max-time 10 --retry 3 --retry-delay 2 \
    "${HEALTHCHECK_URL}${suffix}" >/dev/null 2>&1 || \
    echo "healthcheck ping failed; the run itself is unaffected" >&2

exit 0

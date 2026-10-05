# deploy — what is scheduled here, and what is deliberately not

## `vss.timer` / `vss.service` — the nightly run, 22:30

`python -m vss run`. Writes `reports/YYYY-MM-DD.md`, `reports/OVERVIEW.html`
and the sqlite history, and nothing else: `ReadWritePaths` is `data/` and
`reports/`.

**The overview page rides on the same unit and cannot break it.** It is
regenerated AFTER the report is on disk and the database row is written, so
the run's own job is already done when it starts; a failure is logged at
WARNING (`journalctl --user -t vss -p warning`) and the unit still exits 0.
A **scoped** (`--ticker`) run does not write it: a forty-name page built
beside a one-name run would show the other thirty-nine at whatever the cache
last held, without saying so. Regenerate it by hand with
`python -m vss overview`.

Installed as **copies** under `~/.config/systemd/user/`, not symlinks — a
change here does not reach the running timer until it is copied over and
`systemctl --user daemon-reload` is run.

## `vss-screen.timer` / `vss-screen.service` — the weekly screen, Sat 08:00

`python -m vss screen --weekly` (FRAMEWORK-EDITS **E93**). Snapshot →
fundamentals → rank → store the ranked order → compare with the previous
stored run → `reports/SCREEN-<date>.md` → prune → pointer.

`ReadWritePaths` is `data/` and `reports/` — the same as the nightly run.
**`config/` is not writable by this unit**, which is the ruling in one line.

**`--write-pipeline` is deliberately absent from `ExecStart` and must stay
absent.** Entering a name as PIPELINE stamps `dd_at_entry` and `peak_date`
and **E12 freezes Gate 1 at that moment** — a timer would freeze a catalyst
window on an arbitrary Saturday at whatever the previous close was, and
unlike a fair value that is not undone by re-striking. The run also compares
the watchlist's bytes either side of itself and stops if they differ.
`tests/test_screenwatch.py` pins both the absent flag and the ReadWritePaths.

Retention: the last 4 price snapshots (~235 MB each); **every ranking is kept
forever** in `screen_rankings`, because every future comparison stands on it.

**Tier: `--tier A --tier B`** (owner, 2026-09-01). Tier A is 1,360 large
caps; tier B adds the S&P MidCap 400 and the Oslo / Copenhagen / Helsinki mid
caps, **+651 instruments to 2,011**. Measured 2026-08-31: the chain goes from
~25 to ~38 minutes against the 4-hour timeout, with **zero throttles across
3,495 fundamentals requests**, and seven of the resulting top twenty were
names the old universe could not see. `reports/UNIVERSE-WIDENING-2026-08-31.md`.

**The first widened run needs nobody to remember anything.** It diffs against
a tier-A baseline, and every crossing between the two would be the tier change
rather than the market. `screen_rankings.tiers` records the universe each
ranking was struck on, and `basis_mismatches` refuses the comparison and
withholds the pointer until two consecutive runs agree — the same rule as the
regenerated-baseline case, generalised. It stops applying by itself; nothing
expires on a date.

## The dead man's switch — three legs, and what none of them covers

**The problem it solves.** Before it, a nightly run that CRASHED and a
nightly run with NOTHING TO SAY were the same thing on the phone: silence.
The E92 pointer fires only when a name is waiting, so no pointer meant
either "nothing needs you" or "the run has been dead since Tuesday".

### Leg 1 — the run records itself

`data/vss.sqlite` → `run_completions`. A row is INSERTED when a run starts
(`completed = 0`) and UPDATED when it reaches its end. Three states, none
inferred: **no row** = it never started; **completed = 0** = it started and
died; **completed = 1** = it finished, and `covered`/`expected` say how much
of the list it actually got (PRICED coverage for the nightly, RANKED for
the weekly — not row counts, so a night when every fetch failed cannot
record itself as complete).

The next run reads the newest completed **full, non-dry** run. More than
**72 hours** (nightly) or **10 days** (weekly) and the run says so, in a
`## RUN CONTINUITY` block at the top of its report and in its own ntfy post
with its own title. A `--ticker` run and a `--dry-run` **do not reset the
clock** — a week of one-ticker runs must not read as a week of healthy ones.

**What it cannot do:** report an outage that is still happening. It needs a
later run to succeed before anyone hears about the gap.

### Leg 2 — `OnFailure=` on every unit

`vss.service`, `vss-screen.service` and `vss-checkin.service` each carry
`OnFailure=vss-failure@%n.service`, which runs
`deploy/vss-notify-failure.sh <unit>`. It posts the unit name, the host, the
time and the last eight journal lines the moment the unit exits non-zero or
hits its `TimeoutStartSec=`. **This is the only leg that fires while the
outage is happening.**

It is `/bin/sh` + `curl`, with **no venv, no package and no database**, on
purpose: the failure being reported may BE the Python. It always exits 0 —
a failure notifier that can fail is a second thing to monitor.

### Leg 3 — `vss-checkin.timer`, daily 09:30

`python -m vss checkin`. **A SEPARATE TIMER FROM `vss.timer`, deliberately.**
Legs 1 and 2 both need the run to at least *start*; a timer that was
disabled, masked, or never re-lingered after a reboot starts nothing, so
neither fires — and that failure looks exactly like an ordinary quiet week.
The check-in asks two things the run cannot ask about itself:

* is a completed run on record at all, and how old is it;
* are `vss.timer` and `vss-screen.timer` still **enabled AND active**.

Silence when healthy. A finding **exits 0**, so the check-in's own
`OnFailure=` stays reserved for the check-in itself being broken — a
different fact, which must not be reported as the same one. The unit has
**no `ReadWritePaths` at all**: it opens the database `mode=ro` and writes
nothing.

### Leg 4 — the outside observer: `HEALTHCHECK_URL`

**Legs 1-3 all run on this machine, so none of them can report this machine's
absence.** A powered-off VPS, a network that is down, a user manager that
never started after a reboot — all three go silent, and the silence reads as
a quiet week. That is structural, and no amount of local code closes it.

Leg 4 closes it by **inverting the signal**. `vss.service` carries
`ExecStartPost=-deploy/vss-ping-healthcheck.sh`, which GETs `HEALTHCHECK_URL`
**only when the run succeeded** (`ExecStartPost` runs after a successful
`ExecStart`, which is exactly the semantic wanted). healthchecks.io alarms
when the ping **does not arrive**. Raising that alarm needs nothing from this
machine, which is the whole point.

**One opaque UUID, one GET, no body.** No ticker, no price, no report, no
hostname leaves the machine; the far end learns that something it knows only
as a UUID is alive. Unset is silence (E92), and the leading `-` on
`ExecStartPost` is load-bearing: **a failed ping must never turn a good run
into a failed unit**, which would fire the OnFailure pointer over a network
blip and teach the reader to ignore it.

Set it in `~/.config/vss/vss.env`. Suggested far-end settings: **period 1
day, grace 6 hours** — the run is 22:30 daily with `Persistent=true`.

### What is STILL not covered, with leg 4 in place

* the **weekly screen** has no ping of its own — leg 4 watches the *nightly*
  run, which is the daily proof the box is alive. A Saturday that never runs
  is caught by leg 1's 10-day bar and leg 3's timer check, not by leg 4;
* a machine that is **up and pinging but wrong** — the ping means "the run
  exited 0", not "the report is right". Legs 1 and 3 carry the coverage;
* **healthchecks.io itself** being down, or its mail not reaching you.

### Installing and testing it

```sh
cp deploy/vss.service deploy/vss-screen.service \
   deploy/vss-checkin.service deploy/vss-checkin.timer \
   'deploy/vss-failure@.service' ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vss-checkin.timer

vss checkin --no-send            # what it would say, posting nothing
```

For leg 4, create a check at healthchecks.io, put its ping URL in
`~/.config/vss/vss.env` as `HEALTHCHECK_URL=`, and confirm it once by hand:

```sh
set -a; . ~/.config/vss/vss.env; set +a
deploy/vss-ping-healthcheck.sh   # silent on success; the check goes green
```

To prove the `OnFailure=` path end to end, install a unit that fails on
purpose and watch the notifier start (this DOES post to the real topic):

```sh
printf '[Unit]\nOnFailure=vss-failure@%%n.service\n[Service]\nType=oneshot\nExecStart=/bin/false\n' \
    > ~/.config/systemd/user/vss-failure-test.service
systemctl --user daemon-reload && systemctl --user start vss-failure-test.service
journalctl --user -u 'vss-failure@vss-failure-test.service.service' -n 20 --no-pager
rm ~/.config/systemd/user/vss-failure-test.service && systemctl --user daemon-reload
```

Done live on 2026-08-31: the journal recorded *"Triggering OnFailure=
dependencies"* → *"Finished vss-failure@vss-failure-test.service.service"*,
and the notifier logged neither "NTFY_TOPIC is not set" nor a POST failure,
so `curl -f` got a 2xx.

## `vss refresh` is NOT SCHEDULED — decided by the owner, 2026-08-31

**Do not add a timer, a cron line, or a nightly call to `refresh`.**

`vss refresh` (FRAMEWORK-EDITS **E92**) writes into `config/manual/`, which
is a **git-tracked configuration directory**. The owner decided on
2026-08-31 that unattended writes into tracked config will not run while he
sleeps; he runs `vss refresh --due` **by hand** on report weeks.

Scheduling it would need `ReadWritePaths` widened to `config/manual` —
**that widening is the decision, not the plumbing.** It is decided. If a
future session thinks it should be scheduled, that is a new owner decision,
recorded as a dated entry beneath E92 in `reference/FRAMEWORK-EDITS.md`,
before any unit file changes.

The **nightly run still surfaces** whatever a hand-run refresh left behind,
as its NEEDS OWNER section, and posts the pointer. That half is automatic
and decides nothing.

## The notification topic

`NTFY_TOPIC` is read from the environment and is **never committed**. The
live value lives OUTSIDE the repository, at `~/.config/vss/vss.env`, and
`vss.service` picks it up with `EnvironmentFile=-` (the `-` means a missing
file is not an error). See `vss.env.example` for the shape.

For an interactive `vss refresh` or `vss run`, the same file works in a
shell: `set -a; . ~/.config/vss/vss.env; set +a`.

The topic is **outbound only** — nothing in this project ever reads from
it (E92). `vss watch` keeps its own separate, older `VSS_NTFY_URL`: a
refresh pointer is not a disclosure alert, and one may be set without the
other.

## `vss-overview.service` — the overview page, 2026-09-13

`vss-overview.service` rebuilds `reports/OVERVIEW.html`, the read-only
overview page. In the owner's deployment it is served behind Cloudflare
Access over an outbound-only Cloudflare Tunnel (no inbound port, Caddy on
`127.0.0.1` returning 404 for every path but the page). **The tunnel unit
and its notes are specific to that server and are not included here.**
Serve the page however suits you -- or just open the file.

Ruling **F1** (FRAMEWORK-EDITS, 2026-09-13) governs the page's shape.


# Solution Architecture: Crypto Radar — Phase 1

| | |
|---|---|
| **Scope** | Phase 1 only (PRD R1–R5, R7) — single-repo scan, baseline/diff, risk register, dashboard |
| **Status** | ✅ Approved. Includes `--fail-on-new` (exit-code gate, unused until R8) — kept in scope after explicit review since it's cheap now and makes the CI fast-follow a config change, not new scanner logic. |
| **Depends on** | [`README.md`](README.md) — the approved PRD. This document doesn't re-argue product decisions already made there. |

## Tech stack

**Pure Python 3.11+, standard library only — zero dependencies.** A tool whose pitch is "trivial for a compliance officer or DevOps engineer to run" loses credibility if step one is `pip install` and dependency resolution. Detection uses `re`; the dashboard is hand-built HTML/SVG via string templating — no charting library, no web framework, no build step.

**Feasibility check:** every Phase 1 requirement (pattern matching, JSON I/O, static HTML/SVG generation) is comfortably within stdlib. No blockers, no unproven technology. The only real engineering cost is hand-rolling SVG charts instead of using Chart.js — more code, but it's what keeps the dashboard a single offline-openable file, which is the point.

## Module layout

```
pqc_radar/
  signatures.py   # R1: detection patterns per language/algorithm (carried over, already verified)
  scanner.py      # R1-R2: walk files -> list[Finding] with risk, file, line, fingerprint
  baseline.py     # R3: load/save baseline.json; diff current vs. baseline -> New/Existing/Resolved
  register.py     # R4: accept a finding (ticket, reason, review-by); check expiry on read
  report.py       # R5: merge scan + diff + register -> report.json; render dashboard.html
  cli.py          # subcommands: scan, accept, dashboard
examples/sample_app/
  <multi-language sample files with planted findings>
  .pqc-radar/baseline.json       # committed, shows what a real baseline looks like
  .pqc-radar/register.json       # committed, includes one deliberately-accepted finding (R7)
  dashboard.html                 # PRE-GENERATED AND COMMITTED — reviewers open this directly,
                                  # no need to run Python to see the artifact
tests/
  test_scanner.py, test_baseline.py, test_register.py   # not a PRD requirement, added here:
                                                          # cheap, and tested code signals more
                                                          # engineering rigor than untested code
```

## Data formats

- **`findings`** (in-memory / JSON): `{file, line, language, algorithm, risk, note, snippet, fingerprint}` — unchanged from the scanner built during PRD iteration.
- **`.pqc-radar/baseline.json`** (committed to the target repo): `{saved_at, tool_version, findings: [...]}`. Written **only** by explicit `pqc-radar scan --save-baseline`, never silently by a plain scan. *(Your call, confirmed below.)*
- **`.pqc-radar/register.json`** (committed): keyed by fingerprint → `{status: "accepted", ticket, reason, review_by, accepted_on}`.
- **`report.json`** (scan output, not committed by default — it's a point-in-time artifact): current findings, diff classification against the baseline, register annotations, and summary counts. This is what `dashboard` reads.
- **`dashboard.html`** (generated from `report.json`): self-contained, inline CSS/SVG, no external assets.

## Decision: baseline update semantics — **CONFIRMED: explicit `--save-baseline`**

A plain `pqc-radar scan` never writes the baseline. A finding stays classified `new`/`unreviewed` across repeated scans until a human either fixes the code, runs `pqc-radar accept <fingerprint> --ticket ... --review-by ...` to register it as sanctioned, or deliberately re-runs with `--save-baseline` to accept it into the tracked baseline. This is slightly less convenient than auto-updating, but it's the difference between the register being real audit evidence and it being security theater — a new RSA call can't quietly stop being flagged just because someone ran the tool twice.

## Decision: pre-generated dashboard — **CONFIRMED: commit `examples/sample_app/dashboard.html`**

A hiring manager or reviewer should be able to open the committed `dashboard.html` directly in a browser from the repo — no Python, no setup — and see exactly what the tool produces: summary counts, the risk register with one accepted/time-boxed finding, and the finding list. The build commands to regenerate it from the sample data are documented but running them isn't required to see the artifact.

## CLI surface

```
pqc-radar scan <path> [--baseline FILE] [--save-baseline] [--out report.json]
pqc-radar accept <fingerprint> --ticket TICKET --review-by YYYY-MM-DD [--reason TEXT]
pqc-radar dashboard <report.json> [--out dashboard.html]
```

**Optimization worth calling out:** `scan` will support a `--fail-on-new` flag (non-zero exit when unreviewed-new findings exist) even though Phase 1 has no CI to consume it. It's near-free to add now, and it means R8 (the CI fast-follow) is wiring an existing flag into a YAML file, not new scanner logic. Flagging this so it's a visible choice, not scope creep — no new requirement, just an implementation detail that makes the fast-follow cheap later.

## New vs. Existing vs. Register — the core logic (this is what makes G3 real)

For every finding in the current scan:
1. Compute fingerprint (stable across line-number drift — already built)
2. Classify vs. baseline: **New** (not in baseline) / **Existing** (in baseline) / *(baseline-only entries not seen now become* **Resolved**)
3. Look up the fingerprint in the register:
   - Accepted **and** `review_by` in the future → status `accepted` (visible, not alarming)
   - Accepted **but** `review_by` has passed → status `expired-acceptance` (re-surfaces as risk — this is the mechanism that stops sanctioned debt from becoming forgotten debt)
   - Not in the register → status `unreviewed` (the actual signal compliance cares about)

A New finding that's `unreviewed` is the headline risk. An Existing finding that's `expired-acceptance` is just as important — it's "we said we'd deal with this by March, it's now April."

## Testing approach

Unit tests for the diff logic (baseline.py) and register expiry logic (register.py) specifically — these are the parts with real edge cases (fingerprint collisions, boundary dates) and the parts a hiring manager skimming the repo would actually check for correctness. Scanner detection accuracy stays verified by the sample app rather than exhaustive unit tests, since regex-based detection's limits are already documented as a known tradeoff, not something to over-engineer tests around.

## Build order

1. `signatures.py` + `scanner.py` — mostly a port of what was already built and verified during PRD iteration
2. `baseline.py` — save/load + diff
3. `register.py` — accept + expiry check
4. `report.py` — merge logic + dashboard rendering
5. `cli.py` — wire the three subcommands
6. `examples/sample_app/` — demo data, generate and commit `dashboard.html`
7. Tests for 2 and 3

---

*Approved. Build proceeds in the order above.*

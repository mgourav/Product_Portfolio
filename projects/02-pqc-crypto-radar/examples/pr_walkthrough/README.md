# PR walkthrough — four scenarios, one evolving repo

A runnable demo of how Crypto Radar behaves across a realistic sequence of
pull requests, not just a one-off directory of planted findings
(`examples/sample_app/` is that; this is the "watch it work over time" demo
the PRD's "continuous, not static" positioning is actually about).

One file, `src/payments_service.py`, evolves PR by PR. Each scenario below
is a snapshot of that file plus the exact `pqc-radar` commands run against
it and their real output — copy-pasted from an actual run, not written by
hand. Reproduce it yourself:

```bash
cd projects/02-pqc-crypto-radar
bash examples/pr_walkthrough/run_walkthrough.sh
```

It's self-contained (scratch state lives in `.work/`, wiped and rebuilt
each run) and takes under a second — no network, no dependencies.

---

## Setup — establish `main`'s baseline

Before any PR, `main` has one function: a SHA-256 checksum. First scan ever
run has no baseline to compare against, so everything shows as "new" —
that's expected, and it's the moment you'd run `--save-baseline` to give
the tool a starting point.

```
Total findings:        1
New since baseline:    1
Unreviewed:            1
```

---

## Scenario 1 — PR introduces a quantum-vulnerable algorithm

The PR adds `generate_signing_key()`, which calls `rsa.generate_private_key(...)`
to sign outbound payment tokens. Scanning the branch *before* merging it —
the CI-gate moment — against `main`'s baseline:

```
Total findings:        2
New since baseline:    1   ← the RSA call
Existing:              1   ← the SHA-256 checksum, unchanged
Unreviewed:            2
```

The team decides RSA signing is acceptable for now (a planned migration will
replace it) and files it as a time-boxed exception rather than silently
shipping it:

```
$ pqc-radar accept <path> <RSA fingerprint> --ticket SEC-900 --review-by 2026-12-15
Accepted a28f3e538b59ee11 — ticket SEC-900, review by 2026-12-15
```

Re-running the same scan now shows the RSA finding as `accepted` instead of
`unreviewed` — nothing about the *code* changed, only the fact that someone
reviewed it and put a date on the exception:

```
Total findings:        2
New since baseline:    1
Unreviewed:            1   ← down from 2; RSA is accounted for, SHA-256 still isn't
```

The PR merges; this scan's `--save-baseline` moves `main` forward.

---

## Scenario 2 — PR introduces a PQC-ready algorithm, and nothing else

A second PR adds `derive_session_key()`, using a NIST-standardized
post-quantum key-encapsulation call for session encryption. No existing
code changes.

```
Total findings:        4
New since baseline:    2   ← the import line AND the call site both match
Existing:              2   ← SHA-256, RSA
Unreviewed:            3
```

Two things worth noticing, because they're easy to misread:

- **"New: 2" is one algorithm, not two.** The scanner is line-based: the
  `from pqc_crypto import ml_kem` import line and the
  `ml_kem.encapsulate(...)` call line both independently match the
  post-quantum signature, so one new import produces two findings. This is
  the documented regex tradeoff (ARCHITECTURE.md / README "favor catching
  real usage over avoiding false positives") working as intended, not a
  bug — but it means finding *counts* don't map 1:1 onto distinct
  algorithms, and a dashboard reader should look at `by_risk`, not raw
  counts, to answer "how many algorithms changed."
- **"Unreviewed: 3" includes the good news.** `register_status` is
  computed the same way for every finding regardless of risk level — a
  brand-new post-quantum call is just as "unreviewed" (= no register
  entry) as an unaddressed RSA call, because nobody has a reason to file a
  ticket accepting something that's already safe. The signal that this PR
  is net-positive isn't in `unreviewed_count`; it's in `by_risk`
  (`pqc-ready` goes up, nothing else does). This is a real product nuance,
  not a shortcut taken for the demo — see the `by_risk` breakdown in
  `final/report.json`.

This merges immediately — nothing here needs anyone's sign-off.

---

## Scenario 3 — PR introduces both an unsafe and a safe algorithm

A third PR does two things at once: adds `generate_legacy_partner_key()`
(a partner integration that still requires elliptic-curve signing) and
`sign_payment_receipt()` (a new, NIST-standardized post-quantum signature
call). Scanning the branch:

```
Total findings:        7
New since baseline:    4   ← ECC call, PQC-signature import + call, re-matched PQC-KEM import
Existing:              3
Resolved:              1
Unreviewed:            6
```

(`Resolved: 1` here is the `pqc_crypto` import line for the key-exchange
call changing shape slightly between branches — a reminder that the
"resolved" count tracks exact matched lines, not algorithms; see
ARCHITECTURE.md's note on fingerprint stability.)

The point of this scenario: **a single PR's net effect on risk isn't one
number.** This PR made things worse (a new quantum-vulnerable call) and
better (a new post-quantum call) in the same diff. A report that averaged
those into "net neutral" would hide the part that needs a decision. The
team accepts the elliptic-curve call as a time-boxed partner exception
(ticket SEC-905, same `accept` flow as Scenario 1) and merges.

---

## Cleanup PR — closing the loop before Scenario 4

Between Scenario 3 and Scenario 4, a cleanup PR deletes
`generate_signing_key()` entirely — the RSA migration finally lands. The
RSA finding disappears:

```
Total findings:        6
Resolved:              1   ← RSA, gone
```

One thing this *doesn't* do: the register entry for SEC-900 (RSA, accepted
through 2026-12-15) stays in `register.json`. The register tracks
fingerprints, not "is this code still here" — an accepted finding that
disappears from the codebase just sits there, accepted, for code that no
longer exists. That's not cleaned up automatically, and it matters for
what happens next.

To show what happens once that review date has actually passed, without
waiting for the calendar, the walkthrough script hand-edits SEC-900's
`review_by` to a past date — the same technique `examples/sample_app`'s
committed register uses to simulate an expired acceptance.

---

## Scenario 4 — the same unsafe algorithm comes back in a revised PR

Months later (in the story), a different engineer — unaware RSA signing
was already litigated once — re-adds `generate_signing_key()` while
reworking token rotation. The re-added line is byte-for-byte the line from
Scenario 1, which matters: Crypto Radar's fingerprint is
`sha256(path + algorithm + matched line)`, not a line number, so the exact
same call produces the exact same fingerprint even after months and an
unrelated cleanup PR in between.

```
Total findings:        7
New since baseline:    1   ← RSA, back
Resolved:              0
Unreviewed:            5
Expired acceptances:   1   ← RSA
```

This is the scenario's actual test, and it passes two different ways at
once:

1. **It's flagged as `new`** — the cleanup PR had already removed RSA from
   the baseline, so its return is a fresh diff, not something quietly
   blended into "existing."
2. **It's flagged `expired-acceptance`, not `accepted`.** Because the old
   SEC-900 entry is still sitting in the register under the same
   fingerprint, a less careful design could have let this silently
   inherit the old sign-off and show up as calmly `accepted` — exactly the
   "static one-time discovery" failure mode this tool exists to avoid. It
   doesn't, *because* the review date had already passed by the time this
   happened. (Worth being honest about the edge this doesn't fully close:
   if the same code had come back **before** SEC-900's review date, it
   would have inherited the old acceptance with no new human decision —
   the register expires by date, not by "has this code been continuously
   present." That's a real, documented limitation, not a hidden one.)

`final/report.json` and `final/dashboard.html` are this scenario's output,
committed so you can open the dashboard without running anything.

---

## What this demo is and isn't

This walks through the scanner's actual diff/register/fingerprint logic
against hand-written (not generated) code, and every number above is
copied from a real run, not predicted. It's small on purpose — one file,
one language, a handful of lines — specifically so every finding's cause
is traceable by eye. The "regex matches comments and import lines too, not
just real call sites" behavior surfaced while building this demo and is
called out above rather than edited away, in the same spirit as the main
project's QA pass: a limitation documented is more useful to a reader than
one quietly avoided.

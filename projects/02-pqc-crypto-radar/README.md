
# PRD: Crypto Radar — Continuous Cryptographic Inventory for PQC Readiness

| | |
|---|---|
| **Author** | Gourav Mehta, Product Manager |
| **Status** | ✅ **Phase 1 (R1–R5, single-repo) shipped, QA'd, and closed.** Phase 2 (multi-repo rollup, R6) is scoped below but was **deliberately not started** — see [Competitive Landscape](#competitive-landscape-why-phase-2-stopped-here) below. |
| **Last updated** | Nov 2026 |
| **Related work** | Driving PQC and FIPS 140-3 transitions on Trellix's Data Security portfolio (see [root README](../../README.md)) — this project generalizes that problem outside any one company's codebase |

## TL;DR

Enterprises are being pushed toward PQC migration by customer security questionnaires and NIST's own deprecation timeline for RSA/ECC — not by a single dramatic event. Every migration playbook starts with "discover your cryptographic inventory," but that discovery is almost always a one-time audit, and an inventory that's accurate today is stale the moment the next pull request merges. **Crypto Radar treats cryptographic inventory as a continuously-tracked artifact — scanned on demand, diffed against a baseline, with a compliance-ready dashboard — instead of a point-in-time report**, so a compliance officer can show continuous evidence of PQC posture instead of a report that was only ever true on the day it ran.

## Problem Statement

Cryptography has followed a "discover once, fix, move on" lifecycle — an audit finds weak algorithms, you patch them, you're done until the next audit. Two things break that model for the post-quantum transition:

1. **Migration is a multi-year program, not a patch.** NIST finalized its PQC standards (ML-KEM, ML-DSA, SLH-DSA) in August 2024, and has already signaled a deprecation timeline for 112-bit-security algorithms like 2048-bit RSA (disallowed in NIST's guidance by the early 2030s). That's a long enough window that *new* non-compliant cryptography gets written faster than periodic audits catch it.
2. **"Harvest now, decrypt later" makes drift itself the risk.** Data encrypted today with RSA or ECC can be captured now and decrypted later once a cryptographically relevant quantum computer exists. The dangerous moment isn't "we still have old crypto somewhere" — it's "someone added a new RSA call last week, and nobody will know until next year's audit."

**The specific failure mode this solves:** a point-in-time crypto inventory goes stale the moment the next pull request merges, and there's no standing evidence trail showing posture is actually improving.

## Why Now

- **Customer security questionnaires and RFPs are already asking for a PQC roadmap** — procurement cycles are the forcing function for non-federal enterprises right now, not a future mandate
- **NIST's own deprecation timeline is concrete** — 2048-bit RSA and comparable-strength algorithms are flagged for disallowance in the early 2030s; that's a real date compliance teams are being asked to plan against today
- Existing tooling (CBOM generators, SAST crypto rules) produces inventories, not continuously-tracked evidence — there's a real gap between "we know our crypto debt" and "we can prove our crypto debt is shrinking"

## Users

| Persona | Role | Need |
|---|---|---|
| **Compliance / Head of Compliance** (primary) | Owns proving PQC posture to auditors, regulators, and customer-security questionnaires | A standing, audit-ready artifact showing posture over time and a register of known/accepted risk — not a one-time PDF |
| **DevOps / platform engineer** | Implements and operates the tool | A scanner that's trivial to run without standing up new infrastructure |
| **Developer** | Writes the code the scanner looks at | Clear, specific findings (file/line, why it's flagged) — not vague "fix your crypto" noise |

*Why compliance officer over DevOps as primary:* DevOps can run a tool, but they're not the one accountable for answering "are we PQC compliant, and can you prove it" to an auditor or a customer's security team. That accountability is what makes this worth building at all — a tool nobody is accountable for using doesn't get used.

## Goals (Success Metrics)

*For this as a working portfolio project — not a funded product — "success" means:*

- **G1:** Correctly detects common cryptographic API usage (RSA, ECC, AES, SHA family, PQC algorithms) across a mixed-language sample codebase, with risk classification and file/line reference
- **G2:** A compliance officer could open the generated dashboard and answer "what's our exposure, what's accepted risk with a review date, and is it trending down" without reading code
- **G3:** The exception/risk-register mechanism distinguishes *known, sanctioned, time-boxed* risk (e.g., RSA code that's part of an active hybrid PQC migration) from *new, unreviewed* risk — rather than crying wolf on legitimate migration work
- **G4 (Phase 2):** Multi-repo rollup works without any backend, database, or hosted service — a compliance officer gets one dashboard from N repos' reports, not N separate reports to reconcile by hand

## Non-Goals (v1)

- **Not** a hosted, multi-user SaaS dashboard with login/auth/roles — the dashboard is a static, locally-generated artifact (see Positioning)
- **Not** automatic CI/CD triggering — v1 is a manually-run CLI; GitHub Actions integration (auto-scan every PR) is the explicit fast-follow, not v1 (see Scope)
- **Not** a replacement for a full cryptographic risk assessment (key sizes, protocol context, usage mode)
- **Not** claiming production-grade detection accuracy — regex-based matching has real false-positive/negative rates, stated plainly rather than hidden
- **Not** solving true real-time/runtime crypto observability (detecting what's executing in production) — this is static source-code scanning, triggered on demand

## Positioning

**Standalone tool, built for enterprises to run against their own repos** — not a feature bolted onto an existing SAST/SCA platform, and not a hosted service. "Dashboard" means a self-contained HTML file generated from scan data, opened locally or published as a static page (e.g., GitHub Pages) — not a server with a database behind it. This keeps v1 buildable without infrastructure while still giving the primary persona something dashboard-shaped rather than a raw JSON dump.

## Solution Overview

Treat the crypto inventory **as code, not as a report** — versioned, diffed, and rolled up without a backend:

1. **Scan** (manual CLI run) — walk a codebase for cryptographic algorithm usage; classify each finding as `quantum-vulnerable` (RSA, ECC, DH, DSA — broken by Shor's algorithm), `quantum-safe-today` (AES-256, SHA-256/384/512 — only quadratically weakened by Grover's), or `pqc-ready` (ML-KEM/Kyber, ML-DSA/Dilithium, SLH-DSA/SPHINCS+)
2. **Baseline + diff** — commit the inventory as a file alongside the code; each subsequent scan diffs against it into New / Existing / Resolved, so the signal stays "what changed," not "here's everything, again"
3. **Risk register** (resolves the hybrid-migration problem) — a team can mark a finding `accepted: migration-in-progress` with a ticket reference and a review-by date. Accepted findings don't read as new risk, but they're visible in the dashboard and re-surface once the review date passes — so sanctioned debt can't silently become forgotten debt. This register **is** the compliance officer's audit trail, not just a false-positive workaround.
4. **Dashboard** — a static HTML report generated from one or more scan outputs: summary counts by risk category, the risk register with review dates, and (once more than one historical scan exists) a trend view
5. **Multi-repo rollup** *(Phase 2 — not in the current build gate)* — the dashboard generator can take JSON reports from several repos and merge them into one view, with no server or database — someone collects the JSON files (manually, or via a script) and points the generator at the folder. Phase 1 proves the single-repo flow end to end first; rollup is a straightforward extension of the same JSON format once that's working, not a redesign.

## Scope

| | **Phase 1 (approved, building now)** | Phase 2 (scoped, separate approval) | Fast-follow beyond that | Explicitly out |
|---|---|---|---|---|
| **Trigger** | Manual CLI run, single repo | — | GitHub Actions example (auto-scan every PR) | Runtime/production crypto observability |
| **Source** | Source-code scan (pattern-based), 4–5 languages | — | Dependency manifest / SBOM parsing | Binary, TLS/network, HSM scanning |
| **Detection** | Regex/signature-based | — | AST-based parsing for accuracy | ML-based detection |
| **Output** | JSON report + static HTML dashboard | — | Automated historical trend storage | Hosted, multi-user SaaS |
| **Continuity** | Git-diffable baseline file | — | CI-triggered diff-and-fail | — |
| **Risk handling** | Risk register (accept + review-by date) | — | Automated review-date reminders (e.g., email) | — |
| **Scale** | Single repo only | Multi-repo rollup via local JSON aggregation (R6) | Scripted/scheduled collection across repos | Centralized hosted aggregation service |

## Requirements

**Phase 1 — approved, building now:**

| ID | Requirement | Priority |
|---|---|---|
| R1 | Detect RSA/ECC/DH/DSA, AES, SHA-family, and PQC algorithm usage in source files across common languages | P0 |
| R2 | Classify each finding by risk category with file + line reference | P0 |
| R3 | Save/load a baseline file; diff current scan against it into New / Existing / Resolved | P0 |
| R4 | Risk register: mark a finding `accepted` with ticket + review-by date; re-surface it once that date passes | P0 |
| R5 | JSON report (machine-readable) + static HTML dashboard (summary, register, findings) generated from one or more scans, single repo | P0 |
| R7 | Sample mixed-language demo data, including at least one deliberately-accepted finding, for the dashboard to run against | P1 |

**Phase 2 — scoped, requires separate approval before building:**

| ID | Requirement | Priority |
|---|---|---|
| R6 | Multi-repo rollup: generate one dashboard from N repos' JSON reports | P0 (Phase 2) |

**Fast-follow, beyond Phase 2:**

| ID | Requirement | Priority |
|---|---|---|
| R8 | Example GitHub Actions workflow demonstrating CI-triggered scanning | P2 |
| R9 | Dependency-manifest parsing (requirements.txt, package.json) | P2 |

## Risks & Mitigations

| Risk | Mitigation for v1 |
|---|---|
| Regex detection produces false positives/negatives vs. AST parsing | State the limitation explicitly in docs; this is a concept demo, not a production scanner |
| "Vulnerable vs. safe" is a simplification — real urgency depends on key size, mode, and context (signing vs. key exchange) | Note it as a known simplification rather than silently overclaiming precision |
| Multi-repo rollup with no backend means someone still has to collect the JSON files from each repo | Acceptable for v1 — explicitly named as manual in Scope; automated collection is a fast-follow, not hidden as if it's solved |
| A static dashboard can't show a trend without multiple historical scans being kept somewhere | v1 shows a trend only when the user points it at more than one timestamped report; automatic historical storage is a fast-follow |

## Milestones

- [x] Problem framed, personas and forcing functions pressure-tested, scope agreed
- [x] **PRD approved for Phase 1** (single-repo scan → baseline/diff → risk register → dashboard)
- [x] Solution architecture plan for Phase 1 ([`ARCHITECTURE.md`](ARCHITECTURE.md)) — approved
- [x] Core scanner + signature set (R1–R2) — `pqc_radar/scanner.py`, `pqc_radar/signatures.py`
- [x] Baseline + diff + risk register (R3–R4) — `pqc_radar/baseline.py`, `pqc_radar/register.py`, with unit tests for both
- [x] Report + dashboard generation (R5) — `pqc_radar/report.py`
- [x] Sample demo data (R7) — [`examples/sample_app/`](examples/sample_app), including a pre-generated [`dashboard.html`](examples/sample_app/dashboard.html) you can open directly
- [x] **PR walkthrough** — [`examples/pr_walkthrough/`](examples/pr_walkthrough), four runnable scenarios (unsafe-only, safe-only, both-at-once, regression) across one evolving file, output captured from real runs
- [x] **QA pass** — 8 bugs/usability issues found and fixed (see below); 19 unit tests, all passing
- [x] **Competitive landscape research before Phase 2** — decision: don't build R6, see below
- [ ] ~~Phase 2 approval gate — multi-repo rollup (R6)~~ — deliberately not pursued
- [ ] ~~Fast-follows beyond Phase 2: CI example (R8), dependency parsing (R9)~~ — superseded by the landscape finding

## Try it

```bash
cd projects/02-pqc-crypto-radar
python3 -m unittest discover -s tests          # 19 tests: baseline diff, register expiry, path validation
python3 -m pqc_radar scan examples/sample_app --repo-name sample-app --out report.json
python3 -m pqc_radar dashboard report.json --out dashboard.html
```

Or just open the already-generated [`examples/sample_app/dashboard.html`](examples/sample_app/dashboard.html) — no setup required. It shows a realistic mixed state: 3 new unreviewed findings (simulating code added this sprint), one finding accepted as part of an active migration (ticket SEC-451, review-by 2027), and one accepted finding whose review date has already passed (ticket SEC-200) — which is exactly the "sanctioned debt becoming forgotten debt" scenario the risk register exists to catch.

**Want to see it react to a sequence of PRs instead of one static snapshot?** [`examples/pr_walkthrough/`](examples/pr_walkthrough) runs four scenarios against one evolving file — an unsafe-only PR, a safe-only PR, a PR with both at once, and a regression where the same unsafe call comes back months later under a different engineer. Run `bash examples/pr_walkthrough/run_walkthrough.sh` or just read the walkthrough's README, which has every command and its real output already captured.

## QA pass

Before moving to Phase 2, the Phase 1 build was tested deliberately looking for ways to break it, not just re-reading the code. Eight issues found and fixed, two of them real correctness bugs rather than polish:

| Severity | Issue | Fix |
|---|---|---|
| Critical | Scanning a mistyped/nonexistent path silently returned "0 findings, exit 0" — indistinguishable from a genuine clean scan. The worst failure mode a compliance tool can have. | `scan_path` now raises `FileNotFoundError`/`NotADirectoryError`; the CLI reports it cleanly and exits non-zero. |
| High | The baseline diff collapsed findings into a `{fingerprint: Finding}` dict before classifying, silently dropping duplicate occurrences. If the same risky line was copy-pasted into 3 new places, the dashboard table correctly showed 3 new rows but the headline said "1 new finding." | `diff()` now classifies every occurrence by iterating the full lists, using fingerprints only for identity — not for deduplication. Regression tests added. |
| High | Several Java/Python AES signatures required the key-size call on the *same line* as `getInstance`/`new` (e.g. `KeyGenerator.getInstance("AES")` + `.init(128)`). Splitting them across two lines — extremely common real-world style — produced zero detections. | Added fallback signatures (with negative lookahead to avoid double-firing) that flag these as "key size unknown" instead of missing them entirely. |
| Medium | `scan` derives the register/baseline location from the repo path; `accept` required typing the full `--register` file path by hand — same tool, two inconsistent mental models. | `accept` now takes the repo path the same way `scan` does, defaulting the register location from it. |
| Medium | Missing/corrupt report or baseline files surfaced as raw Python tracebacks. | Top-level error handling in the CLI prints a clean message and exits 1. |
| Low | SVG charts drew a visible minimum-width bar even for zero-count categories, and hid a category entirely if it had zero findings — both misleading and inconsistent between scans. | Zero-count categories now always show as a labeled row with no bar; chart row order is fixed instead of scan-dependent. |
| Low | `accept <fingerprint>` gave no feedback on a typo'd fingerprint — it would silently create a register entry that matches nothing. | Soft warning (not a hard failure, since a brand-new finding is legitimately not yet baselined) when the fingerprint isn't found in the repo's baseline. |

All fixes verified with reproductions before and after, and covered by the test suite (19 tests, up from 14).

## Competitive landscape — why Phase 2 stopped here

Before scoping Phase 2 (multi-repo rollup, R6) any further, I researched what already exists in this space rather than assuming the gap this PRD's "Why Now" section described was still open. It isn't, and the finding changes the plan:

- **The detection approach Phase 1 uses (regex) is already outclassed by open-source tools.** [CBOMkit-hyperion](https://github.com/PQCA/sonar-cryptography) (the Sonar Cryptography Plugin, originally built by IBM Research and donated to the Linux Foundation's Post-Quantum Cryptography Alliance) does AST-based detection with type resolution across Java, Python, and Go, claiming 100% coverage of libraries like `pyca/cryptography`. GitHub's CodeQL ships high-precision, dataflow-based crypto queries (`py/weak-cryptographic-algorithm`, Java's RSA-without-OAEP check, Go's `weak-crypto-algorithm`) out of the box. A 2025 paper (*Cryptoscope*, arXiv:2503.19531) makes the direct case that regex-based detection becomes unreliable once a codebase interleaves multiple crypto types — the exact tradeoff this project's `signatures.py` documents and accepts.
- **The CI-gate and CBOM-output pieces (R5, R8) already exist as finished open-source tools**, not just concepts: `cbomkit-action` is a GitHub Action that runs on PRs and emits CycloneDX CBOMs per module; CBOMkit itself ships a full web viewer, a database, and an OPA/Rego-based compliance policy engine.
- **The multi-repo rollup idea (R6) is already being built and monetized.** [Keylens](https://github.com/keylens/cbom) is explicit that its open-source CLI is "built for single-repo developer use" with a stated commercial boundary for the multi-repo/enterprise case — i.e., the exact Phase 2 I scoped is already someone else's roadmap and business model.
- **The "continuous, not static" framing this PRD's problem statement leans on also has real prior art** — [DynamicCBOM](https://github.com/SEG-UNIBE/DynamicCBOM) extracts a CBOM at runtime via eBPF with no code changes, and SafeLogic's commercial CPM product correlates CI/CD, runtime, and SIEM data into one continuously-updating cryptographic inventory.
- **One piece genuinely doesn't appear bundled anywhere I found**: a finding-level, ticket-tracked risk acceptance that automatically re-surfaces once its review date lapses (this project's register, R4). That pattern is standard general GRC/SBOM exception-management practice, but I didn't find it wired into any crypto/CBOM-specific tool — CBOMkit's compliance layer checks policy compliance per-component, not "we already decided about *this specific finding*, and that decision expires."

**Decision:** rather than build Phase 2 (R6, multi-repo rollup) on top of a detection engine that's already behind the open-source state of the art, I'm stopping here. Continuing to extend the home-grown regex scanner would mean re-deriving — with less rigor — what CBOMkit-hyperion and CodeQL already do with AST and dataflow analysis, maintained by IBM Research/Linux Foundation and GitHub respectively. That's not a good use of further build time on a project whose actual point is demonstrating product judgment, including the judgment to recognize when the right move is *not* building more.

If I were taking this from portfolio project to something real, the honest next step isn't R6 — it's rebuilding on top of an existing detection engine (CodeQL or `cbomkit-lib`'s programmatic API) and keeping only the register/expiry/audit-trail layer as the actual differentiated piece, since that's the one gap the research didn't turn up a ready-made answer for.

---

*Phase 1 is built, QA'd, and verified against the sample app and the PR walkthrough. Phase 2 was researched and deliberately not pursued — see above.*

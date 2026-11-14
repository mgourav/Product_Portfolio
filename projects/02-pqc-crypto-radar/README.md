
# PRD: Crypto Radar — Continuous Cryptographic Inventory for PQC Readiness

| | |
|---|---|
| **Author** | Gourav Mehta, Product Manager |
| **Status** | ✅ **Approved — Phase 1 (R1–R5, single-repo).** Phase 2 (multi-repo rollup, R6) is scoped below but requires a separate approval once Phase 1 ships. |
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
- [ ] **Phase 2 approval gate** — multi-repo rollup (R6) scoped above, not started
- [ ] Fast-follows beyond Phase 2: CI example (R8), dependency parsing (R9)

## Try it

```bash
cd projects/02-pqc-crypto-radar
python3 -m unittest discover -s tests          # 14 tests, baseline diff + register expiry logic
python3 -m pqc_radar scan examples/sample_app --repo-name sample-app --out report.json
python3 -m pqc_radar dashboard report.json --out dashboard.html
```

Or just open the already-generated [`examples/sample_app/dashboard.html`](examples/sample_app/dashboard.html) — no setup required. It shows a realistic mixed state: 3 new unreviewed findings (simulating code added this sprint), one finding accepted as part of an active migration (ticket SEC-451, review-by 2027), and one accepted finding whose review date has already passed (ticket SEC-200) — which is exactly the "sanctioned debt becoming forgotten debt" scenario the risk register exists to catch.

---

*Phase 1 is built and verified against the sample app. Phase 2 (multi-repo rollup) is scoped above but requires a separate approval before any code.*

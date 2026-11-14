
# PRD: Crypto Radar — Continuous Cryptographic Inventory for PQC Readiness

| | |
|---|---|
| **Author** | Gourav Mehta, Product Manager |
| **Status** | 🚧 Build in progress — this doc is the plan; code follows below it |
| **Last updated** | Nov 2026 |
| **Related work** | Driving PQC and FIPS 140-3 transitions on Trellix's Data Security portfolio (see [root README](../../README.md)) — this project generalizes that problem outside any one company's codebase |

## TL;DR

Enterprises are being forced to migrate off RSA/ECC before quantum computers can break them. Every migration playbook starts the same way: "first, discover your cryptographic inventory." The problem is that discovery is treated as a one-time audit — and an inventory that's accurate on the day it's run is already stale the day after, because engineering doesn't stop shipping. **Crypto Radar treats crypto inventory as a continuously-checked artifact, like a dependency lockfile, instead of a point-in-time report.** It scans code, classifies algorithms by quantum risk, commits a baseline, and fails a PR when someone introduces new quantum-vulnerable crypto — catching drift at the moment it's created, not at next year's audit.

## Problem Statement

Cryptography has always followed a "discover once, fix, move on" lifecycle — an audit finds weak algorithms, you patch them, you're done until the next audit. Two things break that model for the post-quantum transition:

1. **Migration is a multi-year program, not a patch.** NIST finalized its PQC standards (ML-KEM, ML-DSA, SLH-DSA) in August 2024; the NSA's CNSA 2.0 mandate gives federal systems until 2030–2033 to comply. That window is long enough that *new* non-compliant cryptography gets written faster than periodic audits can catch it.
2. **"Harvest now, decrypt later" makes drift itself the risk.** Data encrypted today with RSA or ECC can be captured now and decrypted later once a cryptographically relevant quantum computer exists. The dangerous moment isn't "we still have old crypto somewhere" — it's "a developer added a new RSA call last Tuesday, and nobody will know until the next scheduled audit."

**The specific failure mode this solves:** a point-in-time crypto inventory goes stale the moment the next pull request merges.

## Why Now

- NIST's PQC algorithms are finalized — there's a concrete target to migrate *to*, not just a vague future requirement
- Regulated industries (finance, healthcare, gov/defense supply chain) are already receiving compliance timelines from customers and regulators
- Existing tooling (CBOM generators, SAST crypto rules) produces inventories, not continuous guardrails — there's a real gap between "we know our crypto debt" and "we catch new crypto debt before it ships"

## Users

| Persona | Need |
|---|---|
| **Security/compliance engineer** (primary) | Needs to prove crypto posture is improving over time, not just know what it looked like at last audit |
| **Engineering team** (secondary) | Wants an automated check, not a manual audit ticket, when they touch anything crypto-adjacent |
| **Engineering leadership** | Wants a trend line for a board/compliance deck, not a one-time PDF |

## Goals (Success Metrics)

*For this as a working portfolio project — not a funded product — "success" means:*

- **G1:** Correctly detects common cryptographic API usage (RSA, ECC, AES, SHA family) across a mixed-language sample codebase with low false-negative rate on canonical patterns
- **G2:** Diff output clearly separates **new** quantum-vulnerable usage (should block a PR) from **existing** accepted debt (tracked, not re-flagged every run)
- **G3:** CI integration is one copy-pasted YAML file away — no bespoke setup
- **G4:** The README makes the "continuous vs. one-time" argument clearly enough that a security engineer would recognize the problem, not just the tool

## Non-Goals (v1)

- Not a replacement for a full cryptographic risk assessment (key sizes, protocol context, usage mode)
- Not claiming production-grade detection accuracy — regex-based matching has real false positive/negative rates; this is explicit, not hidden
- Not solving enterprise-scale concerns: multi-repo aggregation, dashboards, RBAC, suppression workflows

## Positioning

**Standalone tool, built for enterprises to integrate into their own pipelines** — not a feature bolted onto an existing SAST/SCA platform. The reasoning: a team evaluating PQC readiness shouldn't need to adopt a whole new security platform to get a continuous crypto-drift check; a CLI that drops into any CI pipeline in one config file has a much shorter path from "interesting" to "running on every PR." That also keeps the tool platform-agnostic — it doesn't compete with or depend on whatever SAST/SCA tooling an enterprise already has.

## Solution Overview

Treat the crypto inventory **as code, not as a report** — versioned and diffed like a lockfile:

1. **Scan** — walk a codebase (and, as a fast-follow, dependency manifests) for cryptographic algorithm usage
2. **Classify** — tag each finding by quantum-migration risk: `quantum-vulnerable` (RSA, ECC, DH, DSA — broken by Shor's algorithm), `quantum-safe-today` (AES-256, SHA-256/384/512 — only quadratically weakened by Grover's, still safe at these key sizes), `pqc-ready` (ML-KEM/Kyber, ML-DSA/Dilithium, SLH-DSA/SPHINCS+)
3. **Baseline** — commit the inventory as a file alongside the code, the way a lockfile travels with a manifest
4. **Diff on every PR** — flag *new* quantum-vulnerable usage before merge; leave existing, already-known debt alone so the signal stays actionable instead of noisy
5. **Trend, don't snapshot** — because every run is diffed against the last, the inventory becomes a time series a team can actually report against

## Scope

| | MVP (building now) | Fast-follow | Explicitly out |
|---|---|---|---|
| **Source** | Source-code scan (pattern-based), 4–5 languages | Dependency manifest / SBOM parsing | Binary, TLS/network, HSM scanning |
| **Detection** | Regex/signature-based | AST-based parsing for accuracy | ML-based detection |
| **Output** | CLI → Markdown + JSON report | — | Hosted dashboard |
| **Continuity** | Git-diffable baseline file + CI gate example | Historical trend chart from stored baselines | Multi-repo aggregation |
| **Workflow** | — | Suppression/accept-risk workflow | RBAC, SSO, enterprise auth |

## Requirements (MVP)

| ID | Requirement | Priority |
|---|---|---|
| R1 | Detect RSA/ECC/DH/DSA, AES, SHA-family, and PQC algorithm usage in source files across common languages | P0 |
| R2 | Classify each finding by risk category with file + line reference | P0 |
| R3 | Save/load a baseline file; diff current scan against it into New / Existing / Resolved | P0 |
| R4 | CLI exits non-zero when new quantum-vulnerable findings exist (CI-gateable) | P0 |
| R5 | Human-readable Markdown report + machine-readable JSON output | P0 |
| R6 | Example GitHub Actions workflow demonstrating PR-gating usage | P1 |
| R7 | Sample mixed-language demo app with deliberately planted findings, for the report to run against | P1 |
| R8 | Dependency-manifest parsing (requirements.txt, package.json) | P2 — fast-follow |

## Risks & Open Questions

| Risk | Mitigation for v1 |
|---|---|
| Regex detection produces false positives/negatives vs. AST parsing | State the limitation explicitly in docs; this is a concept demo, not a production scanner |
| "Vulnerable vs. safe" is a simplification — real urgency depends on key size, mode, and context (signing vs. key exchange) | Note it as a known simplification rather than silently overclaiming precision |

## Milestones

- [x] Problem framed, scope agreed (this document)
- [x] Core scanner + signature set (R1–R2) — `pqc_radar/scanner.py`, `pqc_radar/signatures.py`
- [ ] Baseline + diff logic (R3–R4)
- [ ] Report output (R5)
- [ ] Sample app + CI example (R6–R7)
- [ ] Dependency parsing fast-follow (R8)

---

*Build log and code live in this directory as they ship. This PRD is the plan — the commits below it are the execution.*

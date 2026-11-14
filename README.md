# Gourav Mehta — Product Manager, Security & Identity

Senior Product Manager at Trellix, owning the combined Database Security and Encryption portfolio (~$50M ARR across 250+ enterprise customers). 8+ years across engineering and product, with 4+ years leading enterprise security and fintech platforms — growing from Product Analyst to Senior Product Manager in under four years. Now extending that security/identity foundation into Agentic AI and Non-Human Identity (NHI) governance.

This repo is where I ship small, real projects instead of talking about product sense in the abstract — each one picks a problem in security/identity tooling, ships a working artifact, and documents the thinking behind it.

## What I work on

- **Database security & encryption** — CVE governance, virtual patching, and compliance posture across Oracle, MongoDB, MSSQL, and PostgreSQL
- **Cryptographic & compliance transitions** — currently driving Trellix's Post-Quantum Cryptography (PQC) transition across its Data Security line (~$90M ARR) and the FIPS 140-3 transition across the encryption portfolio
- **Identity & access** — IAM/OAuth 2.0/OIDC systems, RBAC, token lifecycle, and (now) Non-Human Identity governance for agentic AI systems
- **AI-assisted product tooling** — shipped a production LangChain support bot; using Claude Code in my own PM workflow

## Experience

**Trellix** — *Senior Product Manager*, Jul 2026–present
Owns the combined Database Security and Encryption portfolio (~$50M ARR: $40M encryption, $10M database security; 250+ enterprise customers). Promoted from Product Manager 2 after driving product-strategy impact on Database Security. Currently:
- Driving the Post-Quantum Cryptography (PQC) transition across Trellix's full Data Security line (DLP, Database Security, Data Encryption — ~$90M ARR), concentrated on the core encryption products ahead of post-quantum compliance requirements
- Leading the FIPS 140-3 transition across the data encryption portfolio, protecting $15M in at-risk federal customer ARR
- Championing the SaaS transformation of the File and Removable Media Protection product ($2M ARR, 7 enterprise customers)
- Ran structured discovery across Support, Sales, Account Management, and Engineering, synthesizing ICP/anti-ICP profiles and a SWOT analysis that shaped a 2027+ roadmap presented to Trellix leadership

**Trellix** — *Product Manager 2*, Feb 2025–Jun 2026
- Defined strategy to support 200+ cloud-native databases, sizing an $18M revenue opportunity over 2 years
- Turned around an at-risk relationship with Rimini Street (an Oracle-focused MSP), recovering and growing Database Security ARR from $7M to $10M
- Built and shipped an AI-powered LangChain support bot resolving 200+ database-security queries/month (~50 hours/month of manual effort recovered)
- Introduced a standing 10%-of-engineering-bandwidth tech-debt mandate, cutting supportability gaps 36.5% and P1/P2 critical defects 52%
- Integrated 195 CVEs into vulnerability scans and delivered 9 virtual patches covering 24 CVEs across Oracle, MongoDB, MSSQL, and PostgreSQL
- Enabled AWS RDS support (winning ~$2M in closed RFP business, 5× query throughput) and added IPv6 support for federal compliance

**Open Financial Technologies** — *Product Manager*, Nov 2024–Jan 2025
AI-native neobanking platform for Indian businesses; owned SME payments and onboarding (16k+ SMEs). Identified a 96% KYC drop-off rate and led onboarding-streamlining initiatives targeting a 50% reduction; grew payouts ARR by ₹15 lakhs via pricing redesign; lifted payment-gateway adoption 20%.

**Zeta Suite** — *Associate Product Manager*, Jan 2023–May 2024 → *Product Analyst*, Nov 2021–Jan 2023
Cloud-native banking infrastructure for card processing, core banking, and digital lending. Drove a 71% contact-rate reduction and 18-point CSAT increase for HDFC Bank's PayZapp 2.0 (4M MAU, ₹65 lakhs annual savings); led IAM API adoption (OAuth 2.0/OIDC, RBAC, token lifecycle) across 200+ platform integrations, cutting auth failures 40%; defined the product vision for a Key Management System; redesigned Zeta's developer documentation portal (17% adoption increase, 30% fewer support queries).

**Walkover** — *Product Management Intern*, Aug–Nov 2021
Early-stage developer-platform startup. Led filtering-API features for third-party developers; research with 50+ developer users cut integration time 30%.

**Amdocs** — *Associate Software Engineer*, Jun 2018–Aug 2020
Telecom/media software provider. Led a database migration cutting data-sync latency 10% for 1M+ daily transactions — moved from engineering into product from here, deliberately, validating the switch via the Walkover internship before committing.

## Education & Skills

BE in Computer Science, SGSITS, Indore (2014–2018).

**Product:** Strategy & roadmapping, prioritization, A/B testing, user research, cross-functional & executive stakeholder management
**Data & tools:** SQL, REST APIs, Postman, Mixpanel, Google Analytics, Jira, Confluence, Asana, Figma, Miro
**AI:** LangChain (production support bot), Claude Code
**Domain:** Cybersecurity & IAM, Cloud & Compliance (AWS RDS, IPv6, FIPS 140-3), Fintech (payments, KYC), Developer Platforms

## Projects

| Project | Problem | Status |
|---|---|---|
| [`projects/02-pqc-crypto-radar/`](projects/02-pqc-crypto-radar) — **Crypto Radar** | Crypto inventory is a one-time audit; PQC migration needs continuous drift detection. PRD + build for a CI-native scanner that flags new quantum-vulnerable crypto on every PR. | 🚧 Build in progress |
| [`projects/01-nhi-discovery-gap/`](projects/01-nhi-discovery-gap) | Mapping what identity governance tools can and can't see for AI agents (the "remediation trust gap") | 🚧 Problem framing |

See [`CHECKLIST.md`](CHECKLIST.md) for how this repo gets built out, and [`PROJECT_TEMPLATE.md`](PROJECT_TEMPLATE.md) for the format every project follows.

## Contact

- LinkedIn: [linkedin.com/in/gourav-mehta-pm](https://www.linkedin.com/in/gourav-mehta-pm/)
- Email: m.gourav0110@gmail.com
- Blog: [Trellix Database Security 10.3 — New Insights & Support Coverage](https://www.trellix.com/blogs/platform/trellix-database-security-10-3-new-insights-support-coverage/)
- Webinar: [Product webinar](https://www.youtube.com/watch?v=TyUdpKI5zME)

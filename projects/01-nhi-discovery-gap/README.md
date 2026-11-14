# NHI Discovery Gap Mapper

A framework (and eventually, a small tool) for mapping what identity-governance platforms can actually detect about AI agents vs. what they claim to, and where the resulting blind spots create risk.

**Status: problem framing in progress — not yet built.**

## Problem

Non-Human Identity (NHI) governance tools are built to discover and manage service accounts, API keys, and bots. AI agents break several of their core assumptions: agents spin up and down dynamically, act with delegated and often-changing permissions, and their "activity" is behavioral rather than a fixed set of API calls.

Most discovery engines are strong at one thing — finding unowned or orphaned credentials — and weak at three others:
- **Behavioral attribution**: distinguishing an agent acting on legitimate delegated authority from one that's been hijacked or is scope-creeping
- **Runtime activity visibility**: what the agent is actually doing right now, not just what credentials it holds
- **Decommissioning confirmation**: proof that an agent's access was actually revoked, not just flagged for review

I'm calling this the "remediation trust gap": the distance between a tool telling you *it found a problem* and you being able to trust that *the problem is actually fixed*.

## Solution (planned)

A short public write-up plus a lightweight scoring rubric that security/identity teams can use to evaluate NHI tooling against these four capabilities, rather than taking vendor marketing at face value. Longer-term: a small interactive tool where you input which controls you have and get back a gap map.

## Tradeoffs

- Starting with the write-up and rubric, not code — the hard part of this problem is the framework, and shipping that first lets me validate it before building anything
- Deliberately vendor-agnostic rather than naming specific products, since the point is a durable mental model, not a competitive comparison

## What I'm learning

To be filled in as this develops — this project is intentionally left visible mid-build rather than only showing finished work.

## Status

- [x] Problem framing drafted
- [ ] Shared with 2-3 people in identity/security for feedback
- [ ] Rubric v1 published
- [ ] Interactive tool shipped

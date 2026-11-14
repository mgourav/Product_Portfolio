"""
Risk register (PRD requirement R4).

This is the mechanism that resolves the hybrid-PQC-migration false-positive
problem: a team can mark a finding as a known, sanctioned, time-boxed risk
(e.g. "this RSA call is part of an active migration, tracked in JIRA-123,
review again by 2027-03-01") rather than the scanner treating every RSA
call as equally alarming forever.

It is also, deliberately, the compliance audit trail (PRD G3) — not a
separate feature. An accepted entry that has passed its review_by date
re-surfaces as risk on the next scan (status "expired-acceptance") rather
than silently staying accepted forever. That expiry is what makes this a
register instead of a permanent suppression list.
"""

import json
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from pathlib import Path


class RegisterStatus:
    ACCEPTED = "accepted"
    EXPIRED_ACCEPTANCE = "expired-acceptance"
    UNREVIEWED = "unreviewed"


@dataclass
class RegisterEntry:
    fingerprint: str
    ticket: str
    review_by: str       # ISO date string, e.g. "2027-03-01"
    reason: str = ""
    accepted_on: str = ""  # ISO datetime, set automatically when the entry is created

    def to_dict(self) -> dict:
        return asdict(self)


def load_register(path: str | Path) -> dict[str, RegisterEntry]:
    """Returns an empty register if none exists yet — nothing has been accepted."""
    path = Path(path)
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    return {fp: RegisterEntry(**entry) for fp, entry in data.get("entries", {}).items()}


def save_register(path: str | Path, entries: dict[str, RegisterEntry]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"entries": {fp: e.to_dict() for fp, e in entries.items()}}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def accept(
    register_path: str | Path,
    fingerprint: str,
    ticket: str,
    review_by: str,
    reason: str = "",
) -> RegisterEntry:
    """
    Adds or updates a register entry for `fingerprint`. This is what the
    CLI's `accept` subcommand calls. `review_by` must be an ISO date
    (YYYY-MM-DD) in the future — accepting something with a past review
    date would be a no-op (it'd show as expired immediately), so that's
    rejected outright rather than silently allowed.
    """
    review_date = date.fromisoformat(review_by)  # raises ValueError on bad format
    if review_date <= date.today():
        raise ValueError(
            f"review_by ({review_by}) must be in the future — "
            f"today is {date.today().isoformat()}"
        )

    entries = load_register(register_path)
    entries[fingerprint] = RegisterEntry(
        fingerprint=fingerprint,
        ticket=ticket,
        review_by=review_by,
        reason=reason,
        accepted_on=datetime.now(timezone.utc).isoformat(),
    )
    save_register(register_path, entries)
    return entries[fingerprint]


def status_for(fingerprint: str, register: dict[str, RegisterEntry]) -> str:
    """
    The core classification logic: is this fingerprint covered by a still-
    valid acceptance, has that acceptance expired, or was it never reviewed
    at all? report.py calls this for every finding (new and existing alike)
    to decide what actually gets surfaced as risk.
    """
    entry = register.get(fingerprint)
    if entry is None:
        return RegisterStatus.UNREVIEWED

    review_date = date.fromisoformat(entry.review_by)
    if review_date >= date.today():
        return RegisterStatus.ACCEPTED
    return RegisterStatus.EXPIRED_ACCEPTANCE

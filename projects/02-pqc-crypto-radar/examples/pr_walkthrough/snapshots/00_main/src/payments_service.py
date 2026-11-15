"""Payments service — token integrity helpers.

This is `main` before any of the walkthrough's PRs land. It's intentionally
small: one function, one hash check, nothing alarming.
"""

import hashlib


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()

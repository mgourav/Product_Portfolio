"""Payments service — token integrity helpers.

Scenario 1: a PR that introduces a quantum-vulnerable algorithm and
nothing else — the clean "this PR made things worse" case.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric import rsa


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()


def generate_signing_key():
    """New in this PR: a keypair for signing outbound payment tokens."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)

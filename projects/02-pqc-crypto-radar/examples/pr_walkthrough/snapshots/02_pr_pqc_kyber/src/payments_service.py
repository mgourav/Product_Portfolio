"""Payments service — token integrity + session key exchange.

Scenario 2: a PR that introduces a NIST-standardized post-quantum
key-encapsulation call and nothing else — the "this PR made things
better" case. Branched from main after PR #1 (RSA signing) was merged.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric import rsa
from pqc_crypto import ml_kem  # placeholder import for a post-quantum KEM library


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()


def generate_signing_key():
    """A keypair for signing outbound payment tokens."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def derive_session_key(peer_public_key: bytes) -> bytes:
    """New in this PR: post-quantum key exchange for session encryption."""
    return ml_kem.encapsulate(peer_public_key)

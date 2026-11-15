"""Payments service — token integrity, session key exchange, partner
signing, and receipt signing.

Scenario 3: a PR that introduces BOTH a quantum-vulnerable algorithm
(a legacy partner integration still requires elliptic-curve signing)
and a post-quantum algorithm (a new receipt-signing feature uses a
NIST-standardized post-quantum signature scheme) in the same change.
Branched from main after PR #2 (post-quantum key exchange) was merged.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from pqc_crypto import ml_dsa, ml_kem  # placeholder imports for post-quantum libraries


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()


def generate_signing_key():
    """A keypair for signing outbound payment tokens."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def derive_session_key(peer_public_key: bytes) -> bytes:
    """Post-quantum key exchange for session encryption."""
    return ml_kem.encapsulate(peer_public_key)


def generate_legacy_partner_key():
    """New in this PR: one partner's integration still requires
    elliptic-curve signing — tracked as a time-boxed exception, not a
    free pass."""
    return ec.generate_private_key(ec.SECP256R1())


def sign_payment_receipt(message: bytes, private_key) -> bytes:
    """New in this PR: post-quantum signing for payment receipts."""
    return ml_dsa.sign(private_key, message)

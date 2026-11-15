"""Payments service — token integrity, session key exchange, partner
signing, and receipt signing.

Scenario 4: a revised PR, written by a different engineer who wasn't
around for the earlier decision, reintroduces RSA token signing — the
exact line that was accepted (ticket SEC-900) and later removed in the
cleanup PR. The matched line is intentionally identical to the one in
01_pr_rsa_signing/, so it produces the same fingerprint: this tests
whether a finding that comes back is still caught, not whether a
differently-written one is.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from pqc_crypto import ml_dsa, ml_kem  # placeholder imports for post-quantum libraries


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()


def generate_signing_key():
    """Re-added in this PR: token rotation needs a signing keypair again,
    and nobody remembered the earlier migration covered this case too."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def derive_session_key(peer_public_key: bytes) -> bytes:
    """Post-quantum key exchange for session encryption."""
    return ml_kem.encapsulate(peer_public_key)


def generate_legacy_partner_key():
    """One partner's integration still requires elliptic-curve signing —
    tracked as a time-boxed exception, not a free pass."""
    return ec.generate_private_key(ec.SECP256R1())


def sign_payment_receipt(message: bytes, private_key) -> bytes:
    """Post-quantum signing for payment receipts."""
    return ml_dsa.sign(private_key, message)

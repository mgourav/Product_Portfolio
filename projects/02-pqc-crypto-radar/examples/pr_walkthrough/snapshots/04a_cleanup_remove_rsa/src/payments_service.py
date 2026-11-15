"""Payments service — token integrity, session key exchange, partner
signing, and receipt signing.

Cleanup PR (between scenarios 3 and 4): the team finishes migrating
token signing off RSA now that the post-quantum calls are in place,
and deletes `generate_signing_key()` entirely. Nothing new is added
here — this PR exists only to make the RSA finding disappear from
`main`, so Scenario 4 has something to regress.
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric import ec
from pqc_crypto import ml_dsa, ml_kem  # placeholder imports for post-quantum libraries


def checksum(payload: bytes) -> str:
    """Integrity check for outgoing payment payloads."""
    return hashlib.sha256(payload).hexdigest()


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

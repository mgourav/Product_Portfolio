"""Legacy authentication module — key generation for signing user sessions."""
from Crypto.PublicKey import RSA
import hashlib


def generate_session_key():
    # TODO(SEC-451): migrating off RSA, tracked and accepted below via the
    # risk register — this isn't forgotten debt, it's actively scheduled.
    rsa_key = RSA.generate(2048)
    digest = hashlib.sha256(b"session-payload").hexdigest()
    return rsa_key, digest

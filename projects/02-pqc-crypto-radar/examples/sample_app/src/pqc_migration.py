"""New post-quantum key-exchange module, replacing legacy_transport.go over time."""
from ml_kem import generate_keypair as kyber_keygen
from ml_dsa import generate_keypair as dilithium_keygen

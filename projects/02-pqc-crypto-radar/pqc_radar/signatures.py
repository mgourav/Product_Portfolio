"""
Cryptographic algorithm signatures for Crypto Radar.

Each signature is a (compiled regex, metadata) pair. Detection is intentionally
regex/pattern-based for v1 (see the PRD's "Risks" section) — it trades recall/
precision for being trivial to read, extend, and run with zero dependencies.
Patterns are deliberately permissive (case-insensitive, loose on whitespace)
to favor catching real usage over avoiding false positives, since a security
scanner that stays quiet is worse than one that over-flags.

Risk categories:
    quantum-vulnerable   Broken by Shor's algorithm given a large enough
                         cryptographically relevant quantum computer (RSA,
                         ECC/ECDSA/ECDH, Diffie-Hellman, DSA).
    quantum-safe-today   Only quadratically weakened by Grover's algorithm;
                         safe at current key sizes (AES-256, SHA-256/384/512).
                         AES-128 is flagged `monitor` — Grover's halves its
                         effective security to 64 bits, below most compliance
                         bars, even though it isn't "vulnerable" the way RSA is.
    pqc-ready            NIST-standardized post-quantum algorithms (ML-KEM/
                         Kyber, ML-DSA/Dilithium, SLH-DSA/SPHINCS+).
"""

import re
from dataclasses import dataclass
from enum import Enum


class Risk(str, Enum):
    QUANTUM_VULNERABLE = "quantum-vulnerable"
    MONITOR = "monitor"
    QUANTUM_SAFE_TODAY = "quantum-safe-today"
    PQC_READY = "pqc-ready"


@dataclass(frozen=True)
class Signature:
    algorithm: str          # human-readable algorithm name, e.g. "RSA"
    risk: Risk
    language: str           # "python" | "java" | "javascript" | "go" | "c/c++" | "generic"
    pattern: re.Pattern
    note: str = ""          # short reason shown in reports, e.g. why it's risky


def _rx(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


SIGNATURES: list[Signature] = [
    # ---------------------------------------------------------------- Python
    Signature("RSA", Risk.QUANTUM_VULNERABLE, "python",
              _rx(r"\b(rsa\.generate_private_key|RSA\.generate|from\s+Crypto\.PublicKey\s+import\s+RSA)\b"),
              "Shor's algorithm breaks RSA's integer-factorization assumption."),
    Signature("ECC/ECDSA/ECDH", Risk.QUANTUM_VULNERABLE, "python",
              _rx(r"\b(ec\.generate_private_key|ec\.ECDSA|ec\.ECDH|from\s+ecdsa\s+import)\b"),
              "Shor's algorithm breaks the elliptic-curve discrete-log assumption."),
    Signature("Diffie-Hellman", Risk.QUANTUM_VULNERABLE, "python",
              _rx(r"\b(dh\.generate_parameters|dh\.DHParameterNumbers)\b"),
              "Classical DH key exchange is broken by Shor's algorithm."),
    Signature("AES-128", Risk.MONITOR, "python",
              _rx(r"\bAES\.new\([^)]*\b(128|16)\b|algorithms\.AES128\b"),
              "Grover's algorithm halves effective security to 64 bits; below most compliance bars."),
    Signature("AES-256", Risk.QUANTUM_SAFE_TODAY, "python",
              _rx(r"\bAES\.new\([^)]*\b(256|32)\b|algorithms\.AES256\b|algorithms\.AES\(.*256"),
              "Grover's algorithm only halves effective security, to 128 bits — still safe."),
    Signature("SHA-256/384/512", Risk.QUANTUM_SAFE_TODAY, "python",
              _rx(r"\bhashlib\.sha(256|384|512)\b|hashes\.SHA(256|384|512)\(\)"),
              "Hash functions are not broken by Shor's; Grover's gives only a quadratic speedup."),
    Signature("ML-KEM/Kyber", Risk.PQC_READY, "python",
              _rx(r"\b(ml_kem|kyber)\b"), "NIST-standardized post-quantum KEM."),
    Signature("ML-DSA/Dilithium", Risk.PQC_READY, "python",
              _rx(r"\b(ml_dsa|dilithium)\b"), "NIST-standardized post-quantum signature scheme."),

    # ------------------------------------------------------------------ Java
    Signature("RSA", Risk.QUANTUM_VULNERABLE, "java",
              _rx(r'KeyPairGenerator\.getInstance\(\s*"RSA"\s*\)|Cipher\.getInstance\(\s*"RSA'),
              "Shor's algorithm breaks RSA's integer-factorization assumption."),
    Signature("ECC/ECDSA", Risk.QUANTUM_VULNERABLE, "java",
              _rx(r'KeyPairGenerator\.getInstance\(\s*"EC"\s*\)|Signature\.getInstance\(\s*"SHA\d+withECDSA"'),
              "Shor's algorithm breaks the elliptic-curve discrete-log assumption."),
    Signature("DSA", Risk.QUANTUM_VULNERABLE, "java",
              _rx(r'KeyPairGenerator\.getInstance\(\s*"DSA"\s*\)'),
              "Shor's algorithm breaks the discrete-log assumption DSA relies on."),
    Signature("AES-128", Risk.MONITOR, "java",
              _rx(r'KeyGenerator\.getInstance\(\s*"AES"\s*\).*?init\(\s*128\s*\)'),
              "Grover's algorithm halves effective security to 64 bits."),
    Signature("AES-256", Risk.QUANTUM_SAFE_TODAY, "java",
              _rx(r'KeyGenerator\.getInstance\(\s*"AES"\s*\).*?init\(\s*256\s*\)'),
              "Grover's algorithm only halves effective security, to 128 bits — still safe."),
    Signature("AES (key size unknown)", Risk.QUANTUM_SAFE_TODAY, "java",
              _rx(r'Cipher\.getInstance\(\s*"AES/[A-Za-z0-9]+/[A-Za-z0-9]+"\s*\)'),
              "Cipher.getInstance reveals the mode, not the key length — verify the key size manually; this call alone doesn't say AES-128 vs AES-256."),
    Signature("SHA-256/384/512", Risk.QUANTUM_SAFE_TODAY, "java",
              _rx(r'MessageDigest\.getInstance\(\s*"SHA-?(256|384|512)"\s*\)'),
              "Hash functions are not broken by Shor's; Grover's gives only a quadratic speedup."),

    # ------------------------------------------------------------ JavaScript/TypeScript
    Signature("RSA", Risk.QUANTUM_VULNERABLE, "javascript",
              _rx(r"generateKeyPair\w*\(\s*['\"]rsa['\"]|createSign\(\s*['\"]RSA"),
              "Shor's algorithm breaks RSA's integer-factorization assumption."),
    Signature("ECC/ECDSA/ECDH", Risk.QUANTUM_VULNERABLE, "javascript",
              _rx(r"generateKeyPair\w*\(\s*['\"]ec['\"]|createECDH\("),
              "Shor's algorithm breaks the elliptic-curve discrete-log assumption."),
    Signature("AES-128", Risk.MONITOR, "javascript",
              _rx(r"createCipheriv\(\s*['\"]aes-128"),
              "Grover's algorithm halves effective security to 64 bits."),
    Signature("AES-256", Risk.QUANTUM_SAFE_TODAY, "javascript",
              _rx(r"createCipheriv\(\s*['\"]aes-256"),
              "Grover's algorithm only halves effective security, to 128 bits — still safe."),
    Signature("SHA-256/384/512", Risk.QUANTUM_SAFE_TODAY, "javascript",
              _rx(r"createHash\(\s*['\"]sha(256|384|512)['\"]"),
              "Hash functions are not broken by Shor's; Grover's gives only a quadratic speedup."),

    # -------------------------------------------------------------------- Go
    Signature("RSA", Risk.QUANTUM_VULNERABLE, "go",
              _rx(r"\brsa\.(GenerateKey|GenerateMultiPrimeKey)\b"),
              "Shor's algorithm breaks RSA's integer-factorization assumption."),
    Signature("ECC/ECDSA", Risk.QUANTUM_VULNERABLE, "go",
              _rx(r"\becdsa\.(GenerateKey|Sign|Verify)\b"),
              "Shor's algorithm breaks the elliptic-curve discrete-log assumption."),
    Signature("AES (key size unknown)", Risk.QUANTUM_SAFE_TODAY, "go",
              _rx(r"\baes\.NewCipher\b"),
              "Key size comes from the byte slice passed in, not visible from this call alone — verify manually."),
    Signature("SHA-256/384/512", Risk.QUANTUM_SAFE_TODAY, "go",
              _rx(r"\bsha(256|512)\.(New|Sum256|Sum512)\b"),
              "Hash functions are not broken by Shor's; Grover's gives only a quadratic speedup."),

    # ----------------------------------------------------------------- C/C++ (OpenSSL)
    Signature("RSA", Risk.QUANTUM_VULNERABLE, "c/c++",
              _rx(r"\bRSA_generate_key(_ex)?\b"),
              "Shor's algorithm breaks RSA's integer-factorization assumption."),
    Signature("ECC", Risk.QUANTUM_VULNERABLE, "c/c++",
              _rx(r"\bEC_KEY_new(_by_curve_name)?\b"),
              "Shor's algorithm breaks the elliptic-curve discrete-log assumption."),
    Signature("AES-256", Risk.QUANTUM_SAFE_TODAY, "c/c++",
              _rx(r"\bEVP_aes_256_\w+\b"),
              "Grover's algorithm only halves effective security, to 128 bits — still safe."),
    Signature("AES-128", Risk.MONITOR, "c/c++",
              _rx(r"\bEVP_aes_128_\w+\b"),
              "Grover's algorithm halves effective security to 64 bits."),

    # --------------------------------------------------------- Generic / cross-language
    Signature("ML-KEM/Kyber", Risk.PQC_READY, "generic",
              _rx(r"\b(ml-?kem|kyber)\b"), "NIST-standardized post-quantum KEM."),
    Signature("ML-DSA/Dilithium", Risk.PQC_READY, "generic",
              _rx(r"\b(ml-?dsa|dilithium)\b"), "NIST-standardized post-quantum signature scheme."),
    Signature("SLH-DSA/SPHINCS+", Risk.PQC_READY, "generic",
              _rx(r"\b(slh-?dsa|sphincs\+?)\b"), "NIST-standardized post-quantum signature scheme."),
]

# File extension -> language, used to scope which signatures apply to a file.
EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "javascript",
    ".jsx": "javascript",
    ".tsx": "javascript",
    ".go": "go",
    ".c": "c/c++",
    ".h": "c/c++",
    ".cc": "c/c++",
    ".cpp": "c/c++",
    ".hpp": "c/c++",
}

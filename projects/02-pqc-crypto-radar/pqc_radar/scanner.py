"""
Core scanner (PRD requirements R1-R2).

R1: Detect RSA/ECC/DH/DSA, AES, SHA-family, and PQC algorithm usage in
    source files across common languages.
R2: Classify each finding by risk category with a file + line reference.

Design notes:
- Pattern-based (regex), not AST-based. This is a known, documented tradeoff
  (see the PRD's Risks section) — it's trivial to extend and has zero
  dependencies, at the cost of real-world precision/recall.
- A `Finding` carries a stable `fingerprint` (not just file+line) so the
  diff logic in diff.py can recognize "the same finding" even if the file
  is reformatted and the line number shifts slightly.
"""

import hashlib
import os
from dataclasses import dataclass, asdict
from pathlib import Path

from .signatures import SIGNATURES, EXTENSION_LANGUAGE, Risk

# Directories we never want to walk into: VCS metadata, dependency caches,
# and build output. Keeping this list short and generic on purpose — v1
# scans a repo's own source, not its vendored dependencies.
DEFAULT_EXCLUDES = {
    ".git", "node_modules", "vendor", "__pycache__", ".venv", "venv",
    "dist", "build", "target", ".pqc-radar",
}


@dataclass
class Finding:
    file: str
    line: int
    language: str
    algorithm: str
    risk: str          # Risk value, kept as str for clean JSON serialization
    note: str
    snippet: str        # the matched line, trimmed, for human context
    fingerprint: str     # stable id used by diff.py across runs

    def to_dict(self) -> dict:
        return asdict(self)


def _fingerprint(relative_path: str, algorithm: str, snippet: str) -> str:
    """
    Stable identity for a finding that survives line-number drift from
    unrelated edits elsewhere in the file. Deliberately excludes the line
    number; includes the matched snippet so two different call sites of the
    same algorithm in the same file are still distinguished.
    """
    raw = f"{relative_path}:{algorithm}:{snippet.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _iter_source_files(root: Path, excludes: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")]
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in EXTENSION_LANGUAGE:
                yield Path(dirpath) / filename


def scan_file(path: Path, root: Path) -> list[Finding]:
    """Scan a single file and return every signature match found in it."""
    language = EXTENSION_LANGUAGE.get(path.suffix.lower())
    if language is None:
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = text.splitlines()
    relevant_signatures = [s for s in SIGNATURES if s.language in (language, "generic")]
    relative_path = str(path.relative_to(root))

    findings: list[Finding] = []
    for line_no, line in enumerate(lines, start=1):
        for sig in relevant_signatures:
            if sig.pattern.search(line):
                snippet = line.strip()[:160]
                findings.append(Finding(
                    file=relative_path,
                    line=line_no,
                    language=language,
                    algorithm=sig.algorithm,
                    risk=sig.risk.value,
                    note=sig.note,
                    snippet=snippet,
                    fingerprint=_fingerprint(relative_path, sig.algorithm, snippet),
                ))
    return findings


def scan_path(root: str | Path, excludes: set[str] | None = None) -> list[Finding]:
    """
    Walk `root` and return every cryptographic-algorithm finding across all
    supported source files, sorted for deterministic output (stable diffs
    and reports run-to-run).
    """
    root = Path(root).resolve()
    excludes = excludes or DEFAULT_EXCLUDES

    all_findings: list[Finding] = []
    for file_path in _iter_source_files(root, excludes):
        all_findings.extend(scan_file(file_path, root))

    all_findings.sort(key=lambda f: (f.file, f.line, f.algorithm))
    return all_findings


def risk_summary(findings: list[Finding]) -> dict[str, int]:
    """Counts per risk category — used by the report and the CI exit-code check."""
    summary = {risk.value: 0 for risk in Risk}
    for finding in findings:
        summary[finding.risk] += 1
    return summary

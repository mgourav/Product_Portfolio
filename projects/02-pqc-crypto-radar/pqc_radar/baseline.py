"""
Baseline storage and diffing (PRD requirement R3).

Design decision (ARCHITECTURE.md, explicitly confirmed): the baseline file
is written ONLY by an explicit `save_baseline()` call (wired to `--save-
baseline` in the CLI) — never automatically during a plain scan. A finding
stays classified "new" across repeated scans until a human either fixes the
code, registers it as an accepted/sanctioned risk (register.py), or
deliberately re-baselines. This is what keeps "new" meaningful instead of a
label that quietly disappears the second time anyone runs the tool.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .scanner import Finding

TOOL_VERSION = "0.1.0"


@dataclass
class DiffResult:
    new: list[Finding]
    existing: list[Finding]
    resolved: list[Finding]  # was in the baseline, no longer found by this scan


def load_baseline(path: str | Path) -> list[Finding] | None:
    """Returns None if no baseline exists yet (first-ever scan of a repo)."""
    path = Path(path)
    if not path.exists():
        return None

    data = json.loads(path.read_text(encoding="utf-8"))
    return [Finding(**f) for f in data["findings"]]


def save_baseline(path: str | Path, findings: list[Finding]) -> None:
    """
    Writes the baseline file. Only called when the caller explicitly opted
    in (CLI: --save-baseline) — see the module docstring for why this is
    never automatic.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "tool_version": TOOL_VERSION,
        "findings": [f.to_dict() for f in findings],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def diff(current: list[Finding], baseline: list[Finding] | None) -> DiffResult:
    """
    Classifies `current` findings against a (possibly absent) baseline by
    fingerprint. If there's no baseline yet, everything is "new" by
    definition — a first scan has nothing to compare against.

    Deliberately iterates the full `current`/`baseline` lists rather than
    collapsing into {fingerprint: Finding} dicts first. An earlier version
    did that collapse, which silently dropped real occurrences whenever the
    same risky line appeared more than once with an identical fingerprint
    (e.g. the same RSA.generate(2048) call copy-pasted into three new
    functions) — the dashboard's headline count would say "1 new finding"
    while the table correctly showed 3 rows. Fingerprints still decide
    *identity* (new vs. existing vs. resolved); they must not also decide
    *how many times a finding is counted*.
    """
    if baseline is None:
        return DiffResult(new=list(current), existing=[], resolved=[])

    baseline_fps = {f.fingerprint for f in baseline}
    current_fps = {f.fingerprint for f in current}

    new = [f for f in current if f.fingerprint not in baseline_fps]
    existing = [f for f in current if f.fingerprint in baseline_fps]
    resolved = [f for f in baseline if f.fingerprint not in current_fps]

    return DiffResult(new=new, existing=existing, resolved=resolved)

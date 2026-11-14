"""
Unit tests for baseline.py's diff logic — this is the part with real edge
cases (first scan with no baseline, findings that disappear/reappear) and
the part a reviewer would actually check for correctness.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pqc_radar.baseline import diff, save_baseline, load_baseline
from pqc_radar.scanner import Finding


def make_finding(fp: str, algorithm: str = "RSA", line: int = 1) -> Finding:
    return Finding(
        file="src/auth.py", line=line, language="python", algorithm=algorithm,
        risk="quantum-vulnerable", note="test", snippet="RSA.generate(2048)",
        fingerprint=fp,
    )


class TestDiff(unittest.TestCase):
    def test_no_baseline_means_everything_is_new(self):
        current = [make_finding("aaa"), make_finding("bbb")]
        result = diff(current, None)
        self.assertEqual({f.fingerprint for f in result.new}, {"aaa", "bbb"})
        self.assertEqual(result.existing, [])
        self.assertEqual(result.resolved, [])

    def test_unchanged_findings_are_existing(self):
        current = [make_finding("aaa")]
        baseline = [make_finding("aaa")]
        result = diff(current, baseline)
        self.assertEqual(result.new, [])
        self.assertEqual({f.fingerprint for f in result.existing}, {"aaa"})
        self.assertEqual(result.resolved, [])

    def test_new_finding_not_in_baseline(self):
        current = [make_finding("aaa"), make_finding("bbb")]
        baseline = [make_finding("aaa")]
        result = diff(current, baseline)
        self.assertEqual({f.fingerprint for f in result.new}, {"bbb"})
        self.assertEqual({f.fingerprint for f in result.existing}, {"aaa"})

    def test_resolved_finding_in_baseline_not_current(self):
        current = [make_finding("aaa")]
        baseline = [make_finding("aaa"), make_finding("ccc")]
        result = diff(current, baseline)
        self.assertEqual({f.fingerprint for f in result.resolved}, {"ccc"})

    def test_a_resolved_finding_reappearing_counts_as_new_again(self):
        # If something was resolved (baseline updated without it), and later
        # the same code comes back, it should be flagged new again — not
        # silently treated as "we already knew about this."
        baseline = [make_finding("aaa")]  # ccc already dropped from a prior baseline save
        current = [make_finding("aaa"), make_finding("ccc")]
        result = diff(current, baseline)
        self.assertEqual({f.fingerprint for f in result.new}, {"ccc"})

    def test_duplicate_fingerprint_occurrences_are_not_collapsed(self):
        # Regression test for a real bug: the same risky line copy-pasted
        # into 3 new call sites shares one fingerprint (by design — identity
        # is content-based, not line-based). An earlier implementation
        # collapsed {fingerprint: Finding} into a dict before classifying,
        # which silently dropped 2 of the 3 occurrences from diff.new. The
        # dashboard table (built from the raw list) still showed all 3 rows
        # as "new," while the headline count said 1 — a visible, confusing
        # mismatch. Every occurrence must be preserved.
        baseline = [make_finding("known", line=99)]
        current = [
            make_finding("dup", line=10),
            make_finding("dup", line=20),
            make_finding("dup", line=30),
            make_finding("known", line=1),
        ]
        result = diff(current, baseline)
        self.assertEqual(len(result.new), 3, "all 3 duplicate-fingerprint occurrences must count as new")
        self.assertEqual(len(result.existing), 1)

    def test_duplicate_fingerprint_occurrences_in_baseline_all_resolve_together(self):
        # Same issue, mirrored on the resolved side: if 3 occurrences of a
        # fingerprint were baselined and none remain in the current scan,
        # all 3 should show as resolved, not just 1.
        baseline = [make_finding("dup", line=10), make_finding("dup", line=20), make_finding("dup", line=30)]
        current = []
        result = diff(current, baseline)
        self.assertEqual(len(result.resolved), 3)


class TestBaselinePersistence(unittest.TestCase):
    def test_save_then_load_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".pqc-radar" / "baseline.json"
            findings = [make_finding("aaa"), make_finding("bbb", "AES-256")]
            save_baseline(path, findings)

            loaded = load_baseline(path)
            self.assertEqual({f.fingerprint for f in loaded}, {"aaa", "bbb"})

    def test_load_missing_baseline_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "does-not-exist.json"
            self.assertIsNone(load_baseline(path))


if __name__ == "__main__":
    unittest.main()

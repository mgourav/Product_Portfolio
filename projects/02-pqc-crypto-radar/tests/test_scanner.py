"""
Unit tests for scanner.py — specifically the path-validation fix. Regression
test for a real bug: scanning a nonexistent path used to silently return an
empty finding list with no error, indistinguishable from a real clean scan.
For a compliance tool, that's the worst failure mode — "0 findings" has to
mean "we looked and found nothing," never "we didn't actually look."
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pqc_radar.scanner import scan_path


class TestScanPathValidation(unittest.TestCase):
    def test_nonexistent_path_raises_not_silently_empty(self):
        with self.assertRaises(FileNotFoundError):
            scan_path("/this/path/definitely/does/not/exist/anywhere")

    def test_path_that_is_a_file_not_a_directory_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".py") as tmp:
            with self.assertRaises(NotADirectoryError):
                scan_path(tmp.name)

    def test_valid_empty_directory_returns_empty_list_without_raising(self):
        # Contrast with the above: an empty-but-real directory should scan
        # cleanly to an empty list. Only a bad path should raise.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(scan_path(tmp), [])


if __name__ == "__main__":
    unittest.main()

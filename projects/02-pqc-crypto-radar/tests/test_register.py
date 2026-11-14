"""
Unit tests for register.py — specifically the expiry boundary logic, since
that's what makes the register's "audit trail" claim (PRD G3) actually
hold up rather than being a permanent suppression list in disguise.
"""

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pqc_radar.register import accept, status_for, load_register, RegisterStatus


class TestAccept(unittest.TestCase):
    def test_accept_rejects_past_review_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            past_date = (date.today() - timedelta(days=1)).isoformat()
            with self.assertRaises(ValueError):
                accept(path, "fp1", ticket="JIRA-1", review_by=past_date)

    def test_accept_rejects_todays_date(self):
        # review_by must be strictly in the future — "today" would expire
        # the instant it's checked, which defeats the point of accepting it.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            today = date.today().isoformat()
            with self.assertRaises(ValueError):
                accept(path, "fp1", ticket="JIRA-1", review_by=today)

    def test_accept_succeeds_with_future_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            future = (date.today() + timedelta(days=30)).isoformat()
            entry = accept(path, "fp1", ticket="JIRA-1", review_by=future, reason="migration")
            self.assertEqual(entry.ticket, "JIRA-1")

            reloaded = load_register(path)
            self.assertIn("fp1", reloaded)
            self.assertEqual(reloaded["fp1"].reason, "migration")


class TestStatusFor(unittest.TestCase):
    def test_unregistered_fingerprint_is_unreviewed(self):
        self.assertEqual(status_for("unknown-fp", {}), RegisterStatus.UNREVIEWED)

    def test_future_review_date_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            future = (date.today() + timedelta(days=30)).isoformat()
            accept(path, "fp1", ticket="JIRA-1", review_by=future)
            register = load_register(path)
            self.assertEqual(status_for("fp1", register), RegisterStatus.ACCEPTED)

    def test_past_review_date_is_expired_acceptance(self):
        # Can't call accept() with a past date directly (it's rejected), so
        # this simulates time passing: accept with a near-future date, then
        # check status_for as if today were after that date by constructing
        # the register entry directly.
        from pqc_radar.register import RegisterEntry, save_register

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            entries = {"fp1": RegisterEntry(fingerprint="fp1", ticket="JIRA-1", review_by=yesterday)}
            save_register(path, entries)

            register = load_register(path)
            self.assertEqual(status_for("fp1", register), RegisterStatus.EXPIRED_ACCEPTANCE)

    def test_review_date_of_exactly_today_is_still_accepted(self):
        # Boundary check: "review by today" should still count as accepted
        # on the day itself — it expires starting tomorrow, not before.
        from pqc_radar.register import RegisterEntry, save_register

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "register.json"
            today = date.today().isoformat()
            entries = {"fp1": RegisterEntry(fingerprint="fp1", ticket="JIRA-1", review_by=today)}
            save_register(path, entries)

            register = load_register(path)
            self.assertEqual(status_for("fp1", register), RegisterStatus.ACCEPTED)


if __name__ == "__main__":
    unittest.main()

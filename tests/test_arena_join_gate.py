"""Regression tests for the arena join gate (`scripts/arena/jev_player.py`).

Why this file exists
--------------------
On 2026-09-23 a review of our own arena record showed that 5 of the 7 competitions we had
joined were already over, or ended minutes after the join. `joinable=true` answers "are you
allowed in" - it never answered "is there time left to play". Those joins produced a
participant row and nothing else.

`join_gate()` is the fix: it refuses to join anything whose remaining time cannot be
verified. These tests pin its decisions so the gate cannot silently regress.

No network and no credentials are needed - `join_gate` and `_parse_ts` are pure functions.
"""

import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "arena"))

import jev_player as jp  # noqa: E402

NOW = datetime.datetime(2026, 9, 23, 15, 45, tzinfo=datetime.timezone.utc)

HEALTHY = {
    "status": "live",
    "currentPhase": "playing",
    "entryFee": 0,
    "cryptoPrizePool": "0.00000000",
    "cancelReason": None,
    "deletedAt": None,
    "endTime": "2026-09-23T18:00:00.000Z",
}


class TestJoinGate(unittest.TestCase):
    def gate(self, **patch):
        d = dict(HEALTHY)
        d.update(patch)
        return jp.join_gate(d, now=NOW)

    def test_healthy_live_match_is_joinable(self):
        self.assertIsNone(self.gate())

    def test_ended_match_is_skipped(self):
        # the exact shape of the 5-of-7 mistake
        self.assertIn("status=ended", self.gate(status="ended", currentPhase="ended"))

    def test_upcoming_is_skipped(self):
        self.assertIn("status=upcoming", self.gate(status="upcoming"))

    def test_ended_phase_is_skipped_even_if_status_is_stale(self):
        self.assertIn("currentPhase=ended", self.gate(currentPhase="ended"))

    def test_cancelled_is_skipped(self):
        self.assertIn("cancelled", self.gate(cancelReason="too few players"))

    def test_paid_entry_is_skipped(self):
        self.assertIn("entryFee=50", self.gate(entryFee=50))

    def test_crypto_pool_is_skipped(self):
        # these need a bound wallet; out of scope by policy
        self.assertIn("cryptoPrizePool", self.gate(cryptoPrizePool="1.00000000"))

    def test_too_little_time_left_is_skipped(self):
        self.assertIn("only 5 min left", self.gate(endTime="2026-09-23T15:50:00.000Z"))

    def test_threshold_boundary(self):
        # 14 min left -> refuse; 15 min left -> allow
        self.assertIsNotNone(self.gate(endTime="2026-09-23T15:59:00.000Z"))
        self.assertIsNone(self.gate(endTime="2026-09-23T16:00:00.000Z"))

    def test_unparseable_end_time_fails_closed(self):
        for bad in (None, "", "not-a-date"):
            self.assertIn("no parseable endTime", self.gate(endTime=bad))

    def test_replays_the_real_bad_join(self):
        """The join we actually made at 07:11, into a match that had ended at 06:02."""
        real = {
            "status": "ended",
            "currentPhase": "ended",
            "entryFee": 0,
            "cryptoPrizePool": "0.00000000",
            "endTime": "2026-09-23T06:02:43.417Z",
        }
        now = datetime.datetime(2026, 9, 23, 7, 11, tzinfo=datetime.timezone.utc)
        self.assertIsNotNone(jp.join_gate(real, now=now), "the gate must refuse this join")

    def test_parse_ts_accepts_zulu_and_rejects_garbage(self):
        self.assertIsNotNone(jp._parse_ts("2026-09-23T06:02:43.417Z"))
        self.assertIsNotNone(jp._parse_ts("2026-09-23T06:02:43Z"))
        self.assertIsNone(jp._parse_ts("nope"))
        self.assertIsNone(jp._parse_ts(None))


if __name__ == "__main__":
    unittest.main()

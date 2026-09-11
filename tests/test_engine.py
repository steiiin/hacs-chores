"""Meaningful scheduling, accounting, persistence and replay regression cases."""
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import importlib.util
import json
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/hacs_chores/engine.py"
spec = importlib.util.spec_from_file_location("chores_engine", path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
ZONE = "Europe/Berlin"


def dt(value):
    return datetime.fromisoformat(value).astimezone(UTC)


def task(kind="daily", **rule):
    return {"id": "vacuum", "title": "Staubsaugen", "category": "Putzen", "description": "Unter dem Tisch auch.",
            "priority": 2, "effort_minutes": 20, "enabled": True,
            "schedule": {"kind": kind, "start_date": "2026-09-01", "time": "08:00:00", "interval": 1, **rule}}


MEMBERS = [{"id": "a", "name": "Anna", "color": "#538B78", "active": True},
           {"id": "b", "name": "Ben", "color": "#BC7854", "active": True}]


class CalendarTests(unittest.TestCase):
    def next(self, rule, after):
        return engine.next_occurrence(rule, dt(after), ZONE)

    def test_weekly_tuesday(self):
        self.assertEqual(self.next(task("weekly", weekdays=[1])["schedule"], "2026-09-09T10:00:00+02:00"), dt("2026-09-15T08:00:00+02:00"))

    def test_last_friday_in_five_friday_month(self):
        self.assertEqual(self.next(task("monthly_weekday", ordinal=-1, weekday=4)["schedule"], "2026-10-01T00:00:00+02:00"), dt("2026-10-30T08:00:00+01:00"))

    def test_last_friday_in_four_friday_month(self):
        self.assertEqual(self.next(task("monthly_weekday", ordinal=-1, weekday=4)["schedule"], "2026-09-01T00:00:00+02:00"), dt("2026-09-25T08:00:00+02:00"))

    def test_month_31_clamped(self):
        self.assertEqual(self.next(task("monthly_day", day=31)["schedule"], "2027-02-01T00:00:00+01:00"), dt("2027-02-28T08:00:00+01:00"))

    def test_leap_year(self):
        self.assertEqual(self.next(task("monthly_day", day=31)["schedule"], "2028-02-01T00:00:00+01:00"), dt("2028-02-29T08:00:00+01:00"))

    def test_interval_anchor(self):
        self.assertEqual(self.next(task(interval=3)["schedule"], "2026-09-02T08:00:00+02:00"), dt("2026-09-04T08:00:00+02:00"))

    def test_spring_gap_moves_forward(self):
        rule = task(time="02:30:00", start_date="2026-01-01")["schedule"]
        self.assertEqual(self.next(rule, "2026-03-29T00:00:00+01:00"), dt("2026-03-29T03:30:00+02:00"))

    def test_autumn_fold_not_repeated(self):
        rule = task(time="02:30:00")["schedule"]
        first = self.next(rule, "2026-10-25T00:00:00+02:00")
        self.assertEqual(first, dt("2026-10-25T02:30:00+02:00"))
        self.assertEqual(engine.next_occurrence(rule, first, ZONE), dt("2026-10-26T02:30:00+01:00"))

    def test_fixed_daily_clock_survives_dst(self):
        rule = task(start_date="2026-01-01")["schedule"]
        first = dt("2026-03-28T08:00:00+01:00")
        self.assertEqual(engine.next_occurrence(rule, first, ZONE) - first, timedelta(hours=23))

    def test_fifth_weekday_rejected(self):
        with self.assertRaises(ValueError):
            engine.validate_task(task("monthly_weekday", ordinal=5, weekday=4))

    def test_empty_weekdays_rejected(self):
        with self.assertRaises(ValueError):
            engine.validate_task(task("weekly", weekdays=[]))


class HouseholdTests(unittest.TestCase):
    def setUp(self):
        self.now = dt("2026-09-11T10:00:00+02:00")
        self.house = engine.Household([task()], MEMBERS, ZONE, now=self.now)

    def complete(self, member="a", now=None):
        due = self.house.data["states"]["vacuum"]["due_at"]
        return self.house.complete("vacuum", member, due, now=now or self.now)

    def test_overdue_persists_and_missed_occurrences_do_not_accumulate(self):
        self.assertTrue(self.house.snapshot(self.now)["tasks"][0]["is_due"])
        self.assertEqual(self.house.snapshot(self.now)["tasks"][0]["due_at"], "2026-09-01T06:00:00+00:00")
        self.complete()
        self.assertEqual(self.house.snapshot(self.now)["tasks"][0]["due_at"], "2026-09-12T06:00:00+00:00")
        self.assertEqual(self.house.snapshot(self.now)["statistics"][0]["count"], 1)

    def test_no_replay_or_early_completion(self):
        old_due = self.house.data["states"]["vacuum"]["due_at"]
        self.complete()
        with self.assertRaises(ValueError):
            self.house.complete("vacuum", "b", old_due, now=self.now)
        with self.assertRaises(ValueError):
            self.complete("b")
        self.assertEqual(len(self.house.data["history"]), 1)

    def test_persistence_round_trip(self):
        self.complete()
        restored = engine.Household([task()], MEMBERS, ZONE, json.loads(json.dumps(self.house.data)), now=self.now)
        self.assertEqual(restored.snapshot(self.now), self.house.snapshot(self.now))

    def test_after_completion_uses_actual_completion_date(self):
        self.house = engine.Household([task("after_completion", interval=3)], MEMBERS, ZONE, now=self.now)
        self.complete()
        self.assertEqual(self.house.data["states"]["vacuum"]["due_at"], "2026-09-14T06:00:00+00:00")

    def test_weighted_effort_and_top_task_list(self):
        self.complete()
        self.complete("b", self.now + timedelta(days=1))
        self.complete("a", self.now + timedelta(days=2))
        stats = self.house.snapshot(self.now + timedelta(days=2))["statistics"]
        self.assertEqual([(x["name"], x["minutes"], x["count"], x["share"]) for x in stats], [("Anna", 40, 2, 66.7), ("Ben", 20, 1, 33.3)])
        self.assertEqual(stats[0]["tasks"][0]["count"], 2)

    def test_14_day_boundary_and_future_excluded(self):
        self.complete()
        self.assertEqual(self.house.snapshot(self.now + timedelta(days=14))["total_minutes"], 20)
        self.assertEqual(self.house.snapshot(self.now + timedelta(days=14, seconds=1))["total_minutes"], 0)
        self.assertEqual(self.house.snapshot(self.now - timedelta(seconds=1))["total_minutes"], 0)

    def test_effort_change_does_not_rewrite_history(self):
        self.complete()
        changed = task(); changed["effort_minutes"] = 90
        house = engine.Household([changed], MEMBERS, ZONE, self.house.data, now=self.now)
        self.assertEqual(house.snapshot(self.now)["total_minutes"], 20)

    def test_deleted_member_and_task_keep_history(self):
        self.complete()
        house = engine.Household([], MEMBERS[1:], ZONE, self.house.data, now=self.now)
        stats = house.snapshot(self.now)["statistics"]
        self.assertEqual(stats[0]["name"], "Anna")
        self.assertFalse(stats[0]["active"])
        self.assertEqual(stats[0]["tasks"][0]["title"], "Staubsaugen")
        self.assertFalse(house.data["states"])

    def test_undo_restores_due_and_accounting(self):
        before = deepcopy(self.house.data["states"])
        event = self.complete()
        self.house.undo(event, now=self.now + timedelta(minutes=1))
        self.assertEqual(self.house.data["states"], before)
        self.assertEqual(self.house.snapshot(self.now)["total_minutes"], 0)
        with self.assertRaises(ValueError):
            self.house.undo(event, now=self.now)

    def test_undo_expires(self):
        event = self.complete()
        with self.assertRaises(ValueError):
            self.house.undo(event, now=self.now + timedelta(minutes=11))

    def test_undo_rejects_changed_schedule(self):
        event = self.complete()
        changed = task(interval=2)
        house = engine.Household([changed], MEMBERS, ZONE, self.house.data, now=self.now)
        with self.assertRaises(ValueError):
            house.undo(event, now=self.now)

    def test_paused_task_and_inactive_member_rejected(self):
        self.house.members["a"]["active"] = False
        with self.assertRaises(ValueError): self.complete()
        self.house.tasks["vacuum"]["enabled"] = False
        with self.assertRaises(ValueError): self.complete("b")
        self.assertFalse(self.house.snapshot(self.now)["tasks"][0]["is_due"])

    def test_rename_keeps_identity_and_last_done(self):
        self.complete()
        changed = task(); changed["title"] = "Wohnzimmer saugen"
        members = deepcopy(MEMBERS); members[0]["name"] = "Anne"
        house = engine.Household([changed], members, ZONE, self.house.data, now=self.now)
        self.assertEqual(house.snapshot(self.now)["tasks"][0]["last_member_name"], "Anne")
        self.assertEqual(house.data["states"]["vacuum"]["last_done"], engine.stamp(self.now))


if __name__ == "__main__":
    unittest.main()

"""Pure calendar and household logic. No Home Assistant dependency."""
from __future__ import annotations

from calendar import monthrange
from copy import deepcopy
from datetime import UTC, date, datetime, time, timedelta
import re
from uuid import uuid4
from zoneinfo import ZoneInfo


def parse(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Timestamp must include a time zone")
    return result.astimezone(UTC)


def stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def local_time(day: date, clock: str, zone: ZoneInfo) -> datetime:
    """Choose first fold; shift a nonexistent spring time forward by the gap."""
    candidate = datetime.combine(day, time.fromisoformat(clock), zone)
    return candidate.astimezone(UTC).astimezone(zone)


def validate_task(task: dict) -> None:
    if not 1 <= len(task["title"].strip()) <= 120:
        raise ValueError("invalid_title")
    if not 1 <= len(task["category"].strip()) <= 80:
        raise ValueError("invalid_category")
    if len(task.get("description", "")) > 4000:
        raise ValueError("invalid_description")
    if task["priority"] not in (1, 2, 3, 4):
        raise ValueError("invalid_priority")
    if not 1 <= task["effort_minutes"] <= 1440:
        raise ValueError("invalid_effort")
    rule = task["schedule"]
    date.fromisoformat(rule["start_date"])
    clock = time.fromisoformat(rule["time"])
    if clock.tzinfo is not None:
        raise ValueError("invalid_time")
    kind = rule["kind"]
    if kind in ("daily", "after_completion"):
        if not 1 <= rule["interval"] <= 365:
            raise ValueError("invalid_interval")
    elif kind == "weekly":
        if not rule["weekdays"] or any(x not in range(7) for x in rule["weekdays"]):
            raise ValueError("invalid_weekdays")
    elif kind == "monthly_day":
        if not 1 <= rule["day"] <= 31:
            raise ValueError("invalid_day")
    elif kind == "monthly_weekday":
        if rule["ordinal"] not in (1, 2, 3, 4, -1) or rule["weekday"] not in range(7):
            raise ValueError("invalid_ordinal")
    else:
        raise ValueError("invalid_schedule")


def validate_member(member: dict) -> None:
    if not 1 <= len(member["name"].strip()) <= 80:
        raise ValueError("invalid_name")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", member["color"]):
        raise ValueError("invalid_color")


def next_occurrence(rule: dict, after: datetime, timezone: str, *, inclusive=False) -> datetime:
    """Calendar schedule; all comparisons in UTC, all dates in household zone."""
    zone = ZoneInfo(timezone)
    anchor = date.fromisoformat(rule["start_date"])
    day = max(anchor, after.astimezone(zone).date())
    for offset in range(367):
        current = day + timedelta(days=offset)
        kind = rule["kind"]
        if kind in ("daily", "after_completion"):
            matches = (current - anchor).days % rule["interval"] == 0
        elif kind == "weekly":
            matches = current.weekday() in rule["weekdays"]
        elif kind == "monthly_day":
            matches = current.day == min(rule["day"], monthrange(current.year, current.month)[1])
        elif kind == "monthly_weekday":
            last = monthrange(current.year, current.month)[1]
            ordinal = rule["ordinal"]
            matches = current.weekday() == rule["weekday"] and (
                current.day + 7 > last if ordinal == -1 else (current.day - 1) // 7 + 1 == ordinal
            )
        else:
            raise ValueError("invalid_schedule")
        if matches:
            candidate = local_time(current, rule["time"], zone).astimezone(UTC)
            if candidate > after or (inclusive and candidate == after):
                return candidate
    raise ValueError("No occurrence within one year")


class Household:
    """JSON-serializable completion state with stable task/member identifiers."""

    def __init__(self, tasks, members, timezone, data=None, now=None):
        self.tasks = {t["id"]: deepcopy(t) for t in tasks}
        self.members = {m["id"]: deepcopy(m) for m in members}
        self.timezone = timezone
        self.data = deepcopy(data) if data else {"states": {}, "history": []}
        now = now or datetime.now(UTC)
        zone = ZoneInfo(timezone)
        for task_id, task in self.tasks.items():
            validate_task(task)
            state = self.data["states"].get(task_id)
            signature = {"schedule": task["schedule"], "timezone": timezone}
            if state is None or state.get("signature") != signature:
                floor = local_time(date.fromisoformat(task["schedule"]["start_date"]), "00:00", zone)
                if state:
                    floor = max(floor, local_time(now.astimezone(zone).date(), "00:00", zone))
                due = next_occurrence(task["schedule"], floor, timezone, inclusive=True)
                self.data["states"][task_id] = {
                    **(state or {"last_done": None, "last_member_id": None, "last_member_name": None}),
                    "due_at": stamp(due), "signature": signature,
                }
        for member in self.members.values():
            validate_member(member)
        self.data["states"] = {key: value for key, value in self.data["states"].items() if key in self.tasks}

    def complete(self, task_id, member_id, expected_due, now=None, user_id=None):
        now = now or datetime.now(UTC)
        if task_id not in self.tasks or member_id not in self.members:
            raise ValueError("Aufgabe oder Mitglied existiert nicht mehr.")
        task, member = self.tasks[task_id], self.members[member_id]
        state = self.data["states"][task_id]
        if not task["enabled"] or not member["active"]:
            raise ValueError("Aufgabe oder Mitglied ist deaktiviert.")
        if expected_due != state["due_at"]:
            raise ValueError("Dieser Termin wurde bereits erledigt oder geändert. Ansicht aktualisieren.")
        if now < parse(state["due_at"]):
            raise ValueError("Diese Aufgabe ist noch nicht fällig.")
        rule = task["schedule"]
        if rule["kind"] == "after_completion":
            day = now.astimezone(ZoneInfo(self.timezone)).date() + timedelta(days=rule["interval"])
            due = local_time(day, rule["time"], ZoneInfo(self.timezone))
        else:
            due = next_occurrence(rule, now, self.timezone)
        event = {
            "id": uuid4().hex, "task_id": task_id, "member_id": member_id,
            "title": task["title"], "category": task["category"],
            "member_name": member["name"], "member_color": member["color"],
            "effort_minutes": task["effort_minutes"], "completed_at": stamp(now),
            "due_at": state["due_at"], "next_due": stamp(due),
            "previous_state": deepcopy(state), "undone": False,
            "ha_user_id": user_id,
        }
        self.data["history"].append(event)
        state.update(due_at=stamp(due), last_done=stamp(now), last_member_id=member_id, last_member_name=member["name"])
        return event["id"]

    def undo(self, completion_id, now=None):
        now = now or datetime.now(UTC)
        event = next((x for x in reversed(self.data["history"]) if x["id"] == completion_id), None)
        if event is None or event["undone"]:
            raise ValueError("Erledigung nicht gefunden oder bereits zurückgenommen.")
        if now - parse(event["completed_at"]) > timedelta(minutes=10):
            raise ValueError("Rückgängig ist nur innerhalb von zehn Minuten möglich.")
        latest = next(x for x in reversed(self.data["history"]) if x["task_id"] == event["task_id"] and not x["undone"])
        current = self.data["states"].get(event["task_id"])
        if latest is not event or current is None or current["due_at"] != event["next_due"] or current["signature"] != event["previous_state"]["signature"]:
            raise ValueError("Aufgabe wurde zwischenzeitlich geändert.")
        self.data["states"][event["task_id"]] = deepcopy(event["previous_state"])
        event["undone"] = True

    def snapshot(self, now=None):
        now = now or datetime.now(UTC)
        tasks = []
        for task_id, task in self.tasks.items():
            state = self.data["states"][task_id]
            member = self.members.get(state["last_member_id"])
            tasks.append({
                **task, **{k: v for k, v in state.items() if k != "signature"},
                "last_member_name": member["name"] if member else state["last_member_name"],
                "is_due": task["enabled"] and parse(state["due_at"]) <= now,
            })
        tasks.sort(key=lambda t: (not t["enabled"], t["due_at"], -t["priority"], t["title"].casefold(), t["id"]))
        # A rolling 14 x 24-hour window. Immutable event effort avoids rewriting history.
        cutoff = now - timedelta(days=14)
        groups = {m["id"]: {**m, "count": 0, "minutes": 0, "tasks": {}} for m in self.members.values()}
        for event in self.data["history"]:
            if event["undone"] or not cutoff <= parse(event["completed_at"]) <= now:
                continue
            group = groups.setdefault(event["member_id"], {
                "id": event["member_id"], "name": event["member_name"], "color": event["member_color"],
                "active": False, "count": 0, "minutes": 0, "tasks": {},
            })
            group["count"] += 1
            group["minutes"] += event["effort_minutes"]
            item = group["tasks"].setdefault(event["task_id"], {"title": event["title"], "count": 0, "minutes": 0})
            item["count"] += 1
            item["minutes"] += event["effort_minutes"]
        total = sum(g["minutes"] for g in groups.values())
        for group in groups.values():
            group["tasks"] = sorted(group["tasks"].values(), key=lambda t: (-t["count"], t["title"]))
            group["share"] = round(100 * group["minutes"] / total, 1) if total else 0
        return {
            "available": True, "timezone": self.timezone, "now": stamp(now),
            "tasks": tasks, "members": list(self.members.values()),
            "statistics": sorted(groups.values(), key=lambda g: (-g["minutes"], g["name"].casefold())),
            "window_start": stamp(cutoff), "total_minutes": total,
        }

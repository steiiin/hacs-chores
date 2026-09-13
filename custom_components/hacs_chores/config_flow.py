"""Create, edit and remove tasks and members from integration settings."""
from copy import deepcopy
from uuid import uuid4

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from .const import DOMAIN, NAME
from .engine import validate_member, validate_task

KINDS = [("daily", "Alle N Tage (fester Kalender)"), ("weekly", "Bestimmte Wochentage"),
         ("monthly_day", "Monatlich an einem Tag"), ("monthly_weekday", "Monatlich an einem Wochentag"),
         ("after_completion", "N Tage nach Erledigung")]
DAYS = [(str(i), x) for i, x in enumerate(["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"])]


def select(options, multiple=False):
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=[{"value": key, "label": label} for key, label in options],
        mode=selector.SelectSelectorMode.DROPDOWN, multiple=multiple,
    ))


def number(low, high):
    return selector.NumberSelector(selector.NumberSelectorConfig(min=low, max=high, mode=selector.NumberSelectorMode.BOX, step=1))


class ChoresConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ChoresOptionsFlow()


class ChoresOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        self._options = deepcopy(dict(self.config_entry.options))
        self._revision = self._options.get("revision")
        self._options.setdefault("tasks", [])
        self._options.setdefault("members", [])
        return self.async_show_menu(step_id="init", menu_options=[
            "task_add", "task_edit", "task_delete", "member_add", "member_edit", "member_delete",
        ])

    def save(self):
        if self.config_entry.options.get("revision") != self._revision:
            return self.async_abort(reason="concurrent_change")
        self._options["revision"] = uuid4().hex
        return self.async_create_entry(title="", data=self._options)

    def pick(self, step, collection):
        items = self._options[collection]
        if not items:
            return self.async_abort(reason="no_items")
        return self.async_show_form(step_id=step, data_schema=vol.Schema({
            vol.Required("item_id"): select([(x["id"], x.get("title", x.get("name"))) for x in items]),
        }))

    async def async_step_task_add(self, user_input=None):
        self._task = {"id": uuid4().hex, "title": "", "category": "Putzen", "description": "",
                      "priority": 2, "effort_minutes": 10, "enabled": True,
                      "allow_early_completion": False, "schedule": {}}
        return await self.async_step_task()

    async def async_step_task_edit(self, user_input=None):
        if user_input is None:
            return self.pick("task_edit", "tasks")
        self._task = deepcopy(next(x for x in self._options["tasks"] if x["id"] == user_input["item_id"]))
        return await self.async_step_task()

    async def async_step_task(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._task.update({key: user_input[key] for key in (
                "title", "category", "priority", "effort_minutes", "enabled", "allow_early_completion"
            )})
            self._task["description"] = user_input.get("description", "")
            self._task["priority"] = int(self._task["priority"])
            self._task["effort_minutes"] = int(self._task["effort_minutes"])
            self._kind = user_input["kind"]
            if not (1 <= len(self._task["title"].strip()) <= 120 and
                    1 <= len(self._task["category"].strip()) <= 80 and
                    len(self._task["description"]) <= 4000):
                errors["base"] = "invalid_input"
            else:
                return await self.async_step_schedule()
        task = self._task
        task.setdefault("allow_early_completion", False)
        return self.async_show_form(step_id="task", errors=errors, data_schema=vol.Schema({
            vol.Required("title", default=task["title"]): selector.TextSelector(),
            vol.Required("category", default=task["category"]): selector.TextSelector(),
            vol.Optional("description", default=task["description"]): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            vol.Required("priority", default=str(task["priority"])): select([("1", "Niedrig"), ("2", "Normal"), ("3", "Hoch"), ("4", "Dringend")]),
            vol.Required("effort_minutes", default=task["effort_minutes"]): number(1, 1440),
            vol.Required("enabled", default=task["enabled"]): selector.BooleanSelector(),
            vol.Required("allow_early_completion", default=task["allow_early_completion"]): selector.BooleanSelector(),
            vol.Required("kind", default=task["schedule"].get("kind", "daily")): select(KINDS),
        }))

    async def async_step_schedule(self, user_input=None):
        errors = {}
        if user_input is not None:
            rule = {**user_input, "kind": self._kind}
            for key in ("interval", "day", "ordinal", "weekday"):
                if key in rule:
                    rule[key] = int(rule[key])
            if "weekdays" in rule:
                rule["weekdays"] = sorted(int(day) for day in rule["weekdays"])
            self._task["schedule"] = rule
            try:
                validate_task(self._task)
            except (ValueError, KeyError):
                errors["base"] = "invalid_input"
            else:
                self._task["title"] = self._task["title"].strip()
                self._task["category"] = self._task["category"].strip()
                self._options["tasks"] = [x for x in self._options["tasks"] if x["id"] != self._task["id"]] + [self._task]
                return self.save()
        rule = self._task["schedule"]
        fields = {
            vol.Required("start_date", default=rule.get("start_date", dt_util.now().date().isoformat())): selector.DateSelector(),
            vol.Required("time", default=rule.get("time", "08:00:00")): selector.TimeSelector(),
        }
        if self._kind in ("daily", "after_completion"):
            fields[vol.Required("interval", default=rule.get("interval", 1))] = number(1, 365)
        elif self._kind == "weekly":
            fields[vol.Required("weekdays", default=[str(x) for x in rule.get("weekdays", [1])])] = select(DAYS, True)
        elif self._kind == "monthly_day":
            fields[vol.Required("day", default=rule.get("day", 1))] = number(1, 31)
        else:
            fields[vol.Required("ordinal", default=str(rule.get("ordinal", -1)))] = select([
                ("1", "Erster"), ("2", "Zweiter"), ("3", "Dritter"), ("4", "Vierter"), ("-1", "Letzter"),
            ])
            fields[vol.Required("weekday", default=str(rule.get("weekday", 4)))] = select(DAYS)
        return self.async_show_form(step_id="schedule", data_schema=vol.Schema(fields), errors=errors)

    async def async_step_member_add(self, user_input=None):
        self._member = {"id": uuid4().hex, "name": "", "color": "#538B78", "active": True}
        return await self.async_step_member()

    async def async_step_member_edit(self, user_input=None):
        if user_input is None:
            return self.pick("member_edit", "members")
        self._member = deepcopy(next(x for x in self._options["members"] if x["id"] == user_input["item_id"]))
        return await self.async_step_member()

    async def async_step_member(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._member.update(user_input)
            self._member["name"] = self._member["name"].strip()
            try:
                validate_member(self._member)
                if any(m["id"] != self._member["id"] and m["name"].casefold() == self._member["name"].casefold() for m in self._options["members"]):
                    raise ValueError("duplicate_name")
            except ValueError as err:
                errors["base"] = str(err) if str(err) in ("invalid_color", "duplicate_name") else "invalid_input"
            else:
                self._options["members"] = [x for x in self._options["members"] if x["id"] != self._member["id"]] + [self._member]
                return self.save()
        return self.async_show_form(step_id="member", errors=errors, data_schema=vol.Schema({
            vol.Required("name", default=self._member["name"]): selector.TextSelector(),
            vol.Required("color", default=self._member["color"]): selector.TextSelector(),
            vol.Required("active", default=self._member["active"]): selector.BooleanSelector(),
        }))

    async def async_step_task_delete(self, user_input=None):
        return await self.delete_item("task_delete", "tasks", user_input)

    async def async_step_member_delete(self, user_input=None):
        return await self.delete_item("member_delete", "members", user_input)

    async def delete_item(self, step, collection, user_input):
        if user_input is None:
            return self.pick(step, collection)
        self._delete_collection = collection
        self._delete_id = user_input["item_id"]
        item = next(x for x in self._options[collection] if x["id"] == self._delete_id)
        self._delete_name = item.get("title", item.get("name"))
        return await self.async_step_confirm_delete()

    async def async_step_confirm_delete(self, user_input=None):
        if user_input is not None:
            if not user_input["confirm"]:
                return self.async_abort(reason="cancelled")
            self._options[self._delete_collection] = [x for x in self._options[self._delete_collection] if x["id"] != self._delete_id]
            return self.save()
        return self.async_show_form(step_id="confirm_delete", description_placeholders={"name": self._delete_name},
                                    data_schema=vol.Schema({vol.Required("confirm", default=False): selector.BooleanSelector()}))

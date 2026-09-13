"""Next due date, last completion and household member."""
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from .engine import parse
from .entity import ChoreEntity, HouseholdEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        OpenChoresSensor(entry.runtime_data),
        *(ChoreSensor(entry.runtime_data, task, key, name)
          for task in entry.options.get("tasks", [])
          for key, name in (("due_at", "Next due"), ("last_done", "Last completed"),
                            ("last_member_name", "Last completed by"))),
    ])


class OpenChoresSensor(HouseholdEntity, SensorEntity):
    """Number of chores that can be completed now."""

    _attr_icon = "mdi:clipboard-list-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "open_chores", "Open chores")

    @property
    def native_value(self):
        return self.open_chore_count


class ChoreSensor(ChoreEntity, SensorEntity):
    def __init__(self, coordinator, task, key, name):
        super().__init__(coordinator, task, key, name)
        self.key = key
        if key != "last_member_name":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        value = self.task[self.key]
        return parse(value) if value and self.key != "last_member_name" else value

    @property
    def extra_state_attributes(self):
        return {**super().extra_state_attributes, "member_id": self.task["last_member_id"]}

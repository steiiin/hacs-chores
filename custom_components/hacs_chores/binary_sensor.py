"""Whether the current occurrence is due."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .entity import ChoreEntity, HouseholdEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ChoresToDoSensor(entry.runtime_data),
        *(DueSensor(entry.runtime_data, task) for task in entry.options.get("tasks", [])),
    ])


class ChoresToDoSensor(HouseholdEntity, BinarySensorEntity):
    """Whether any chore can be completed now."""

    _attr_icon = "mdi:clipboard-alert-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "chores_to_do", "Chores to do")

    @property
    def is_on(self):
        return self.open_chore_count > 0


class DueSensor(ChoreEntity, BinarySensorEntity):
    _attr_icon = "mdi:clipboard-check-outline"

    def __init__(self, coordinator, task):
        super().__init__(coordinator, task, "is_due", "Is due")

    @property
    def is_on(self):
        return self.task["is_due"]

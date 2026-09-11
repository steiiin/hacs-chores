"""Whether the current occurrence is due."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .entity import ChoreEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(DueSensor(entry.runtime_data, task) for task in entry.options.get("tasks", []))


class DueSensor(ChoreEntity, BinarySensorEntity):
    _attr_icon = "mdi:clipboard-check-outline"

    def __init__(self, coordinator, task):
        super().__init__(coordinator, task, "is_due", "Is due")

    @property
    def is_on(self):
        return self.task["is_due"]


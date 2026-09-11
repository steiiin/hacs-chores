"""Shared task identity and device hierarchy."""
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME


class ChoreEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, task, key, name):
        super().__init__(coordinator)
        self.task_id = task["id"]
        self._attr_unique_id = f"{self.task_id}:{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.task_id)}, name=task["title"],
            manufacturer=NAME, model="Wiederkehrende Aufgabe", entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def task(self):
        return next(t for t in self.coordinator.data["tasks"] if t["id"] == self.task_id)

    @property
    def extra_state_attributes(self):
        return {"task_id": self.task_id, "category": self.task["category"],
                "priority": self.task["priority"], "effort_minutes": self.task["effort_minutes"],
                "due_at": self.task["due_at"], "enabled": self.task["enabled"]}


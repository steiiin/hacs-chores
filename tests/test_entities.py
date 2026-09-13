"""Test household-wide and per-chore entity registration and state."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "chores_entity_test_package"


def module(name, **attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    return result


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class DeviceInfo(dict):
    def __init__(self, **kwargs):
        super().__init__(kwargs)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


class EntityTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        fake = {
            PACKAGE: module(PACKAGE),
            f"{PACKAGE}.const": module(
                f"{PACKAGE}.const", DOMAIN="hacs_chores", NAME="HACS Chores"
            ),
            f"{PACKAGE}.engine": module(f"{PACKAGE}.engine", parse=lambda value: value),
            "homeassistant": module("homeassistant"),
            "homeassistant.components": module("homeassistant.components"),
            "homeassistant.components.sensor": module(
                "homeassistant.components.sensor",
                SensorDeviceClass=SimpleNamespace(TIMESTAMP="timestamp"),
                SensorEntity=type("SensorEntity", (), {}),
            ),
            "homeassistant.components.binary_sensor": module(
                "homeassistant.components.binary_sensor",
                BinarySensorEntity=type("BinarySensorEntity", (), {}),
            ),
            "homeassistant.helpers": module("homeassistant.helpers"),
            "homeassistant.helpers.device_registry": module(
                "homeassistant.helpers.device_registry",
                DeviceEntryType=SimpleNamespace(SERVICE="service"),
                DeviceInfo=DeviceInfo,
            ),
            "homeassistant.helpers.update_coordinator": module(
                "homeassistant.helpers.update_coordinator",
                CoordinatorEntity=CoordinatorEntity,
            ),
        }
        component = ROOT / "custom_components/hacs_chores"
        with patch.dict(sys.modules, fake):
            load(f"{PACKAGE}.entity", component / "entity.py")
            cls.sensor = load(f"{PACKAGE}.sensor", component / "sensor.py")
            cls.binary_sensor = load(
                f"{PACKAGE}.binary_sensor", component / "binary_sensor.py"
            )

    def setUp(self):
        self.coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="household-entry"),
            data={
                "tasks": [
                    {"id": "due", "is_due": True},
                    {"id": "future", "enabled": True, "is_due": False},
                    {"id": "paused", "enabled": False, "is_due": False},
                ]
            },
        )

    async def test_setup_registers_household_and_per_chore_entities(self):
        task = {"id": "due", "title": "Due chore"}
        entry = SimpleNamespace(
            runtime_data=self.coordinator, options={"tasks": [task]}
        )
        sensors = []
        binary_sensors = []

        await self.sensor.async_setup_entry(None, entry, sensors.extend)
        await self.binary_sensor.async_setup_entry(None, entry, binary_sensors.extend)

        self.assertEqual(len(sensors), 4)
        self.assertIsInstance(sensors[0], self.sensor.OpenChoresSensor)
        self.assertEqual(sensors[0]._attr_unique_id, "household-entry:open_chores")
        self.assertEqual(len(binary_sensors), 2)
        self.assertIsInstance(
            binary_sensors[0], self.binary_sensor.ChoresToDoSensor
        )
        self.assertEqual(
            binary_sensors[0]._attr_unique_id, "household-entry:chores_to_do"
        )

    def test_household_device_identity_is_shared(self):
        count = self.sensor.OpenChoresSensor(self.coordinator)
        pending = self.binary_sensor.ChoresToDoSensor(self.coordinator)

        self.assertEqual(count._attr_device_info, pending._attr_device_info)
        self.assertEqual(
            count._attr_device_info["identifiers"],
            {("hacs_chores", "household-entry")},
        )
        self.assertEqual(count._attr_device_info["name"], "HACS Chores")

    def test_states_follow_coordinator_updates(self):
        count = self.sensor.OpenChoresSensor(self.coordinator)
        pending = self.binary_sensor.ChoresToDoSensor(self.coordinator)

        self.assertEqual(count.native_value, 1)
        self.assertTrue(pending.is_on)

        self.coordinator.data["tasks"][1]["is_due"] = True
        self.assertEqual(count.native_value, 2)
        self.assertTrue(pending.is_on)

        for task in self.coordinator.data["tasks"]:
            task["is_due"] = False
        self.assertEqual(count.native_value, 0)
        self.assertFalse(pending.is_on)

    def test_future_and_paused_chores_do_not_count(self):
        for task in self.coordinator.data["tasks"]:
            task["is_due"] = False

        count = self.sensor.OpenChoresSensor(self.coordinator)
        pending = self.binary_sensor.ChoresToDoSensor(self.coordinator)

        self.assertEqual(count.native_value, 0)
        self.assertFalse(pending.is_on)


if __name__ == "__main__":
    unittest.main()

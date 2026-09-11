"""Exercise actual coordinator mutations using small HA boundary doubles."""
import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from test_engine import engine, task, MEMBERS, ZONE, dt


class HAError(Exception):
    pass


def module(name, **attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    return result


prefix = "chores_test_package"
fake = {
    prefix: module(prefix),
    f"{prefix}.const": module(f"{prefix}.const", DOMAIN="hacs_chores", SIGNAL="updated"),
    f"{prefix}.engine": engine,
    "homeassistant": module("homeassistant"),
    "homeassistant.exceptions": module("homeassistant.exceptions", HomeAssistantError=HAError),
    "homeassistant.helpers": module("homeassistant.helpers"),
    "homeassistant.helpers.dispatcher": module("homeassistant.helpers.dispatcher", async_dispatcher_send=lambda *a: None),
    "homeassistant.helpers.event": module("homeassistant.helpers.event", async_track_time_interval=lambda *a: None),
    "homeassistant.helpers.storage": module("homeassistant.helpers.storage", Store=object),
    "homeassistant.helpers.update_coordinator": module("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=object),
}
path = Path(__file__).resolve().parents[1] / "custom_components/hacs_chores/coordinator.py"
with patch.dict(sys.modules, fake):
    spec = importlib.util.spec_from_file_location(f"{prefix}.coordinator", path)
    coordinator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(coordinator_module)


class PersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.now = dt("2026-09-11T10:00:00+02:00")
        self.coordinator = object.__new__(coordinator_module.ChoresCoordinator)
        self.coordinator.engine = engine.Household([task()], MEMBERS, ZONE, now=self.now)
        self.coordinator.lock = asyncio.Lock()
        self.coordinator.active = True
        self.coordinator.unsubscribe = None
        self.writes = []
        self.published = []
        self.coordinator.publish = lambda: self.published.append(deepcopy(self.coordinator.engine.data))
        class MemoryStore:
            async def async_save(inner, data):
                await asyncio.sleep(0)
                self.writes.append(deepcopy(data))
        self.coordinator.store = MemoryStore()
        self.due = self.coordinator.engine.data["states"]["vacuum"]["due_at"]

    async def complete(self):
        return await self.coordinator.mutate("complete", "vacuum", "a", self.due, now=self.now)

    async def test_simultaneous_clients_only_book_once(self):
        results = await asyncio.gather(self.complete(), self.complete(), return_exceptions=True)
        self.assertEqual(sum(isinstance(result, HAError) for result in results), 1)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(len(self.published), 1)
        self.assertEqual(len(self.coordinator.engine.data["history"]), 1)

    async def test_disk_failure_rolls_back_and_publishes_nothing(self):
        before = deepcopy(self.coordinator.engine.data)
        async def fail(data):
            raise OSError("Disk full")
        self.coordinator.store.async_save = fail
        with self.assertRaises(OSError):
            await self.complete()
        self.assertEqual(self.coordinator.engine.data, before)
        self.assertFalse(self.published)

    async def test_unload_waits_for_current_save_and_blocks_new_writes(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def slow_save(data):
            entered.set()
            await release.wait()
            self.writes.append(deepcopy(data))
        self.coordinator.store.async_save = slow_save
        writing = asyncio.create_task(self.complete())
        await entered.wait()
        closing = asyncio.create_task(self.coordinator.close())
        await asyncio.sleep(0)
        self.assertFalse(closing.done())
        release.set()
        await writing
        await closing
        with self.assertRaises(HAError):
            await self.complete()
        self.assertEqual(len(self.writes), 1)

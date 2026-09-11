"""Persist completed chores before publishing changes."""
import asyncio
from copy import deepcopy
from datetime import timedelta
import logging

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SIGNAL
from .engine import Household

_LOGGER = logging.getLogger(__name__)


class ChoresCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry)
        self.entry = entry
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.lock = asyncio.Lock()
        self.active = True
        self.engine = None
        self.unsubscribe = None

    async def load(self):
        saved = await self.store.async_load()
        self.engine = Household(
            self.entry.options.get("tasks", []), self.entry.options.get("members", []),
            self.hass.config.time_zone, saved,
        )
        await self.store.async_save(self.engine.data)
        self.publish()
        self.unsubscribe = async_track_time_interval(self.hass, self.tick, timedelta(seconds=30))

    async def tick(self, _now):
        if self.active:
            self.publish()

    def publish(self):
        self.async_set_updated_data(self.engine.snapshot())
        async_dispatcher_send(self.hass, SIGNAL)

    async def mutate(self, operation, *args, **kwargs):
        async with self.lock:
            if not self.active:
                raise HomeAssistantError("HACS Chores wird neu geladen. Bitte erneut versuchen.")
            old = deepcopy(self.engine.data)
            try:
                result = getattr(self.engine, operation)(*args, **kwargs)
                await self.store.async_save(self.engine.data)
            except ValueError as err:
                self.engine.data = old
                raise HomeAssistantError(str(err)) from err
            except BaseException:
                self.engine.data = old
                raise
            self.publish()
            return result

    async def close(self):
        async with self.lock:
            self.active = False
            if self.unsubscribe:
                self.unsubscribe()


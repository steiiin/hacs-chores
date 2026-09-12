"""Recurring household chores and bundled dashboard cards."""
from pathlib import Path

import voluptuous as vol
from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .const import DOMAIN, FRONTEND_URL, SIGNAL, VERSION
from .coordinator import ChoresCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


def coordinator(hass):
    result = hass.data.get(DOMAIN, {}).get("coordinator")
    if result is None or not result.active:
        raise HomeAssistantError("HACS Chores ist noch nicht bereit.")
    return result


async def async_setup(hass, _config):
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths([
        StaticPathConfig(FRONTEND_URL, str(Path(__file__).parent / "frontend" / "chores-cards.js"), False)
    ])
    frontend.add_extra_js_url(hass, f"{FRONTEND_URL}?v={VERSION}")
    for command in (ws_subscribe, ws_complete, ws_undo):
        websocket_api.async_register_command(hass, command)

    async def complete(call):
        await coordinator(hass).mutate(
            "complete", call.data["task_id"], call.data["member_id"], call.data["due_at"],
            user_id=call.context.user_id,
        )

    async def undo(call):
        await coordinator(hass).mutate("undo", call.data["completion_id"])

    hass.services.async_register(DOMAIN, "complete", complete, schema=vol.Schema({
        vol.Required("task_id"): str, vol.Required("member_id"): str, vol.Required("due_at"): str,
    }))
    hass.services.async_register(DOMAIN, "undo", undo, schema=vol.Schema({vol.Required("completion_id"): str}))
    return True


async def async_setup_entry(hass, entry):
    manager = ChoresCoordinator(hass, entry)
    await manager.load()
    hass.data[DOMAIN]["coordinator"] = manager
    entry.runtime_data = manager
    # Remove registry records belonging to tasks deleted through options.
    registry = er.async_get(hass)
    valid = set(manager.engine.tasks)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id.split(":", 1)[0] not in valid:
            registry.async_remove(entity.entity_id)
    devices = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        if any(domain == DOMAIN and identifier not in valid for domain, identifier in device.identifiers):
            devices.async_update_device(device.id, remove_config_entry_id=entry.entry_id)
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await manager.close()
        hass.data[DOMAIN].pop("coordinator", None)
        async_dispatcher_send(hass, SIGNAL)
        raise
    entry.async_on_unload(entry.add_update_listener(async_reload))
    async_dispatcher_send(hass, SIGNAL)
    return True


async def async_reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.close()
        hass.data[DOMAIN].pop("coordinator", None)
        async_dispatcher_send(hass, SIGNAL)
        return True
    return False


async def async_remove_entry(hass, entry):
    from homeassistant.helpers.storage import Store
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()


@websocket_api.websocket_command({vol.Required("type"): "hacs_chores/subscribe"})
@callback
def ws_subscribe(hass, connection, msg):
    @callback
    def send():
        try:
            payload = coordinator(hass).data
        except HomeAssistantError:
            payload = {"available": False}
        connection.send_event(msg["id"], payload)

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL, send)
    connection.send_result(msg["id"])
    send()


@websocket_api.websocket_command({
    vol.Required("type"): "hacs_chores/complete", vol.Required("task_id"): str,
    vol.Required("member_id"): str, vol.Required("due_at"): str,
})
@websocket_api.async_response
async def ws_complete(hass, connection, msg):
    try:
        event_id = await coordinator(hass).mutate(
            "complete", msg["task_id"], msg["member_id"], msg["due_at"], user_id=connection.user.id,
        )
        connection.send_result(msg["id"], {"completion_id": event_id})
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "chores_error", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): "hacs_chores/undo", vol.Required("completion_id"): str,
})
@websocket_api.async_response
async def ws_undo(hass, connection, msg):
    try:
        await coordinator(hass).mutate("undo", msg["completion_id"])
        connection.send_result(msg["id"])
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "chores_error", str(err))

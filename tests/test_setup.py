"""Test integration setup at the Home Assistant boundary."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def module(name, **attrs):
    result = ModuleType(name)
    result.__dict__.update(attrs)
    return result


def passthrough_decorator(_schema=None):
    return lambda function: function


class StaticPathConfig:
    def __init__(self, url_path, path, cache_headers):
        self.url_path = url_path
        self.path = path
        self.cache_headers = cache_headers


class SetupTests(unittest.IsolatedAsyncioTestCase):
    async def test_setup_serves_and_automatically_loads_cards(self):
        package = "chores_setup_test_package"
        loaded_urls = []
        entity_registry = module("homeassistant.helpers.entity_registry")
        device_registry = module("homeassistant.helpers.device_registry")
        frontend = module(
            "homeassistant.components.frontend",
            add_extra_js_url=lambda hass, url: loaded_urls.append(url),
        )
        websocket_api = module(
            "homeassistant.components.websocket_api",
            websocket_command=passthrough_decorator,
            async_response=lambda function: function,
            async_register_command=lambda hass, command: None,
        )
        fake = {
            package: module(package),
            f"{package}.const": module(
                f"{package}.const",
                DOMAIN="hacs_chores",
                FRONTEND_URL="/hacs_chores/chores-cards.js",
                SIGNAL="updated",
                VERSION="0.2.1",
            ),
            f"{package}.coordinator": module(
                f"{package}.coordinator", ChoresCoordinator=object
            ),
            "voluptuous": module(
                "voluptuous", Required=lambda value: value, Schema=lambda value: value
            ),
            "homeassistant": module("homeassistant"),
            "homeassistant.components": module(
                "homeassistant.components",
                frontend=frontend,
                websocket_api=websocket_api,
            ),
            "homeassistant.components.frontend": frontend,
            "homeassistant.components.websocket_api": websocket_api,
            "homeassistant.components.http": module(
                "homeassistant.components.http", StaticPathConfig=StaticPathConfig
            ),
            "homeassistant.const": module(
                "homeassistant.const",
                Platform=SimpleNamespace(BINARY_SENSOR="binary_sensor", SENSOR="sensor"),
            ),
            "homeassistant.core": module(
                "homeassistant.core", callback=lambda function: function
            ),
            "homeassistant.exceptions": module(
                "homeassistant.exceptions", HomeAssistantError=Exception
            ),
            "homeassistant.helpers": module("homeassistant.helpers"),
            "homeassistant.helpers.entity_registry": entity_registry,
            "homeassistant.helpers.device_registry": device_registry,
            "homeassistant.helpers.dispatcher": module(
                "homeassistant.helpers.dispatcher",
                async_dispatcher_connect=lambda *args: None,
                async_dispatcher_send=lambda *args: None,
            ),
        }
        path = ROOT / "custom_components/hacs_chores/__init__.py"
        with patch.dict(sys.modules, fake):
            spec = importlib.util.spec_from_file_location(f"{package}.__init__", path)
            integration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(integration)

        static_paths = []

        class Http:
            async def async_register_static_paths(self, paths):
                static_paths.extend(paths)

        hass = SimpleNamespace(
            data={},
            http=Http(),
            services=SimpleNamespace(async_register=lambda *args, **kwargs: None),
        )

        self.assertTrue(await integration.async_setup(hass, {}))
        self.assertEqual(loaded_urls, ["/hacs_chores/chores-cards.js?v=0.2.1"])
        self.assertEqual(len(static_paths), 1)
        self.assertEqual(static_paths[0].url_path, "/hacs_chores/chores-cards.js")
        self.assertTrue(static_paths[0].path.endswith("frontend/chores-cards.js"))
        self.assertFalse(static_paths[0].cache_headers)

        removed_entities = []
        removed_devices = []
        entity_entries = [
            SimpleNamespace(entity_id="sensor.active", unique_id="active-task:due_at"),
            SimpleNamespace(entity_id="sensor.deleted", unique_id="deleted-task:due_at"),
            SimpleNamespace(
                entity_id="sensor.open_chores",
                unique_id="household-entry:open_chores",
            ),
        ]
        device_entries = [
            SimpleNamespace(
                id="active-device", identifiers={("hacs_chores", "active-task")}
            ),
            SimpleNamespace(
                id="deleted-device", identifiers={("hacs_chores", "deleted-task")}
            ),
            SimpleNamespace(
                id="household-device",
                identifiers={("hacs_chores", "household-entry")},
            ),
        ]
        registry = SimpleNamespace(
            async_remove=lambda entity_id: removed_entities.append(entity_id)
        )
        devices = SimpleNamespace(
            async_update_device=lambda device_id, **kwargs: removed_devices.append(
                (device_id, kwargs)
            )
        )
        entity_registry.async_get = lambda _hass: registry
        entity_registry.async_entries_for_config_entry = (
            lambda _registry, _entry_id: entity_entries
        )
        device_registry.async_get = lambda _hass: devices
        device_registry.async_entries_for_config_entry = (
            lambda _devices, _entry_id: device_entries
        )

        integration._remove_stale_registry_entries(
            hass,
            SimpleNamespace(entry_id="household-entry"),
            {"active-task": {}},
        )

        self.assertEqual(removed_entities, ["sensor.deleted"])
        self.assertEqual(
            removed_devices,
            [
                (
                    "deleted-device",
                    {"remove_config_entry_id": "household-entry"},
                )
            ],
        )

    def test_manifest_declares_frontend_dependency(self):
        manifest = json.loads(
            (ROOT / "custom_components/hacs_chores/manifest.json").read_text()
        )
        self.assertIn("frontend", manifest["dependencies"])


if __name__ == "__main__":
    unittest.main()

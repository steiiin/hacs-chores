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
                VERSION="0.2.0",
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
            "homeassistant.helpers.entity_registry": module(
                "homeassistant.helpers.entity_registry"
            ),
            "homeassistant.helpers.device_registry": module(
                "homeassistant.helpers.device_registry"
            ),
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
        self.assertEqual(loaded_urls, ["/hacs_chores/chores-cards.js?v=0.2.0"])
        self.assertEqual(len(static_paths), 1)
        self.assertEqual(static_paths[0].url_path, "/hacs_chores/chores-cards.js")
        self.assertTrue(static_paths[0].path.endswith("frontend/chores-cards.js"))
        self.assertFalse(static_paths[0].cache_headers)

    def test_manifest_declares_frontend_dependency(self):
        manifest = json.loads(
            (ROOT / "custom_components/hacs_chores/manifest.json").read_text()
        )
        self.assertIn("frontend", manifest["dependencies"])


if __name__ == "__main__":
    unittest.main()

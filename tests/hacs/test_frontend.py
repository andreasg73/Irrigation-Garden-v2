"""Native Lovelace collections: load first, preserve others, handle YAML resources."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from homeassistant import loader
from homeassistant.core import HomeAssistant
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection, ResourceYAMLCollection
from homeassistant.helpers import issue_registry as ir

from custom_components.irrigation_garden.frontend import async_setup_frontend, RESOURCE_BASE, RESOURCE_URL
from custom_components.irrigation_garden.const import DOMAIN


@pytest_asyncio.fixture
async def frontend_hass(tmp_path):
    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    await ir.async_load(hass)
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    yield hass
    await hass.async_stop()


@pytest.mark.asyncio
async def test_native_storage_registration_preserves_unrelated(frontend_hass):
    hass = frontend_hass
    config = SimpleNamespace(async_load=AsyncMock(return_value={}))
    resources = ResourceStorageCollection(hass, config)
    unrelated = await resources.async_create_item({'url': '/unrelated.js?v=1', 'res_type': 'module'})
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)
    await async_setup_frontend(hass)
    await async_setup_frontend(hass)
    assert hass.http.async_register_static_paths.await_count == 1
    items = resources.async_items()
    assert unrelated in items and len(items) == 2
    assert any(item['url'] == RESOURCE_URL for item in items)
    route = hass.http.async_register_static_paths.call_args.args[0][0]
    assert route.url_path == RESOURCE_BASE and Path(route.path).is_file()
    assert ir.async_get(hass).async_get_issue(DOMAIN, 'frontend_resource') is None


@pytest.mark.asyncio
async def test_native_storage_updates_only_owned_resource(frontend_hass):
    hass = frontend_hass
    resources = ResourceStorageCollection(hass, SimpleNamespace(async_load=AsyncMock(return_value={})))
    previous = await resources.async_create_item({'url': RESOURCE_BASE+'?v=old', 'res_type': 'module'})
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)
    await async_setup_frontend(hass)
    assert len(resources.async_items()) == 1
    assert resources.async_items()[0]['id'] == previous['id']
    assert resources.async_items()[0]['url'] == RESOURCE_URL


@pytest.mark.asyncio
async def test_yaml_resources_are_read_only(frontend_hass):
    hass = frontend_hass
    original = [{'url': '/unrelated.js', 'type': 'module'}]
    resources = ResourceYAMLCollection(original.copy())
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)
    await async_setup_frontend(hass)
    assert resources.async_items() == original
    assert ir.async_get(hass).async_get_issue(DOMAIN, 'frontend_resource')


@pytest.mark.asyncio
async def test_existing_yaml_module_needs_no_repair(frontend_hass):
    hass = frontend_hass
    resources = ResourceYAMLCollection([{'url': RESOURCE_URL, 'type': 'module'}])
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=resources)
    await async_setup_frontend(hass)
    assert ir.async_get(hass).async_get_issue(DOMAIN, 'frontend_resource') is None

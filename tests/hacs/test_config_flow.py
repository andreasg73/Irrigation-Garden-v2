"""Exercise HA 2026.10 flow manager; frontend/device dependencies are stubbed."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from homeassistant import config_entries, loader
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.irrigation_garden import async_setup_entry, async_unload_entry, refresh_issues
from custom_components.irrigation_garden.config_flow import idle, prerequisites
from custom_components.irrigation_garden.const import CARD_MARKERS, DOMAIN, VERSION

ROOT = Path(__file__).resolve().parents[2]


@pytest_asyncio.fixture
async def hass(tmp_path):
    (tmp_path / "custom_components").mkdir()
    (tmp_path / "custom_components/irrigation_garden").symlink_to(ROOT / "custom_components/irrigation_garden")
    hass = HomeAssistant(str(tmp_path))
    loader.async_setup(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {})
    await loader.async_get_custom_components(hass)
    await ir.async_load(hass)
    # This suite runs no HTTP/frontend server and controls no devices. Native
    # integration discovery, schemas, flow manager and entry storage stay real.
    with patch("homeassistant.config_entries.async_process_deps_reqs", new=AsyncMock()), patch(
        "homeassistant.config_entries.ConfigEntry.async_setup", new=AsyncMock(return_value=True)
    ), patch("homeassistant.config_entries.async_setup_component", new=AsyncMock(return_value=True)):
        yield hass
        await hass.async_block_till_done()
        await hass.async_stop()


async def create_entry(hass, existing=False):
    if existing:
        hass.states.async_set("input_number.irrigation_number_of_zones", "4")
        hass.states.async_set("input_text.irrigation_zone1_switch_entity_id", "switch.existing_valve")
        hass.states.async_set("switch.existing_valve", "off")
    with patch("custom_components.irrigation_garden.config_flow.prerequisites", new=AsyncMock(return_value="OK")):
        flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert flow["step_id"] == "user"
        flow = await hass.config_entries.flow.async_configure(flow["flow_id"], {"language": "pl", "dashboard_url": "irrigation-garden"})
        assert flow["step_id"] == "confirm"
        rejected = await hass.config_entries.flow.async_configure(flow["flow_id"], {"acknowledge": False})
        assert rejected["errors"]["base"] == "acknowledge_required"
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], {"acknowledge": True})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    return result["result"]


@pytest.mark.asyncio
async def test_existing_installation_preserves_states_and_is_unique(hass):
    calls = []
    hass.services.async_register("switch", "turn_on", lambda call: calls.append(call))
    hass.services.async_register("switch", "turn_off", lambda call: calls.append(call))
    entry = await create_entry(hass, existing=True)
    assert entry.data["existing_installation"] is True
    assert hass.states.get("input_number.irrigation_number_of_zones").state == "4"
    assert hass.states.get("input_text.irrigation_zone1_switch_entity_id").state == "switch.existing_valve"
    assert not calls
    duplicate = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert duplicate["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_update_language_and_activation_status(hass):
    entry = await create_entry(hass)
    await async_setup_entry(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "package_activation")
    hass.states.async_set("input_text.irrigation_garden_package_release", entry.data["release_id"])
    refresh_issues(hass, entry)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "package_activation") is None
    old_release = entry.data["release_id"]
    with patch("custom_components.irrigation_garden.config_flow.prerequisites", new=AsyncMock(return_value="OK")):
        flow = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(flow["flow_id"], {"language": "en", "acknowledge": True})
    assert result["type"] == "create_entry"
    assert entry.data["language"] == "en" and entry.data["release_id"] != old_release
    assert ir.async_get(hass).async_get_issue(DOMAIN, "package_activation")
    await async_unload_entry(hass, entry)
    assert (Path(hass.config.config_dir) / "irrigation_garden/package.yaml").is_file()
    assert entry.data["prepared_version"] == VERSION


@pytest.mark.asyncio
@pytest.mark.parametrize("active_entity", ["script.irrigation_run_a_cycle", "input_boolean.irrigation_cycle3_running", "switch.existing_valve"])
async def test_active_watering_blocks_staging(hass, active_entity):
    hass.states.async_set("input_text.irrigation_zone1_switch_entity_id", "switch.existing_valve")
    hass.states.async_set(active_entity, "on")
    assert not idle(hass)
    with patch("custom_components.irrigation_garden.config_flow.prerequisites", new=AsyncMock(return_value="OK")):
        flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        flow = await hass.config_entries.flow.async_configure(flow["flow_id"], {"language": "pl", "dashboard_url": "irrigation-garden"})
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], {"acknowledge": True})
    assert result["errors"]["base"] == "watering_active"
    assert not (Path(hass.config.config_dir) / "irrigation_garden").exists()


@pytest.mark.asyncio
async def test_resource_check_loads_before_enumeration_without_edits(hass):
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    loaded = []
    items = [{"id": str(i), "url": f"/hacsfiles/{name}/{name}.js"} for i, name in enumerate(CARD_MARKERS)]
    items += [{"id": "browser", "url": "/browser_mod.js"}]
    async def info():
        loaded.append(True)
    def read_items():
        assert loaded
        return items
    hass.data[LOVELACE_DATA] = SimpleNamespace(resources=SimpleNamespace(async_get_info=info, async_items=read_items))
    hass.services.async_register("browser_mod", "popup", lambda call: None)
    with patch.object(hass.config_entries, "async_entries", return_value=[SimpleNamespace(state=config_entries.ConfigEntryState.LOADED)]):
        assert await prerequisites(hass) == "OK"
    assert len(items) == 7

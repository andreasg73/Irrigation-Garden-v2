"""Explicit staging wizard; existing entities are detected, never recreated here."""
from __future__ import annotations

from pathlib import Path

import probatio as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CARD_MARKERS, DOMAIN, TITLE, VERSION
from .installer import InstallError, prepare, validate_choices


def idle(hass) -> bool:
    """Avoid preparing an update while watering or an output is active."""
    for entity_id in ["script.irrigation_run_a_cycle", "script.irrigation_run_a_single_zone_on_demand"] + [
        f"input_boolean.irrigation_cycle{i}_running" for i in (1, 2, 3)
    ]:
        state = hass.states.get(entity_id)
        if state and state.state not in {"off", "idle"}:
            return False
    for zone in range(1, 17):
        mapping = hass.states.get(f"input_text.irrigation_zone{zone}_switch_entity_id")
        if mapping and mapping.state.startswith("switch."):
            target = hass.states.get(mapping.state)
            if target and target.state == "on":
                return False
    return True


async def prerequisites(hass) -> str:
    """Read the loaded resource collection before enumerating it (lazy-load safe)."""
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    lovelace = hass.data.get(LOVELACE_DATA)
    urls = []
    if lovelace is not None:
        resources = lovelace.resources
        await resources.async_get_info()
        urls = [str(item.get("url", "")).lower() for item in resources.async_items()]
    missing = [name for name in CARD_MARKERS if not any(name in url for url in urls)]
    browser_entries = hass.config_entries.async_entries("browser_mod")
    if not any(entry.state is ConfigEntryState.LOADED for entry in browser_entries):
        missing.append("Browser Mod integration (loaded)")
    if not hass.services.has_service("browser_mod", "popup"):
        missing.append("browser_mod.popup")
    if not any("browser_mod" in url for url in urls):
        missing.append("Browser Mod frontend module")
    return ", ".join(missing) or "OK"


def choices(data=None):
    data = data or {}
    return vol.Schema({
        vol.Required("language", default=data.get("language", "en")): selector.SelectSelector(
            selector.SelectSelectorConfig(options=["en", "pl"], translation_key="language")),
        vol.Required("dashboard_url", default=data.get("dashboard_url", "irrigation-garden")): str,
    })


class IrrigationGardenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Prepare a single installation; user explicitly activates its YAML package."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        errors = {}
        if user_input is not None:
            try:
                validate_choices(user_input["language"], user_input["dashboard_url"])
            except InstallError:
                errors["base"] = "invalid_choices"
            else:
                self._choices = user_input
                return await self.async_step_confirm()
        return self.async_show_form(step_id="user", data_schema=choices(user_input), errors=errors)

    async def async_step_confirm(self, user_input=None):
        existing = self.hass.states.get("input_number.irrigation_number_of_zones") is not None
        errors = {}
        if user_input is not None:
            if not user_input.get("acknowledge"):
                errors["base"] = "acknowledge_required"
            elif not idle(self.hass):
                errors["base"] = "watering_active"
            else:
                try:
                    installed = await self.hass.async_add_executor_job(
                        prepare, self.hass.config.config_dir, Path(__file__).with_name("bundle.zip"),
                        self._choices["language"], self._choices["dashboard_url"])
                except (OSError, ValueError):
                    # Do not log user paths, states or configuration contents.
                    errors["base"] = "prepare_failed"
                else:
                    return self.async_create_entry(title=TITLE, data={
                        **self._choices, "prepared_version": VERSION,
                        "release_id": installed["release"].split("/")[-1],
                        "existing_installation": existing,
                    })
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({
            vol.Required("acknowledge", default=False): bool,
        }), errors=errors, description_placeholders={
            "dependencies": await prerequisites(self.hass),
            "existing": "YES / TAK" if existing else "NO / NIE",
        })

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return IrrigationGardenOptionsFlow()


class IrrigationGardenOptionsFlow(config_entries.OptionsFlow):
    """Stage an update/language change deliberately; never overwrite live settings."""
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            if not user_input.get("acknowledge"):
                errors["base"] = "acknowledge_required"
            elif not idle(self.hass):
                errors["base"] = "watering_active"
            else:
                try:
                    installed = await self.hass.async_add_executor_job(
                        prepare, self.hass.config.config_dir, Path(__file__).with_name("bundle.zip"),
                        user_input["language"], self.config_entry.data["dashboard_url"])
                except (OSError, ValueError):
                    errors["base"] = "prepare_failed"
                else:
                    self.hass.config_entries.async_update_entry(self.config_entry, data={
                        **self.config_entry.data, "language": user_input["language"],
                        "prepared_version": VERSION, "release_id": installed["release"].split("/")[-1],
                    })
                    from . import refresh_issues
                    refresh_issues(self.hass, self.config_entry)
                    return self.async_create_entry(title="", data={})
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required("language", default=self.config_entry.data["language"]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=["en", "pl"], translation_key="language")),
            vol.Required("acknowledge", default=False): bool,
        }), errors=errors, description_placeholders={"dependencies": await prerequisites(self.hass)})

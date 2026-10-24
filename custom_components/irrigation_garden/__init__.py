"""HACS installation assistant for the unchanged original irrigation engine."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, ISSUE_SETUP, ISSUE_UPDATE, VERSION


@callback
def refresh_issues(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Report prepared-versus-active package status; never activate actuators."""
    marker = hass.states.get("input_text.irrigation_garden_package_release")
    if marker and marker.state == entry.data.get("release_id"):
        ir.async_delete_issue(hass, DOMAIN, ISSUE_SETUP)
    else:
        ir.async_create_issue(hass, DOMAIN, ISSUE_SETUP, is_fixable=False,
                             severity=ir.IssueSeverity.WARNING, translation_key=ISSUE_SETUP,
                             learn_more_url="https://github.com/andreasg73/Irrigation-Garden-v2/blob/modernization-ha-2026.10/docs/HACS_INSTALLATION.md")
    if entry.data.get("prepared_version") != VERSION:
        ir.async_create_issue(hass, DOMAIN, ISSUE_UPDATE, is_fixable=False,
                             severity=ir.IssueSeverity.WARNING, translation_key=ISSUE_UPDATE)
    else:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_UPDATE)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Observe installation only. Staging requires a deliberate config/options flow."""
    refresh_issues(hass, entry)

    @callback
    def started(_event):
        refresh_issues(hass, entry)

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, started))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Do not delete packages or user settings when unloading the installer."""
    ir.async_delete_issue(hass, DOMAIN, ISSUE_SETUP)
    ir.async_delete_issue(hass, DOMAIN, ISSUE_UPDATE)
    return True

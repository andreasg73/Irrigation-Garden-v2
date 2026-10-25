"""Serve the shipped UI module and register only our owned frontend resource."""
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, VERSION

RESOURCE_BASE = '/irrigation_garden_static/irrigation-garden-ui.js'
RESOURCE_URL = RESOURCE_BASE + '?v=' + VERSION


async def async_setup_frontend(hass):
    """Keep other resources intact; YAML resource lists remain user-managed."""
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get('static_registered'):
        await hass.http.async_register_static_paths([
            StaticPathConfig(RESOURCE_BASE, str(Path(__file__).with_name('frontend') / 'irrigation-garden-ui.js'), False)
        ])
        data['static_registered'] = True
    lovelace = hass.data.get(LOVELACE_DATA)
    resources = lovelace.resources if lovelace else None
    if resources is not None:
        await resources.async_get_info()  # storage is lazy-loaded; never enumerate first
        owned = [item for item in resources.async_items() if item.get('url', '').split('?')[0] == RESOURCE_BASE]
        if any(item.get('url') == RESOURCE_URL and item.get('type') == 'module' for item in owned):
            ir.async_delete_issue(hass, DOMAIN, 'frontend_resource')
            return
        if hasattr(resources, 'async_create_item'):
            if len(owned) == 1:
                await resources.async_update_item(owned[0]['id'], {'url': RESOURCE_URL, 'res_type': 'module'})
            elif not owned:
                await resources.async_create_item({'url': RESOURCE_URL, 'res_type': 'module'})
            else:
                resources = None  # ambiguous user edits: report rather than delete
            if resources is not None:
                ir.async_delete_issue(hass, DOMAIN, 'frontend_resource')
                return
    ir.async_create_issue(hass, DOMAIN, 'frontend_resource', is_fixable=False,
                         severity=ir.IssueSeverity.WARNING, translation_key='frontend_resource',
                         translation_placeholders={'url': RESOURCE_URL})

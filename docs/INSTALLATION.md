# Installation — Home Assistant 2026.10.2 baseline

This is a YAML package plus a compiled version of the original Lovelace UI. It is not a HACS custom integration and is not installed by copying a Python component into `custom_components`.

## Before installing

Back up your current configuration. If another Kloggy version already defines `irrigation_*` entities, do not load both sets of packages: they use the same IDs. An existing irrigation controller must not be scheduled concurrently on the same valves during migration.

The full registry includes all 27 engine files and both Logging files. It also includes the original optional MQTT remote example. Review it if your installation has no MQTT integration. Notifications (`script.notify`), announcements (`script.announcement`), holiday mode and `notify.log_irrigation` are installation-specific optional features. Their absent entities may still be reported by reference-checking tools even though runtime calls are guarded. No fake replacement entities are provided.

## 1. Install frontend dependencies

Install and register these custom cards, normally through HACS:

| Dependency | Tested version |
| --- | --- |
| button-card | 7.0.1 |
| hui-element | 1.1.2 |
| state-switch | 1.9.6 |
| config-template-card | 1.3.6 |
| mini-graph-card | 0.13.0 |
| card-mod | 4.2.1 |
| Browser Mod | 3.4.0 |

These are tested versions, not a statement that they are the newest releases. Repository URLs and vendor hashes are in `dependencies.json`.

For Browser Mod, copying files is insufficient: add its integration under Settings → Devices & services, check that its entry is loaded, verify `browser_mod.popup` exists, and load its frontend module. Refresh existing clients after installation. Without this, the original configuration popups cannot open.

`lovelace_gen`, layout-card and time-picker-card are not required by the current compiled view. Do not load the raw authoring YAML directly as the dashboard; use `dist/en/irrigation_dashboard.yaml` or its Polish equivalent.

## 2. Copy the source

Copy this repository to `/config/irrigation_garden_v2/`. Keep the directory layout intact. If you choose a different path, update the explicit include paths in `installation/packages.yaml` and the dashboard registration example.

## 3. Merge the package registry

`installation/configuration.example.yaml` shows the shape. Merge the registry into your existing `homeassistant.packages` setup; do not duplicate the `homeassistant` root and do not overwrite an existing package configuration blindly. If you already use `!include_dir_named` or another registry, add this registry through that existing mechanism.

The supplied registry uses only the 29 intended package files. Never apply `!include_dir_named` to the whole repository: authoring templates and compiled dashboards are not automation packages.

## 4. Register a separate YAML dashboard

Use the `lovelace.dashboards.irrigation-garden` example. Storage-mode dashboards can remain as they are. English uses `dist/en/irrigation_dashboard.yaml` with title `Irrigation Garden`; Polish uses `dist/pl/irrigation_dashboard.yaml` with title `Podlewanie Ogrodu`.

The sidebar title belongs to the registration, while the view title comes from INI. Rebuilding the view does not automatically update sidebar metadata. Dashboard text replacements normally need only a frontend refresh; adding initial YAML registrations/packages requires validation and the appropriate HA restart.

## 5. Validate and start without outputs

Run the full Home Assistant configuration check before restarting. After the first start, verify:

- `input_boolean.irrigation_master_control_switch` is OFF.
- `input_boolean.irrigation_disable_switches` is ON.
- `input_boolean.irrigation_output_mode_initialized` is ON once startup initialization finishes.
- Both scheduled cycles are OFF; no worker or zone timer is active.
- All valve mapping fields are `Not set` on a fresh installation.

On an existing installation helper values may be restored. Do not assume fresh defaults or overwrite restored settings without checking them. Master is deliberately OFF on each start; output mode is restored on subsequent boots so an interrupted physical run can be cleaned up.

## 6. Configure through the original panel

Use General → Number Of Zones to select 1–16 zones. Click a zone name to set its name and Switch Name (`switch.*`). Set separate durations and weekdays for each scheduled cycle, and use the start-time popup for fixed time/sunrise/sunset and wait conditions.

For initial verification use virtual switch entities and keep Disable Switches ON. Test Mode changes watering-duration units from minutes to seconds; it is separate from Disable Switches and must not be confused with permission to operate hardware.

Use General → Weather Sensors to configure your own sources. Required numeric units are °C and mm (legacy custom sensors without a unit are also accepted by the original compatibility path). A `weather.*` entity is not a substitute for every required temperature/rain sensor. Missing required data retains the last valid correction rather than fabricating rainfall or temperature.

Use rainfall/temperature corrections only after checking the sources, units and history. Optional controller Wi-Fi fields accept your own sensor entities. Configure remote control, notifications and logging only if you use them.

## Physical migration and rollback

The software tests do not establish the physical fail-safe behavior of your relay/controller. Check hardware defaults, maximum run time, loss of HA/network and power recovery on your own installation before enabling real outputs.

Disable the previous scheduler before mapping physical valves to this system. Never operate two schedulers on the same outputs. Start with a supervised single-zone trial and verify OFF acknowledgment.

To roll back the added dashboard, restore its previous YAML/registration. To roll back the engine, first stop it and verify outputs closed, then restore only the package files and registry entry you changed. A full HA restore is not the default rollback for one file change.

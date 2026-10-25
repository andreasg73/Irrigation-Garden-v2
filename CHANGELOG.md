# Irrigation Garden v2 — development, 2026-10-24

Documentation update, 2026-10-25: replaced the weather-source setup guide with EN/PL entity mappings, unit/period requirements, forecast-versus-measurement guidance and current outlook proxy behavior. Marked SmartWeather as an optional historical example while preserving its original body. No engine, dashboard or installation payload changes.

Based on original Kloggy HA-Irrigation-Version2, master `532f01b5e`, incorporating a modernization reference from tinkerfish PR #103 and subsequent changes.

- HACS custom-repository installation assistant 0.1.0b1 bundles the exact published original engine and EN/PL dashboard. Explicit package activation, migration instructions, versioned releases, update options and Repairs status; no automatic global YAML edits or actuator actions. See [HACS guide](docs/HACS_INSTALLATION.md).
- UI module 0.2.0b1 adds searchable entity assignment with explicit save/cancel, supported-domain/unit filters, active-watering and concurrent-edit guards, plus browser-local light/dark appearance for original cards and popups. The29 engine packages and original control structure remain unchanged. HACS serves/registers only the project-owned module; manual installs register it separately.
- HA 2026.10.2 syntax/schema compatibility; safe defaults for numeric filters and missing attributes.
- STOP/CANCEL and Master OFF stop active execution before closing outputs; manual-zone settings are restored from persistent snapshots.
- Output acknowledgment, bounded waits, active-output snapshots, watchdog and controlled shutdown/restart cleanup. Each service boundary rechecks output permissions.
- Package-owned automations selected by stable IDs, avoiding unrelated automations with similar names.
- Dynamic activity proxies for history, calendar-day history boundaries and dated rainfall/temperature data with missing-source handling.
- Replaced author-specific references such as `script.notify`, recipient-name entities and external weather descriptions with configurable project-owned helpers, notification/announcement/logging adapters and `sensor.irrigation_weather_outlook`. Unconfigured external adapters are skipped; no dummy measurements are created to hide missing-entity repairs. See [optional feature configuration](docs/OPTIONAL_FEATURES.md).
- Original 41 Lovelace source files compiled offline, with native zone-count conditions and compatibility fixes for current cards/popups.
- UTF-8 INI localization, EN/PL 248 messages each; displayed default names translated while custom names and canonical control values are preserved.
- Wrapping of long translated headings and settings labels.

The new public repository layout uses root-level original source directories, generic installation examples and portable build/test paths. It contains no exported state or valve mappings from the maintainer's HA instance.

Known scope: no physical production migration is demonstrated by publication; isolated tests and a safe live installation check do not guarantee hardware behavior during power loss or communication failure. Native dropdown options and some backend/Jinja values can remain English. Manual installation selects language at build time; the HACS assistant selects the bundled EN/PL dashboard in its wizard/options.

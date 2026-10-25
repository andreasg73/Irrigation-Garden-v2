# Validation and limits

Baseline: Home Assistant 2026.10.2 / frontend 20260930.4. The package was activated in a live installation with outputs blocked and mapped only to virtual test switches. Full configuration validation, original worker dry-runs, STOP and Master OFF were checked during development. Later localization checks did not change watering settings or mappings.

## Portable publication checks

Python 3.10+ and Node.js (tested locally with Python 3.12 and Node 24):

```sh
python -m pip install -r requirements.txt
python tools/build_i18n_release.py --language en --output dist/en
python tools/build_i18n_release.py --language pl --output dist/pl
python tools/test_localization.py
node tools/test_localization_js.cjs
python tools/check_publication.py
```

The localization contracts cover English identity, preserved controls outside presentation styles, INI fallback, invalid keys/markup/templates, Unicode, JavaScript syntax and representative labels/statuses/custom names. The 0.3.0b1 baseline has 11 Python localization contracts, 1330 JavaScript syntax cases and 13 behavior cases. Counts describe this revision rather than every future version.

The publication check parses all 29 engine/logging packages, verifies package-registry targets, checks generated YAML/JSON equality and recorded hashes, and rejects common private-state/credential artifacts. It is not a substitute for the native HA schema validator or a physical device test.

## Native isolated fixtures

The native fixture scripts in `tools/test_*.py` (other than localization) require an isolated **Python 3.14 / Home Assistant 2026.10.2** environment. They create local state, use a fixed virtual-switch allowlist and do not load the installation's real MQTT, HTTP, shell or valve integrations. Do not run them in a production HA Python environment.

Typical isolated invocation:

```sh
python tools/prepare_schema_config.py
python tools/schema_validate.py
python tools/test_runtime.py
python tools/test_extended.py
python tools/test_shutdown.py
python tools/test_output_mode_races.py
```

Other fixtures cover weather calendars, units, missing data, synchronization, history/Recorder, controllers and logging. Their historical development reports belong to separate source revisions and are not summed here as a single claim of complete coverage. The publication checks do not rerun the whole native campaign.

## Remaining limits

- No certification of physical valves, physical phones or controller fail-safes.
- A controlled stop/start is not a guarantee against sudden power loss or unsaved restore-state data.
- Not all optional external integrations are configured by the package; reference-checking tools may flag their missing example entities.
- Some native compact labels can still be abbreviated. Some backend/Jinja text and canonical dropdown values remain English.
- Wider UI coverage and occasional isolated-frontend latency observations from development are not claimed resolved by publishing this fork.
- `live_native_loader_equality: false` in a portable build manifest means that the offline builder did not validate a particular target HA installation. Live verification is installation-specific and is not copied as a guarantee for other users.

## HACS installation assistant

In an isolated Python 3.14 environment with `homeassistant==2026.10.2 pytest pytest-asyncio`, run `python -m pytest tests/hacs -q`. The suite validates original-source identity, native package configuration in EN/PL, real config/options flows with frontend setup stubbed, existing state preservation, explicit acknowledgment, active-watering checks, lazy resource loading, interrupted staging/retry and managed-file protection. It does not operate physical valves or claim a completed user migration. CI also rebuilds the deterministic HACS bundle and rejects drift from the committed payload.

## Entity picker and appearance

`node tools/test_ui_dom.cjs` requires `happy-dom@21.0.4` and Python requirements. It runs programmatic DOM events against the actual UI module, with transport blocks and an explicit mock helper-write boundary. It checks filters, draft/cancel/save, input focus during updates and candidate rename, failed/delayed/duplicate saves, concurrent edits, watering guards, keyboard selection, local theme persistence/scope, view cleanup, translations and absent actuator requests. Card-helper creation is stubbed; no browser geometry/touch/IME is claimed. The initial file-based browser fixture was blocked by browser URL policy. Live HA screenshots are a separate rendering layer.

## Weather-source diagnostics

`node tools/test_weather_diagnostics.cjs` uses the same `happy-dom@21.0.4` dependency. Its 35 programmatic contracts cover source purpose, missing assignments/entities, invalid domains/units/values, rain-contact states, shared read requests, refresh throttling, delayed responses, failed/malformed reads, recovery, and preserving an open editor. Requests are mocked at the read-only API boundary; no real HA report request or physical sensor is exercised by this suite. Actual report-time rendering was checked separately in a live HA installation.

CI runs the portable checks, native installer/frontend suite and both DOM suites. Check the [Actions page](https://github.com/andreasg73/Irrigation-Garden-v2/actions) for the exact commit you intend to install. Passing tests on a previous PR does not establish the result for a newer commit.

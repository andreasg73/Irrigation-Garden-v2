# Irrigation Garden v2

Modernization of the **original [Kloggy / HA-Irrigation-Version2](https://github.com/kloggy/HA-Irrigation-Version2)** for Home Assistant **2026.10.2**. This is a continuation of the original YAML package and Lovelace dashboard, with their entity IDs and control model preserved.

[Polska instrukcja](README_PL.md) · [Installation](docs/INSTALLATION.md) · [INI translations](docs/TRANSLATIONS.md) · [Changes](CHANGELOG.md) · [Validation](docs/TESTING.md)

**Development version.** Back up an existing installation and validate it on virtual valves before migrating physical outputs. Version 2026.10.2 is the verified HA baseline; this is not a claim of compatibility with every future release or every hardware configuration.

Search HA entities by name/ID when assigning valves and sensors, and switch the original panel between light/dark appearance with its header button. [Entity selection and appearance](docs/ENTITY_PICKER_AND_APPEARANCE.md).

[Weather sources and sensor setup](Weather%20Sensors.md#english) · [Optional historical SmartWeather example](SmartWeather%20reference.md)

## Installation through HACS

The default branch is **`main`**. The current release is **`0.3.0b1` (beta)** and includes weather-source diagnostics. Choose the release in HACS; beta visibility may need to be enabled. Release tags preserve earlier versions; `main` tracks current development.

Use this repository as a HACS custom **Integration** repository. The installer delivers the same original engine and EN/PL panel; activation requires one explicit YAML include. Follow the [HACS installation and migration guide](docs/HACS_INSTALLATION.md), including the existing-installation steps. It is not listed in HACS’s default catalog.

## Features

- 1–16 configurable zones, two scheduled cycles and a manual cycle.
- Original UI configuration for valve mappings, zone/cycle names, weekdays, start times, rainfall and temperature sources.
- Updated HA templates and service handling, bounded waits, STOP/Master OFF cleanup, output acknowledgments, watchdog and restart/shutdown cleanup.
- Dynamic zone activity/history, dated rainfall and temperature history, unavailable-source handling and guarded optional dependencies.
- Original Lovelace compiled offline without `lovelace_gen`.
- Replaceable UTF-8 INI catalogs: English and Polish, 283 messages each. Missing translations fall back to English. Languages are selected when building.
- Configurable project-owned notification/logging adapters and a local weather-description proxy replace author-specific external entities. See [optional features and configuration](docs/OPTIONAL_FEATURES.md#english).

## Names

The repository/project is **Irrigation Garden v2**. The installed dashboard is **Irrigation Garden** in English and **Podlewanie Ogrodu** in Polish. The `v2` suffix is not part of the installed display title. Internal `irrigation_*` IDs remain unchanged for compatibility.

## What is included

`Garden Irrigation/` contains the 27 modernized original engine packages; `Logging/` contains the two original logging packages. `lovelace/` contains the 41 original dashboard authoring files. `dist/en/` and `dist/pl/` contain ready-built dashboards; `tools/` contains builders and isolated test fixtures. Use the explicit registry in `installation/packages.yaml` — never load the entire repository as packages.

Install the required custom cards and configure Browser Mod as described in [the installation guide](docs/INSTALLATION.md). Then configure your own valve and weather entities in the dashboard. No personal HA state, credentials, valve mappings, private logs or private screenshots are distributed.

## Build the dashboard

Python 3.10+ with dependencies from `requirements.txt`:

```sh
python -m pip install -r requirements.txt
python tools/build_i18n_release.py --language en --output dist/en
python tools/build_i18n_release.py --language pl --output dist/pl
```

Without options the builder uses `i18n/build.ini` and writes `generated/`. Copy your selected dashboard YAML to the registered filename. Replacing its text does not change watering settings. The sidebar registration title is separate from the translated view title.

## Attribution

Original project and design: **Kloggy**. Modernization reference: **tinkerfish**, `modernization-2026`, upstream PR #103. This development branch is maintained by **[andreasg73](https://github.com/andreasg73)**, who defined requirements and tested the installation. Implementation, analysis and documentation were prepared with assistance from **ChatGPT (OpenAI)**. This does not imply endorsement by OpenAI or by the upstream authors.

See [AUTHORS.md](AUTHORS.md) and [LICENSE_NOTICE.md](LICENSE_NOTICE.md). The original author and history remain credited; this branch does not claim that the original project was created by its maintainer or by AI.

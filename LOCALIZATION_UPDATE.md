# Localization update — 24 October 2026

The panel now builds from all 248 EN/PL catalog entries. Complete scheduler messages, work status, output confirmation failures, units, calendar words and cycle-conflict warnings are translated in the presentation layer. The schedule and temperature selectors show translated labels while sending the original canonical options. User-defined cycle and zone names stay unchanged.

This update includes the previously interrupted removal of references to optional entities from the original author's installation. The installed panel has 575 static entity references; all resolve in the checked installation. Unconfigured external data remain unconfigured. No physical output was operated during this continuation.

The replacement helpers and adapters, their exact entity IDs, destination-script contracts and weather-description behavior are documented in [Optional features / Funkcje opcjonalne](docs/OPTIONAL_FEATURES.md). Upgrades must include the updated packages as well as the dashboard; changing only the panel does not install the added helpers or scripts.

Validation: 11 Python contracts, 1330 JavaScript syntax checks, 13 JavaScript behavior cases, generated YAML/JSON equality and live native-loader equality. Active HA 2026.10.2 configuration check is valid and Spook reports no active repairs. These live checks describe one installation; they do not certify another installation or physical commissioning. No new full engine runtime campaign was executed for the earlier optional-adapter edits.

The frozen English baseline in tests/fixtures/stage41-english-before.json records the source state recovered at the start of this continuation. The previous stage37 baseline is retained; its equality check fails against the new optional-feature configuration and selectors, so it is not claimed as a regression pass for that changed source structure.

The wider interaction-audit coverage map, testing on a physical phone and physical valve commissioning remain separate work. Backend logs, notification bodies and arbitrary external weather descriptions retain their source language; internal technical values remain canonical.

The rain-schedule checkbox now has an explicit catalog label in both states, rather than inheriting an English entity name. Polish: “Pomijaj harmonogramy podczas deszczu”. Long labels wrap on small screens. The new stage41 baseline and focused regression check cover this display-only change.

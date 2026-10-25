# INI translations / Tłumaczenia INI

Project name: **Irrigation Garden v2**. Installed English name: **Irrigation Garden**. Installed Polish name: **Podlewanie Ogrodu**. The display names are catalog entries; no `v2` is appended in HA.

EN and PL have 283 messages each. For manual installation the language is selected at build time; the HACS assistant selects the bundled EN/PL dashboard in its setup/options flow. It does not switch automatically per HA user. Native HA dialog controls use the HA profile language; canonical helper options such as `Use Forecast`, backend messages and dynamic Jinja values may remain English.

## Build / Budowanie

```sh
python -m pip install -r requirements.txt
python tools/build_i18n_release.py --language en --output dist/en
python tools/build_i18n_release.py --language pl --output dist/pl
```

Without `--language` the builder uses `i18n/build.ini`; default output is `generated/`. Copy only the selected `irrigation_dashboard.yaml` over your registered dashboard filename. The JSON is an equivalent inspectable config, not an HA automation package. This does not write helper values, durations, mappings or schedules.

## Add a language / Dodawanie języka

1. Copy `i18n/en.ini` to e.g. `i18n/de.ini`.
2. Set `language = de` and an appropriate `native_name` in `[meta]`. Retain `fallback = en`, `format = 1`.
3. Translate values under `[messages]`; retain the keys. Values are **JSON strings within INI**: keep double quotes, use `\n` for newlines and `\"` for quotes. Save UTF-8; BOM is supported. Preserve HTML tags, technical identifiers and units.
4. Run `python tools/build_i18n_release.py --language de`.

No Python edits are needed. Missing keys fall back to English; an empty string is intentional. Unknown keys, changed markup, invalid JSON values and template injection are rejected. A missing language file is an error.

Tłumaczone są napisy, pomoc i domyślne wyświetlane nazwy stref/cykli. Własne nazwy użytkownika pozostają zachowane. Wewnętrzne identyfikatory, opcje, warunki i wywołania usług nie są tłumaczone.

After changing source wording, back up catalogs, run `python tools/build_i18n_release.py --extract`, review the new English keys and reconcile translations. Run both language builds and the tests before deploying.

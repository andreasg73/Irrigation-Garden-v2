# Irrigation Garden v2 — development, 2026-10-24

Based on original Kloggy HA-Irrigation-Version2, master `532f01b5e`, incorporating a modernization reference from tinkerfish PR #103 and subsequent changes.

- HA 2026.10.2 syntax/schema compatibility; safe defaults for numeric filters and missing attributes.
- STOP/CANCEL and Master OFF stop active execution before closing outputs; manual-zone settings are restored from persistent snapshots.
- Output acknowledgment, bounded waits, active-output snapshots, watchdog and controlled shutdown/restart cleanup. Each service boundary rechecks output permissions.
- Package-owned automations selected by stable IDs, avoiding unrelated automations with similar names.
- Dynamic activity proxies for history, calendar-day history boundaries and dated rainfall/temperature data with missing-source handling.
- Guards for optional notifications, announcements and logging; absent log file no longer causes a read command error.
- Original 41 Lovelace source files compiled offline, with native zone-count conditions and compatibility fixes for current cards/popups.
- UTF-8 INI localization, EN/PL 210 messages each; displayed default names translated while custom names and canonical control values are preserved.
- Wrapping of long translated headings and settings labels.

The new public repository layout uses root-level original source directories, generic installation examples and portable build/test paths. It contains no exported state or valve mappings from the maintainer's HA instance.

Known scope: no physical production migration is demonstrated by publication; isolated tests and a safe live installation check do not guarantee hardware behavior during power loss or communication failure. Native dropdown options and some backend/Jinja values can remain English. Language selection is at build time.

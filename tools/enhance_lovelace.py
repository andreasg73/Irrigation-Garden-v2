"""UI-only adapters around the compiled original dashboard; no engine changes."""
import copy
import re
from localize_lovelace import key_for, read_catalog
from decision_labels import DECISION_LABELS

UI_LABELS = {
    'search': ('Search entities', 'Szukaj encji'),
    'save': ('Save', 'Zapisz'), 'cancel': ('Cancel', 'Anuluj'),
    'clear': ('Clear selection', 'Wyczyść wybór'),
    'none': ('Not configured', 'Nie skonfigurowano'),
    'empty': ('No matching entities', 'Brak pasujących encji'),
    'unavailable': ('Unavailable', 'Niedostępna'),
    'invalid': ('Select an existing compatible entity.', 'Wybierz istniejącą encję odpowiedniego typu.'),
    'failed': ('Save failed. Your previous setting is retained.', 'Zapis nie powiódł się. Poprzednie ustawienie zostało zachowane.'),
    'busy': ('Stop watering and close mapped valves before changing valve assignments.', 'Przed zmianą przypisania zaworu zatrzymaj podlewanie i zamknij przypisane zawory.'),
    'changed': ('This setting changed elsewhere. Reopen the picker before saving.', 'To ustawienie zmieniono w innym miejscu. Otwórz wybór ponownie przed zapisaniem.'),
    'more': ('matching entities — type to narrow the list', 'pasujących encji — wpisz tekst, aby zawęzić listę'),
    'dark': ('Dark mode', 'Tryb ciemny'), 'light': ('Light mode', 'Tryb jasny'),
    'to_dark': ('Switch to dark mode', 'Przełącz na tryb ciemny'),
    'to_light': ('Switch to light mode', 'Przełącz na tryb jasny'),
    'loading': ('Loading…', 'Wczytywanie…'),
    'load_failed': ('Cannot load the original card. Refresh the dashboard.', 'Nie można wczytać oryginalnej karty. Odśwież panel.'),
    'measurement': ('Measurement', 'Pomiar'),
    'forecast': ('Forecast', 'Prognoza'),
    'condition': ('Current conditions', 'Bieżąca pogoda'),
    'healthy': ('Available; value is valid', 'Dostępna; wartość poprawna'),
    'missing_source': ('Assigned entity does not exist', 'Przypisana encja nie istnieje'),
    'missing_helper': ('Mapping helper is unavailable', 'Pomocnik przypisania jest niedostępny'),
    'unknown_value': ('Source has no known value', 'Źródło nie ma znanej wartości'),
    'wrong_unit': ('Wrong unit; expected', 'Niewłaściwa jednostka; wymagana'),
    'wrong_domain': ('Wrong entity type; expected', 'Niewłaściwy typ encji; wymagany'),
    'invalid_value': ('Invalid value', 'Nieprawidłowa wartość'),
    'value': ('Value', 'Wartość'),
    'reported': ('Last report to HA', 'Ostatni raport do HA'),
    'updated': ('State or attributes updated', 'Zmiana wartości lub atrybutów'),
    'checked': ('Report time checked', 'Czas raportu sprawdzono'),
    'refresh': ('Refresh report time', 'Odśwież czas raportu'),
    'report_failed': ('Report time unavailable; retry refresh', 'Czas raportu niedostępny; ponów odświeżanie'),
    'no_report': ('No report timestamp', 'Brak czasu raportu'),
    'report_hint': ('An unchanged value does not indicate failure. HA report time is not the time of a physical measurement or forecast issue.', 'Niezmienna wartość nie oznacza awarii. Czas raportu do HA nie jest czasem pomiaru fizycznego ani wydania prognozy.'),
    'raining_on': ('on = raining; off = dry. Check the sensor polarity.', 'on = pada; off = sucho. Sprawdź polaryzację czujnika.'),
}


def policy(entity):
    """Filter real sources by the original engine's supported domains and units."""
    if re.fullmatch(r'input_text\.irrigation_zone(?:[1-9]|1[0-6])_switch_entity_id', entity):
        return {'domains': ['switch'], 'guard_watering': True}
    if re.fullmatch(r'input_text\.irrigation_cycle[12]_wait_for_entity_name', entity):
        return {'domains': ['*']}
    suffix = entity.removeprefix('input_text.irrigation_')
    if suffix in {'external_sensor_forecast_high_temp', 'external_sensor_current_temp'}:
        return {'domains': ['sensor'], 'units': ['°C']}
    if suffix.startswith('external_sensor_rainfall_') or suffix == 'external_sensor_forecast_rain':
        return {'domains': ['sensor'], 'units': ['mm']}
    if suffix == 'external_sensor_raining_now':
        return {'domains': ['binary_sensor']}
    if suffix == 'external_sensor_weather_outlook':
        return {'domains': ['sensor', 'weather']}
    if re.fullmatch(r'external_sensor_controller_\d+_wifi', suffix):
        return {'domains': ['sensor'], 'units': ['dBm', '%']}
    if suffix in {'notification_script', 'announcement_script'}:
        return {'domains': ['script']}
    if suffix == 'log_notify_entity':
        return {'domains': ['notify']}
    if suffix == 'announcement_player':
        return {'domains': ['media_player']}
    if suffix in {'startup_ready_entity', 'ha_stopping_entity'}:
        return {'domains': ['binary_sensor', 'input_boolean']}
    return None


def weather_kind(entity):
    suffix = entity.removeprefix('input_text.irrigation_external_sensor_')
    if suffix.startswith('forecast_'):
        return 'forecast'
    if suffix == 'weather_outlook':
        return 'condition'
    if suffix.startswith('rainfall_') or suffix in {'raining_now', 'current_temp'}:
        return 'measurement'
    return None


def enhance(data, language, catalog_dir):
    result = copy.deepcopy(data)
    _, catalog = read_catalog(catalog_dir / (language + '.ini'))
    _, english = read_catalog(catalog_dir / 'en.ini')
    labels = {name: catalog.get(key_for(pair[0]), english.get(key_for(pair[0]), pair[0])) for name, pair in UI_LABELS.items()}
    decision_labels = {name: catalog.get(key_for(pair[0]), english.get(key_for(pair[0]), pair[0])) for name, pair in DECISION_LABELS.items()}
    counts = {'picker_rows': 0, 'popup_wrappers': 0, 'section_wrappers': 0}

    def wrapper(card):
        return {'type': 'custom:irrigation-garden-themed-card', 'ui_labels': labels, 'card': card}

    def walk(node):
        if isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict):
            entity = node.get('entity', '')
            filters = policy(entity) if isinstance(entity, str) else None
            if filters and node.get('type') in {None, 'entity'}:
                node.update(type='custom:irrigation-garden-entity-picker', ui_labels=labels, **filters)
                kind = weather_kind(entity)
                if kind:
                    node['diagnostic_kind'] = kind
                counts['picker_rows'] += 1
            for value in list(node.values()):
                if value is not labels:
                    walk(value)
            popup = node.get('browser_mod')
            if isinstance(popup, dict) and popup.get('service') == 'browser_mod.popup':
                content = popup.get('data', {}).get('content')
                if isinstance(content, dict):
                    popup['data']['content'] = wrapper(content)
                    counts['popup_wrappers'] += 1

    walk(result)
    for view in result['views']:
        for section in view.get('sections', []):
            section['cards'] = [wrapper(card) for card in section.get('cards', [])]
            counts['section_wrappers'] += len(section['cards'])
        view['sections'][0]['cards'].insert(0, {'type': 'custom:irrigation-garden-appearance', 'ui_labels': labels, 'show_decisions': False})
        view['sections'][0]['cards'].insert(1, {'type': 'custom:irrigation-garden-decisions', 'ui_labels': decision_labels})
    return result, counts


def original_structure(data):
    """Remove only the documented UI adapters, for independent legacy parity checks."""
    if isinstance(data, list):
        return [original_structure(v) for v in data if not (isinstance(v, dict) and v.get('type') in {'custom:irrigation-garden-appearance', 'custom:irrigation-garden-decisions'})]
    if not isinstance(data, dict):
        return data
    if data.get('type') == 'custom:irrigation-garden-themed-card':
        return original_structure(data['card'])
    if data.get('type') == 'custom:irrigation-garden-entity-picker':
        return {k: original_structure(v) for k, v in data.items() if k not in {'type', 'ui_labels', 'domains', 'units', 'guard_watering', 'diagnostic_kind'}}
    return {k: original_structure(v) for k, v in data.items()}

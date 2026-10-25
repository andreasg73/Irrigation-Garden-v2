# Entity search and light/dark appearance

## Polski

Panel zachowuje oryginalny układ Kloggy. Nowy moduł interfejsu dodaje wyszukiwanie encji oraz przycisk ☀/☾ nad sekcją stanu.

**Wybór encji:** kliknij pole przypisania, wyszukaj nazwę lub identyfikator encji, wybierz pozycję i naciśnij **Zapisz**. Samo otwarcie, wpisanie tekstu i wybór pozycji nie zmieniają ustawienia. **Anuluj** pozostawia poprzednią wartość; **Wyczyść wybór → Zapisz** jawnie usuwa przypisanie zgodnie z dotychczasowym zachowaniem pakietów. Lista pokazuje do50 wyników, a wpisanie fragmentu nazwy/ID zawęża wyszukiwanie. Niedostępne encje pozostają oznaczone jako niedostępne.

Filtry odpowiadają silnikowi: zawory `switch`, deszcz teraz `binary_sensor` (także czujnik otwarcia Aqara), temperatura `sensor` w°C, opady `sensor` wmm, sygnał Wi-Fi w dBm lub%. Pola opcjonalnych adapterów dobierają odpowiednio skrypty, odtwarzacze, powiadomienia i pomocniki logiczne. Nazwy stref, odbiorców i czcionek pozostają zwykłymi polami tekstowymi.

Zmiana zaworów jest blokowana podczas podlewania lub przy aktywnym przypisanym wyjściu. Jeśli ustawienie zmieni się w innym miejscu podczas edycji, otwórz listę ponownie. Błąd zapisu pozostawia formularz z Twoim wyborem, aby można było ponowić zapis. Zmiana konfiguracji nie jest testem urządzenia ani potwierdzeniem przepływu wody.

**Wygląd:** przycisk przełącza jasny/ciemny wygląd panelu, wykresów i jego okien ustawień. Wybór jest pamiętany lokalnie w danej przeglądarce dla użytkownika HA. Nie zmienia profilu, motywu innych dashboardów ani ustawień podlewania. Bez zapisanego wyboru panel korzysta z aktualnego trybu HA; gdy przeglądarka blokuje pamięć lokalną, wybór działa do zamknięcia sesji strony.

Od wersji **0.3.0b1** przy przypisanych źródłach pogody widać także diagnostykę wartości, jednostek, dostępności oraz czasu raportu do HA. Niezmienna wartość nie oznacza awarii. [Opis diagnostyki](../Weather%20Sensors.md#polski).

### Instalacja modułu

Przez HACS: po aktualizacji pomocnika do **0.3.0b1** i wymaganym restarcie integracja udostępnia swój moduł i dodaje/aktualizuje tylko własny zasób dashboardu. Następnie przygotuj nowy panel przez opcje integracji zgodnie z [instrukcją HACS](HACS_INSTALLATION.md). Przy zasobach YAML integracja zgłosi w Naprawach dokładny adres modułu do dodania.

Ręcznie: skopiuj `custom_components/irrigation_garden/frontend/irrigation-garden-ui.js` z repozytorium do `/config/www/irrigation-garden/irrigation-garden-ui.js`. Dodaj zasób typu **JavaScript Module**:

```text
/local/irrigation-garden/irrigation-garden-ui.js?v=0.3.0b1
```

Wgraj przebudowany panel EN albo PL i odśwież przeglądarkę/aplikację. Przy kolejnej zmianie pliku zmień także wersję w URL zasobu, żeby ominąć cache. Wbudowane komponenty oryginalnego panelu pozostają wymagane.

### Cofnięcie

Przywróć poprzedni wygenerowany YAML panelu i poprzedni zasób modułu, jeśli istniał. Dopiero po wycofaniu nowego YAML usuń nowy zasób/plik. Sam moduł nie przenosi ani nie usuwa pomocników i mapowań. Nie ma potrzeby restartowania silnika podczas ręcznej aktualizacji samego panelu i jego zasobu.

## English

The original dashboard layout remains intact. Click an entity assignment to search real HA states by friendly name or entity ID. Select a candidate, then **Save**; opening, typing and selecting alone do not write anything. **Cancel** discards the draft. **Clear selection → Save** explicitly clears the existing mapping. At most50 matches are listed; type to narrow them. Unavailable sources are labeled.

Filters match the original engine: switch outputs; binary sensors for current rain, including contact sensors; temperature sensors in°C; rainfall sensors inmm; controller Wi-Fi sensors in dBm/%. Optional adapter fields use their corresponding domains. Zone names, recipient names and font names stay text fields. Valve reassignment is blocked while watering or a mapped output is on. Concurrent edits require reopening the picker; failed requests retain the draft.

The ☀/☾ button changes the irrigation dashboard, charts and its popup content. Its preference is stored in this browser for the HA user and does not change HA's profile/global theme, other dashboards or watering settings. Without a preference it follows HA's current mode. If local storage is blocked, the selection lasts for the current page session.

Version **0.3.0b1** also displays weather-source diagnostics for value/unit validity, availability and actual last reports to HA. Unchanged values do not imply failure. [Diagnostics guide](../Weather%20Sensors.md#english).

HACS assistant **0.3.0b1** serves the module and registers/updates only its owned resource on setup. Prepare the updated dashboard through its options. YAML resource lists require the URL shown in Repairs. For manual installation, copy `custom_components/irrigation_garden/frontend/irrigation-garden-ui.js` into `/config/www/irrigation-garden/`, register `/local/irrigation-garden/irrigation-garden-ui.js?v=0.3.0b1` as a **JavaScript Module**, install the rebuilt EN/PL panel and refresh clients. Bump the resource URL version after future edits.

To roll back, restore the previous generated panel and then remove the newly added resource/file. Mapping helper values remain unchanged. UI validation includes programmatic DOM simulations and native HA schemas/collections; this is not real-phone touch, IME or physical-device certification.

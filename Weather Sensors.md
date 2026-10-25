# Weather sources / Źródła danych pogodowych

[English](#english) · [Polski](#polski) · [Entity picker / Wybór encji](docs/ENTITY_PICKER_AND_APPEARANCE.md)

## English

Irrigation Garden uses **your existing Home Assistant entities**. Configure a weather integration or local sensor first, then assign its entities in the original dashboard. SmartWeather is optional. The project does not automatically install a weather provider, obtain API credentials or create a working rain gauge from the default entity names.

### Assign sources in the dashboard

1. Open **Settings → Temperature** or **Settings → Rainfall** and the source/entity settings for that section. Weather description is under **Settings → General → Notifications and optional features**.
2. Click the assignment field, search by friendly name or full entity ID, select a result and press **Save**. Selecting alone does not save; **Cancel** discards the draft. **Clear selection → Save** clears the mapping; engine initialization may subsequently display `Not set` for an unset weather source.
3. Check the source's state, unit and reporting period in HA, then check the corresponding irrigation reading. The list's domain/unit filter cannot verify that a daily total actually covers the right day or location.

The picker requires the [UI module](docs/ENTITY_PICKER_AND_APPEARANCE.md). Its choices come from `hass.states`; disabled entities without a current state are absent. Unavailable entities can appear with an unavailable label when their domain/unit matches. Selecting one does not make its data valid.

| Input | Required source and meaning | Mapping helper |
|---|---|---|
| Current temperature | `sensor.*`, numeric **°C**, current measurement | `input_text.irrigation_external_sensor_current_temp` |
| Forecast high temperature | `sensor.*`, numeric **°C**, maximum forecast for **today** | `input_text.irrigation_external_sensor_forecast_high_temp` |
| Rain today | `sensor.*`, numeric **mm**, observed total since local midnight | `input_text.irrigation_external_sensor_rainfall_today` |
| Rain yesterday | `sensor.*`, numeric **mm**, observed total for the previous local calendar day | `input_text.irrigation_external_sensor_rainfall_yesterday` |
| Forecast rain | `sensor.*`, numeric **mm**, predicted accumulation; establish its forecast window explicitly | `input_text.irrigation_external_sensor_forecast_rain` |
| Raining now | `binary_sensor.*`, **on = raining/wet**, **off = dry** | `input_text.irrigation_external_sensor_raining_now` |
| Weather description | `sensor.*` or `weather.*`, text state | `input_text.irrigation_external_sensor_weather_outlook` |

Rainfall totals must be nonnegative. The picker requires explicit `°C`/`mm` units; legacy unitless sources accepted by some backend templates will not appear in these lists. Convert and label other units in a separate source before assigning them. A rain rate in `mm/h`, a probability in `%` and a lifetime counter are not a daily total in `mm`.

### Keep measurements and forecasts separate

**Forecast rainfall is not observed rainfall.** Do not assign a next-24-hours forecast to Rain today or Rain yesterday. Likewise, yesterday's calendar total is not the last rolling 24 hours. A provider's total for today is not necessarily a next-24-hours forecast.

The original settings also support rolling observed rainfall: last 24 hours, 24–48, 48–72, 72–96 and 96–120 hours ago. Their helpers are `input_text.irrigation_external_sensor_rainfall_last_twenty_four_hours` and `input_text.irrigation_external_sensor_rainfall_between_24_and_48_hours_ago` through the corresponding later intervals. Each source must cover its exact, nonoverlapping interval in mm. Assign the sources needed by the selected calendar/rolling mode and history length. Do not fill missing measurements with invented zeroes or with forecasts.

The **Forecast rain** input provides a separate forecast reading; assigning it does not make the historical rainfall multiplier use predicted rain. Rainfall and temperature adjustments and “Ignore schedules if it is raining” have their own controls. Configure and verify the relevant sources before enabling these controls. Missing or unavailable data must be investigated, not treated as proof of dry conditions.

A wet/dry sensor, including a suitably adapted contact sensor, can supply **Raining now**. Verify its actual polarity when wet and dry; its HA device class or displayed “open/closed” label alone does not establish the required on/off meaning. It does not measure rainfall quantity.

### Weather providers and display

[OpenWeatherMap in HA](https://www.home-assistant.io/integrations/openweathermap/) is one possible provider. Its available entities depend on configuration and API access. If a forecast is supplied as structured forecast data rather than a numeric sensor, prepare a separate sensor using HA's [`weather.get_forecasts`](https://www.home-assistant.io/integrations/weather/#action-weatherget_forecasts) response and the required date/window, units and missing-data handling. This repository does not bundle a universal provider-specific forecast adapter. Do not sum rain probabilities or call a rate an accumulation.

The project already defines **`sensor.irrigation_weather_outlook`** as a local text proxy. Assign an external description source using its helper; do not create another sensor with the same ID. This proxy mirrors the source state, uses its own icon and shows `Not configured` if the source has no value. It does not copy the author's old multiline forecast template or provider-specific picture assets. Provider text retains its own language. See [optional features](docs/OPTIONAL_FEATURES.md#english).

[SmartWeather reference](SmartWeather%20reference.md) retains the original author's historical example; it is not a required installation step. The [previous Weather Sensors example](https://github.com/andreasg73/Irrigation-Garden-v2/blob/e89fc57dd71918f457dc51fd2904974950b06e91/Weather%20Sensors.md) remains available in Git history for provenance, including its author-specific outlook and day/night examples. It is not the current setup guide.

## Polski

Irrigation Garden korzysta z **istniejących encji Twojego Home Assistanta**. Najpierw skonfiguruj integrację pogodową lub własny czujnik, potem przypisz źródła w panelu. SmartWeather jest opcjonalny. Projekt nie instaluje automatycznie dostawcy pogody, nie uzyskuje kluczy API i nie tworzy działającego deszczomierza z domyślnych nazw encji.

### Przypisywanie źródeł

1. Otwórz **Ustawienia → Temperatura** albo **Ustawienia → Opady**, następnie ustawienia źródeł/encji danej sekcji. Źródło opisu pogody znajduje się w **Ustawienia → Ogólne → Powiadomienia i funkcje opcjonalne**.
2. Kliknij pole przypisania, wyszukaj nazwę lub pełny identyfikator, wybierz encję i naciśnij **Zapisz**. Sam wybór nie zapisuje ustawienia; **Anuluj** odrzuca edycję. **Wyczyść wybór → Zapisz** usuwa przypisanie; automatyczna inicjalizacja silnika może później ustawić dla pustego źródła `Not set`.
3. Sprawdź stan, jednostkę i okres pomiaru źródła w HA, a następnie odczyt w podlewaniu. Filtr listy nie potwierdza, że suma dobowa dotyczy właściwej daty lub lokalizacji.

Lista wymaga [modułu interfejsu](docs/ENTITY_PICKER_AND_APPEARANCE.md). Pokazuje encje obecne w `hass.states`; wyłączone encje bez bieżącego stanu nie występują. Źródło niedostępne może być widoczne z oznaczeniem niedostępności, jeśli pasuje domena i jednostka. Wybranie go nie przywraca pomiarów.

| Wejście | Wymagane źródło i znaczenie | Pomocnik przypisania |
|---|---|---|
| Temperatura bieżąca | `sensor.*`, liczba w **°C**, aktualny pomiar | `input_text.irrigation_external_sensor_current_temp` |
| Prognozowana temperatura maksymalna | `sensor.*`, liczba w **°C**, maksimum prognozowane na **dzisiaj** | `input_text.irrigation_external_sensor_forecast_high_temp` |
| Opady dzisiaj | `sensor.*`, liczba w **mm**, zmierzona suma od lokalnej północy | `input_text.irrigation_external_sensor_rainfall_today` |
| Opady wczoraj | `sensor.*`, liczba w **mm**, zmierzona suma poprzedniej lokalnej doby kalendarzowej | `input_text.irrigation_external_sensor_rainfall_yesterday` |
| Prognoza opadów | `sensor.*`, liczba w **mm**, przewidywana suma dla jawnie określonego okresu | `input_text.irrigation_external_sensor_forecast_rain` |
| Pada teraz | `binary_sensor.*`, **on = pada/mokro**, **off = sucho** | `input_text.irrigation_external_sensor_raining_now` |
| Opis pogody | `sensor.*` lub `weather.*`, stan tekstowy | `input_text.irrigation_external_sensor_weather_outlook` |

Sumy opadów muszą być nieujemne. Lista wymaga jawnej jednostki `°C`/`mm`; starsze źródła bez jednostki, akceptowane przez część szablonów silnika, nie pojawią się w tych filtrach. Inne jednostki trzeba najpierw przeliczyć i oznaczyć w osobnym źródle. Natężenie `mm/h`, prawdopodobieństwo `%` i licznik opadu od początku działania nie są dobową sumą w `mm`.

### Pomiary, prognozy i czujnik deszczu

**Prognoza nie jest pomiarem rzeczywistych opadów.** Prognozy na następne 24 godziny nie przypisuj do opadów dzisiaj ani wczoraj. Suma poprzedniej doby kalendarzowej różni się od ostatnich 24 godzin; prognoza na dzisiaj również nie musi obejmować kolejnych 24 godzin.

Oryginalny panel obsługuje także ruchome okresy pomiaru: ostatnie 24 godziny, 24–48, 48–72, 72–96 oraz 96–120 godzin temu. Pomocniki to `input_text.irrigation_external_sensor_rainfall_last_twenty_four_hours` oraz `input_text.irrigation_external_sensor_rainfall_between_24_and_48_hours_ago` i odpowiednie dalsze przedziały. Źródła mają dotyczyć dokładnie tych rozłącznych okresów i zwracać mm. Uzupełnij dane wymagane przez wybrany tryb kalendarzowy/ruchomy i liczbę dni historii. Braków nie zastępuj wymyślonym zerem ani prognozą.

Pole **Prognoza opadów** dostarcza osobny odczyt prognozy; samo przypisanie nie powoduje używania prognozy przez mnożnik historycznych opadów. Korekty opadowe i temperaturowe oraz **Pomijaj harmonogramy podczas deszczu** mają własne przełączniki. Przed ich włączeniem skonfiguruj i sprawdź odpowiednie źródła. Brak danych lub niedostępność nie potwierdzają, że jest sucho.

Czujnik mokro/sucho, także odpowiednio przystosowany czujnik otwarcia, może obsługiwać **Pada teraz**. Sprawdź rzeczywistą polaryzację w stanie mokrym i suchym: klasa urządzenia lub napis „otwarte/zamknięte” nie potwierdzają znaczenia on/off. Taki czujnik nie podaje ilości deszczu w mm.

### Dostawcy pogody i opis

[OpenWeatherMap w HA](https://www.home-assistant.io/integrations/openweathermap/) jest jednym z możliwych źródeł. Zestaw encji zależy od konfiguracji i dostępu do API. Jeżeli prognoza występuje jako dane strukturalne, zamiast gotowego sensora liczbowego, przygotuj osobny sensor na podstawie odpowiedzi [`weather.get_forecasts`](https://www.home-assistant.io/integrations/weather/#action-weatherget_forecasts), uwzględniając datę/okres, jednostki i brakujące dane. Repozytorium nie dostarcza uniwersalnego adaptera prognoz dla konkretnego dostawcy. Nie sumuj prawdopodobieństw i nie traktuj natężenia jako sumy opadu.

Projekt definiuje już **`sensor.irrigation_weather_outlook`** jako lokalny pośrednik tekstowy. Przypisz zewnętrzne źródło opisu jego pomocnikiem; nie twórz drugiego sensora o tym ID. Pośrednik pokazuje stan źródła, korzysta z własnej ikony i zwraca `Not configured` („Nie skonfigurowano” w polskim panelu), gdy źródło nie ma wartości. Nie kopiuje starego wieloliniowego szablonu autora ani jego prywatnych obrazków. Tekst dostawcy zachowuje swój język. Szczegóły: [funkcje opcjonalne](docs/OPTIONAL_FEATURES.md#polski).

[SmartWeather reference](SmartWeather%20reference.md) pozostaje historycznym przykładem autora, bez obowiązku instalacji. [Poprzedni Weather Sensors.md](https://github.com/andreasg73/Irrigation-Garden-v2/blob/e89fc57dd71918f457dc51fd2904974950b06e91/Weather%20Sensors.md), wraz z przykładem opisu i dnia/nocy, zachowano w historii Git. Aktualną instrukcją jest ten dokument.

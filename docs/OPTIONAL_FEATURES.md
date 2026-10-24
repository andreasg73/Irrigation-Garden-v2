# Optional features / Funkcje opcjonalne

## Polski

### Co zmieniono i dlaczego

Oryginalna konfiguracja odwoływała się do elementów z instalacji autora, np. `script.notify`, nazw odbiorców i zewnętrznego opisu pogody. Na innej instalacji takie odwołania mogły powodować zgłoszenia brakujących encji w Spook.

Zastąpiono te zależności własnymi adapterami projektu i polami konfiguracji. Nie usuwano urządzeń użytkownika ani nie tworzono fikcyjnych pomiarów do ukrywania ostrzeżeń. Nowe pomocniki przechowują ustawienia funkcji opcjonalnych; podstawowe podlewanie nie wymaga skonfigurowania powiadomień, komunikatów głosowych ani dziennika plikowego.

### Gdzie to ustawić

W panelu otwórz **Ustawienia → Ogólne → Powiadomienia i funkcje opcjonalne**. Wpisuj pełne identyfikatory istniejących encji w polach przeznaczonych na encje. Nazwy odbiorców są tekstem interpretowanym przez Twój skrypt powiadomień; same nazwy nie wybierają automatycznie telefonu.

| Pomocnik | Wartość i zastosowanie |
|---|---|
| `input_text.irrigation_notification_script` | Własny `script.*` obsługujący powiadomienia. |
| `input_text.irrigation_notification_user1_name` | Nazwa/klucz pierwszego odbiorcy przekazywany do skryptu. |
| `input_text.irrigation_notification_user2_name` | Nazwa/klucz drugiego odbiorcy przekazywany do skryptu. |
| `input_text.irrigation_log_notify_entity` | Istniejąca encja `notify.*`, skonfigurowana do zapisu do pliku przez integrację File. |
| `input_text.irrigation_announcement_script` | Własny `script.*` obsługujący komunikaty głosowe. |
| `input_text.irrigation_announcement_player` | Istniejąca encja odtwarzacza dla komunikatów. |
| `input_text.irrigation_startup_ready_entity` | Opcjonalne zewnętrzne źródło gotowości po starcie HA. Kontrola ostrzeżeń kontrolera dopuszcza stan `on` lub `unknown`. |
| `input_text.irrigation_ha_stopping_entity` | Opcjonalne źródło zatrzymywania HA. Stan `on` wstrzymuje ostrzeżenie o niedostępnym kontrolerze przy zamykaniu. |
| `input_text.irrigation_external_sensor_weather_outlook` | Istniejące źródło tekstowego opisu pogody. |

Pola nieustawione lub niedostępne nie uruchamiają odpowiednich zewnętrznych adapterów. Włączenie przełącznika powiadomień lub logowania nie wystarcza bez prawidłowego celu. Integrację File, własny skrypt i źródło pogody konfiguruje użytkownik; projekt nie tworzy ich automatycznie.

### Adaptery i opis pogody

- `script.irrigation_notify` przekazuje do skonfigurowanego skryptu dostępne pola: `show`, `tell`, `type`, `title`, `message`, `notification_id`, `mobile_app_tag`. Twój skrypt musi obsłużyć potrzebne mu pola i wybrać właściwą usługę wysyłki. `tell` może być przekazywane małymi literami przez wywołujący kod.
- `script.irrigation_announce` przekazuje `announcement`, `initiated_by`, `media_players` do własnego skryptu komunikatów. Nie jest gotową integracją TTS.
- `script.irrigation_log_message` wysyła `message` do wskazanej encji przez `notify.send_message`. Zapis wymaga również włączenia odpowiedniej funkcji logowania.
- `sensor.irrigation_weather_outlook` jest lokalnym pośrednikiem opisu pogody. Pokazuje stan wskazanego źródła albo `Not configured` (w polskim panelu: „Nie skonfigurowano”). Nie generuje prognozy, nie zastępuje czujnika deszczu i nie jest pomiarem opadów ani temperatury. Tekst zewnętrznego dostawcy zachowuje jego język.

Definicje pomocników, adapterów i sensora znajdują się w [irrigation_notifications.yaml](../Garden%20Irrigation/irrigation_notifications.yaml). Nie są to encje dawnego stanowiska `Kloggy TEST`.

### Aktualizacja i kontrola

Przy aktualizacji istniejącej instalacji uaktualnij zarówno źródła pakietów, jak i gotowy panel lub jego build. Sama wymiana panelu nie tworzy nowych helperów i skryptów. Zachowaj własne ustawienia, sprawdź konfigurację HA i załaduj zaktualizowane pakiety zgodnie z [instrukcją instalacji](INSTALLATION.md).

Po konfiguracji sprawdź, czy wskazane cele istnieją i czy Spook nie zgłasza starych odwołań. Nie ignoruj ostrzeżeń ani nie twórz pustych encji zastępczych. Potwierdzony brak napraw na jednej instalacji nie gwarantuje braku błędów w innej.

## English

Author-specific external references, including `script.notify`, recipient-name entities and the external weather description, were replaced with project-owned adapters and configurable helpers. This avoids requiring the original author's personal integrations. Devices were not removed and fake measurements were not introduced to silence Spook.

Open **Settings → General → Notifications and optional features**. The table above lists the exact helper IDs. Entity fields take existing full entity IDs; recipient fields are routing names interpreted by your own notification script. Unconfigured external adapters are skipped. Basic irrigation does not require these optional notification, announcement or file-logging destinations.

`script.irrigation_notify` forwards available `show`, `tell`, `type`, `title`, `message`, `notification_id` and `mobile_app_tag` variables to your script; some callers lowercase `tell`. `script.irrigation_announce` forwards `announcement`, `initiated_by` and `media_players`. These adapters do not automatically implement mobile notifications or TTS. `script.irrigation_log_message` uses `notify.send_message` with the configured existing File notification entity and a `message` value; the relevant logging option must also be enabled.

`sensor.irrigation_weather_outlook` mirrors the configured source's text or returns `Not configured`. It does not generate forecasts or substitute for rainfall/temperature inputs. External provider text retains its original language. Definitions are in [irrigation_notifications.yaml](../Garden%20Irrigation/irrigation_notifications.yaml); these are not the old `Kloggy TEST` helpers.

When upgrading, update both the packages and the generated dashboard. Replacing only the dashboard does not create the added helpers/scripts. Preserve your settings, validate HA configuration and load the updated packages following [INSTALLATION.md](INSTALLATION.md). Verify each configured destination and investigate stale Spook references rather than suppressing repairs or creating dummy entities.

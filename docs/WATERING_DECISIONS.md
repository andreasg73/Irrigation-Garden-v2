# Watering decisions / Wyjaśnienia podlewania

## Polski

Karta **Dlaczego tak podlewa?** pokazuje ostatnią zapisaną decyzję. Rozwiń
**Historię decyzji**, aby zobaczyć wcześniejsze wpisy z datą, cyklem i strefą.
Pierwsze wpisy pojawią się dopiero przy kolejnej próbie wykonania harmonogramu
lub cyklu. Nie odtwarzamy dawnych decyzji z bieżącej pogody.

Silnik zapisuje przyczyny pominięcia harmonogramu (deszcz, brak potwierdzenia,
że jest sucho, wyłączony harmonogram, zajęty system), oczekiwanie na encję
i przekroczenie czasu oczekiwania. Dla każdej odwiedzonej strefy zapisuje
czas bazowy, czas wybrany przez silnik, włączone korekty opadów i temperatury,
ich mnożniki, limity czasu oraz tryb testowy i blokadę wyjść. Strefy pominięte
przez zerowy czas, dzień tygodnia, korektę do zera lub brak mapowania mają
osobny powód. Błędy potwierdzenia wyjścia i przerwanie cyklu również trafiają
do historii.

To zapis decyzji, a nie potwierdzenie przepływu wody. „Przyjęto cykl”
nie oznacza, że otworzył się zawór. Ręczny cykl 3 zachowuje dotychczasowe
pomijanie korekt pogody i wyboru dni. Blokada wyjść jest oznaczona jako
symulacja; tryb testowy, który zamienia minuty na sekundy, jest osobną opcją.

Mnożnik ×0,8 oznacza zmniejszenie o 20%, a ×1,2 zwiększenie o 20%.
Limity stosuje się po obu mnożnikach, przed skalowaniem testowym i zaokrągleniem.
Brak mnożnika jest pokazywany jako brak danych; zachowany silnik przyjmuje
w takim przypadku zero. Jeśli czas silnika nie zgadza się z obliczeniem na
zapisanych ustawieniach, karta jawnie zgłasza rozbieżność. Nie przypisuje wtedy
jednej pewnej przyczyny.

Dziennik `sensor.irrigation_last_decision` jest czujnikiem szablonowym
wyzwalanym zdarzeniami `irrigation_decision`. Zachowuje ostatnie 64 wpisy
w atrybucie `records` i korzysta z natywnego odtwarzania stanu i atrybutów HA
po zwykłym restarcie. Nie zależy od opcjonalnego logowania do pliku ani
od włączenia Recorder. Nagła utrata zasilania może utracić ostatnie niezapisane
wpisy. Automatyzacja wyłączona w HA nie podejmuje decyzji i nie tworzy wpisu.

### Aktualizacja i cofnięcie

W instalacji ręcznej zaktualizuj cztery pakiety: `irrigation_logging.yaml`,
`irrigation_triggered.yaml`, `irrigation_run_a_cycle.yaml`, `irrigation_cancel.yaml`,
moduł UI i przebudowany panel. Zrób kopię poprzednich plików, sprawdź konfigurację
HA i przeładuj szablony, skrypty oraz automatyzacje przy nieaktywnym podlewaniu.
Zmień wersję w adresie zasobu JavaScript i odśwież klienta.

W HACS pobierz wydanie zawierające tę funkcję, a następnie przygotuj pakiet
w opcjach instalatora zgodnie z instrukcją instalacji. Samo pobranie pomocnika
nie przełącza aktywnych pakietów. Kod rozwojowy ma wersję `0.4.0b1`; istnienie
publicznego wydania o tym numerze sprawdź na liście Releases.

Cofnięcie: przywróć poprzednie cztery pakiety, panel i moduł UI oraz poprzedni
URL zasobu, sprawdź konfigurację i wykonaj te same przeładowania. Nie zmieniaj
przypisań zaworów, źródeł pogody ani harmonogramów. Nie usuwaj pomocników.

## English

**Why this watering decision?** shows the last recorded decision; expand
**Decision history** for earlier entries. The engine captures inputs when it
evaluates a schedule or zone. Later weather changes do not rewrite history.
There is no reconstruction of attempts before this feature was installed.

Records explain rain/dry-state admission, unavailable data, disabled/busy
schedules, entity waits/timeouts, zero durations, weekdays, weather multipliers,
time bounds, testing, blocked outputs, output acknowledgment faults and stops.
The selected duration comes from the existing worker, including its 7200-second
cap. A mismatch with the captured inputs is explicitly reported rather than
given a definitive weather explanation. Manual cycle 3 still ignores weather
adjustments and weekday selection.

The journal records decisions, not measured water flow. Accepted cycles may
still fail before opening an output. Testing-mode time scaling and blocked-output
simulation are separate settings. Disabled HA automations cannot record attempts.

The event-triggered `sensor.irrigation_last_decision` retains 64 snapshots in
`records`, independently of optional file logging and Recorder. Native HA sensor
restoration retains state/attributes across ordinary restarts; sudden power loss
can lose recent unsaved entries.

Manual updates require the four packages listed above, the UI module and rebuilt
dashboard. Back up originals, validate HA configuration and reload templates,
scripts and automations while irrigation is idle. Bump the module resource URL
and refresh clients. HACS users must also prepare the new package using installer
options; downloading the helper does not activate engine changes. Roll back the
same files and resource URL, validate and reload. No settings or mappings need
to be changed.

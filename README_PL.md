# Irrigation Garden v2

Modernizacja **oryginalnego [Kloggy / HA-Irrigation-Version2](https://github.com/kloggy/HA-Irrigation-Version2)** sprawdzona na **Home Assistant 2026.10.2**. Zachowano oryginalne pakiety YAML, panel Lovelace, identyfikatory encji i sposób konfigurowania podlewania. Nie jest to nowa integracja zastępująca projekt Kloggy.

Nazwa projektu na GitHubie: **Irrigation Garden v2**. Po instalacji panel nazywa się **Irrigation Garden** po angielsku albo **Podlewanie Ogrodu** po polsku — bez dopisku v2.

Przypisywanie zaworów i czujników obsługuje wyszukiwanie encji HA po nazwie/ID. Przycisk w panelu przełącza jasny i ciemny wygląd. [Wybór encji i wygląd](docs/ENTITY_PICKER_AND_APPEARANCE.md).

[Źródła pogody i konfiguracja czujników](Weather%20Sensors.md#polski) · [Opcjonalny historyczny przykład SmartWeather](SmartWeather%20reference.md)

## Instalacja przez HACS

Gałąź domyślna to **`main`**. Aktualne wydanie **`0.3.0b1` (beta)** obejmuje także diagnostykę źródeł pogody. W HACS wybierz to wydanie; może być potrzebne wyświetlanie wersji beta. Tagi wydań zachowują wcześniejsze wersje, a `main` zawiera bieżący rozwój.

Repozytorium można dodać w HACS jako **niestandardową integrację**. Instalator dostarcza ten sam silnik i panel EN/PL; aktywacja wymaga jednego wpisu YAML. [Instrukcja HACS i migracji istniejącej instalacji](docs/HACS_INSTALLATION.md#polski). Projekt nie jest w domyślnym katalogu HACS.

## Co zawiera ta wersja

- 27 oryginalnych, zmodernizowanych pakietów silnika, dwa pakiety logowania i 41 źródeł panelu.
- Obsługę 1–16 stref, dwóch harmonogramów i cyklu ręcznego.
- Poprawki zgodności z HA, szablonów, STOP/Master OFF, timerów, potwierdzania wyjść i sprzątania przy restarcie/zatrzymaniu HA.
- Poprawki historii, opadów i temperatury oraz brakujących danych.
- Oryginalny panel budowany bez `lovelace_gen`.
- Wymienne słowniki INI EN/PL po 283 wiadomości, gotowe panele oraz narzędzia i testy.
- Własne, konfigurowalne adaptery powiadomień i logowania oraz lokalny pośrednik opisu pogody, zastępujące odwołania do prywatnych encji autora. [Co dodano i jak to skonfigurować](docs/OPTIONAL_FEATURES.md#polski).

Jest to **wersja rozwojowa**. Zgodność sprawdzono z HA 2026.10.2; nie deklarujemy sprawdzenia każdej przyszłej wersji ani niezawodności każdego sterownika fizycznego. Przed migracją wykonaj kopię i sprawdź działanie na wirtualnych zaworach. Wymagania i pełna instalacja: [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Szybka orientacja

1. Zainstaluj wymagane karty oraz skonfiguruj wpis integracji Browser Mod.
2. Skopiuj repozytorium do `/config/irrigation_garden_v2/`.
3. Dodaj wyłącznie jawny rejestr `installation/packages.yaml` do istniejącej konfiguracji packages, scalając go z własnymi wpisami.
4. Zarejestruj dodatkowy dashboard YAML, korzystając z przykładu w `installation/configuration.example.yaml`.
5. Sprawdź całą konfigurację HA przed restartem. Pierwszy start: Master OFF, wyjścia zablokowane, mapowania nieustawione.
6. W panelu ustaw własną liczbę stref, nazwy, czasy, dni oraz źródła pogody. Najpierw użyj wirtualnych zaworów. Nie uruchamiaj dwóch systemów na tych samych zaworach.

Nie dołączamy prywatnych mapowań, konfiguracji domu, danych logowania, stanów pomocników ani prywatnych zrzutów ekranu. Opcjonalne powiadomienia, pilot i logowanie wymagają dopasowania do własnego HA. Instrukcja tłumaczeń: [docs/TRANSLATIONS.md](docs/TRANSLATIONS.md).

## Autorstwo i pomoc AI

Autorem oryginalnego projektu i panelu jest **Kloggy**. Uwzględniono modernizację **tinkerfish**, gałąź `modernization-2026`, PR #103. Rozwój tej gałęzi, wymagania i testy na własnej instalacji: **andreasg73**. Implementacja, analiza i dokumentacja powstały przy wsparciu **ChatGPT (OpenAI)**. Nie oznacza to oficjalnego wsparcia ani akceptacji ze strony OpenAI lub autorów pierwowzoru.

Szczegóły: [AUTHORS.md](AUTHORS.md), [LICENSE_NOTICE.md](LICENSE_NOTICE.md), [CHANGELOG.md](CHANGELOG.md), [zakres testów](docs/TESTING.md).

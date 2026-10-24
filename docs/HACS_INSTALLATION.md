# Install the original Irrigation Garden through HACS

[Polski](#polski) · [English](#english)

## Polski

### Co instaluje HACS

To **ten sam opublikowany silnik i oryginalny panel** Irrigation Garden v2: 29 pakietów YAML, gotowy panel EN/PL i te same identyfikatory `irrigation_*`. Integracja `irrigation_garden` jest pomocnikiem instalacji. Nie zastępuje silnika innym sterownikiem. Wersja pomocnika: **0.1.0b1**, Home Assistant **2026.10.2 lub nowszy**; testy wykonano na 2026.10.2.

Repozytorium dodaje się jako **niestandardowe repozytorium HACS**, typ **Integration**. Nie jest to deklaracja przyjęcia projektu do domyślnego katalogu HACS. HACS pobiera integrację wraz z kompletnym pakietem silnika i panelu. Jednorazowe włączenie pakietów YAML wymaga wpisu w konfiguracji HA. Nie edytujemy automatycznie `configuration.yaml` ani `.storage`.

### Pierwsza instalacja

1. Wykonaj pełną kopię zapasową Home Assistanta. Na czas instalacji zatrzymaj podlewanie i zamknij zawory.
2. W HACS otwórz menu → **Custom repositories / Niestandardowe repozytoria**. Dodaj `https://github.com/andreasg73/Irrigation-Garden-v2`, typ **Integration**. Pobierz **Irrigation Garden**. Jeśli HACS prosi o restart, wykonaj go przed dodaniem integracji.
3. Zainstaluj i zarejestruj zasoby: **button-card, card-mod, hui-element, config-template-card, mini-graph-card, state-switch**. Zainstaluj **Browser Mod**, dodaj jego integrację i moduł przeglądarki. Szczegóły i sprawdzone wersje: [dependencies.json](../dependencies.json). Samo pobranie Browser Mod nie wystarcza do obsługi okien panelu.
4. **Ustawienia → Urządzenia i usługi → Dodaj integrację → Irrigation Garden**. Wybierz PL albo EN i adres panelu, domyślnie `irrigation-garden`. Adres musi zawierać myślnik. Kreator pokaże wykryte braki zależności i informację o istniejącym podlewaniu. To kontrola obecności zasobów, nie pełny test przeglądarki.
5. Potwierdzenie przygotuje pliki w `/config/irrigation_garden/`. Następnie dodaj **jedną pozycję** do istniejącej mapy `homeassistant.packages`:

   ```yaml
   homeassistant:
     packages:
       irrigation_garden: !include irrigation_garden/package.yaml
   ```

   Nie dodawaj drugiej sekcji `homeassistant` ani `packages`. Jeżeli `packages` korzysta z `!include`, dopisz samą pozycję `irrigation_garden` w tym dołączanym pliku. Przy `!include_dir_named packages` utwórz `packages/irrigation_garden.yaml` z zawartością `!include ../irrigation_garden/package.yaml`. Nie wczytuj całego katalogu repozytorium jako pakietów.
6. Sprawdź konfigurację HA, a dopiero po poprawnym wyniku uruchom HA ponownie. Pakiet rejestruje panel w pasku bocznym; nie dodawaj osobno drugiego panelu. Informacja w Naprawach znika po załadowaniu właściwej wersji pakietu.
7. Ustaw własne encje zaworów i czujników w panelu. Zacznij od krótkich testów ręcznych i sprawdź STOP/Master OFF przed włączeniem harmonogramów.

### Migracja istniejącej instalacji

Zachowaj tę samą instancję HA i identyfikatory encji. Zapisane ustawienia pomocników pozostają powiązane z tymi identyfikatorami; nie usuwaj ich z rejestru encji. Kreator nie kopiuje ustawień do nowych encji ani nie zmienia bieżących wartości.

W kroku 5 **zastąp** dotychczasowe wpisy 29 pakietów podlewania jednym nowym wpisem. Usuń również poprzednią rejestrację tego panelu z `lovelace.dashboards`. Nie wczytuj obu instalacji równocześnie. **Zachowaj inne pakiety, szczególnie osobne adaptery prognozy pogody**, oraz ich źródła i ustawienia. Nie usuwaj encji fizycznych zaworów ESPHome. Nie ma potrzeby ponownego instalowania Irrigation V5.

Przed restartem sprawdź konfigurację, a po restarcie porównaj liczbę stref, mapowania zaworów, harmonogramy oraz źródła pogody. Integracja nie wykrywa automatycznie wszystkich starych wpisów YAML; za ich zastąpienie odpowiada ten krok migracji.

### Aktualizacja i zmiana języka

Aktualizacja w HACS dostarcza nowy pomocnik i archiwum źródeł. Po restarcie wymaganym przez HACS otwórz **Opcje integracji Irrigation Garden** i potwierdź przygotowanie aktualizacji. Możesz też wybrać nowy język panelu. Kreator zapisuje nowy, kompletny katalog wersji, zachowuje poprzedni i na końcu atomowo przełącza plik `package.yaml`. Sprawdź konfigurację i uruchom HA ponownie. Nie stosuj przeładowań pojedynczych domen podczas podlewania.

Przygotowanie plików nie uruchamia zaworów i nie przeładowuje działającego silnika. Obowiązuje normalne zachowanie oryginalnych pakietów przy restarcie HA. Nowa wersja aktywuje się przy kolejnym odczycie YAML, także jeśli restart wykonasz później z innego powodu.

Nie edytuj plików w `irrigation_garden/releases/` ani wskaźnika `package.yaml`: zmodyfikowane zarządzane pliki blokują kolejne przygotowanie, żeby zachować Twoje zmiany. Własne adaptery trzymaj w osobnych pakietach. Brak miejsca lub przerwana operacja pozostawia poprzedni kompletny wskaźnik; ponowienie przygotowania rozpoznaje zapisany poprzedni wskaźnik i może bezpiecznie dokończyć operację. Nie kasuj katalogu instalacji w ciemno.

### Wycofanie i odinstalowanie

Poprzednie katalogi pozostają w `irrigation_garden/releases/`, a kopie starych wskaźników w `irrigation_garden/previous/`. Przy zatrzymanym podlewaniu możesz skierować wpis pakietu bezpośrednio na poprzedni `irrigation_garden/releases/<identyfikator>/package.yaml`, sprawdzić konfigurację i zrestartować HA. Pełna kopia HA pozostaje drogą odtworzenia ustawień.

Usunięcie integracji albo pobrania HACS **nie usuwa aktywnych pakietów, ustawień ani zaworów**. Aby wyłączyć całe podlewanie: zatrzymaj cykle, zamknij zawory, usuń wpis pakietu z konfiguracji, sprawdź konfigurację i zrestartuj HA. Dopiero wtedy usuń pomocnik/HACS i zbędne pliki. Nie usuwaj innych pakietów pogodowych, jeśli korzystają z nich pozostałe części HA.

## English

### What HACS installs

The installer delivers **the same published original engine and dashboard**: 29 YAML packages, compiled EN/PL dashboards and unchanged `irrigation_*` IDs. It is an installation assistant, not a replacement controller. Assistant version **0.1.0b1**, minimum Home Assistant **2026.10.2**; tested on 2026.10.2.

Use this repository as a HACS **custom repository**, category **Integration**. This does not imply acceptance into HACS's default catalog. One explicit YAML package include is required; global configuration and `.storage` are never automatically edited.

### Installation

1. Back up HA, stop irrigation and close mapped valves.
2. HACS → menu → **Custom repositories** → `https://github.com/andreasg73/Irrigation-Garden-v2` → **Integration**. Download **Irrigation Garden**. Restart first if HACS requests it.
3. Install/register **button-card, card-mod, hui-element, config-template-card, mini-graph-card, state-switch**. Install and configure **Browser Mod**, including its integration, popup service and frontend module. See the tested versions in [dependencies.json](../dependencies.json).
4. **Settings → Devices & services → Add integration → Irrigation Garden**. Select EN/PL and a hyphenated dashboard URL, normally `irrigation-garden`. Review missing prerequisites. Presence checks are not a full browser compatibility test.
5. Confirm preparation, then merge this entry into your **existing** `homeassistant.packages` mapping:

   ```yaml
   irrigation_garden: !include irrigation_garden/package.yaml
   ```

   For a new configuration it belongs under `homeassistant:` → `packages:`. For an included packages mapping edit that mapping instead. With `!include_dir_named packages`, create `packages/irrigation_garden.yaml` containing `!include ../irrigation_garden/package.yaml`. Never add duplicate top-level keys or include the whole repository directory.
6. Validate HA configuration, then restart. The package registers its own sidebar dashboard. The Repairs notice clears when the prepared package marker is loaded.
7. Configure your valves/weather sources and test short manual runs, STOP and Master OFF before enabling schedules.

### Existing installation

**Replace** the old 29 irrigation package includes with the new single entry and remove its old `lovelace.dashboards` registration. Never load both installations. Preserve unrelated packages, **especially separate weather forecast adapters**, and physical ESPHome valve entities. Do not delete irrigation helper entities: retaining IDs on the same HA instance allows their stored settings to restore. The wizard does not change running helper values. Review zone count, mappings, schedules and weather sources after restart. Legacy YAML removal is explicit; the wizard cannot discover every configuration layout.

### Updates, rollback and removal

After a HACS update and any requested restart, use the integration's **Options** to prepare the new original packages or change panel language. Preparation retains prior releases and old include pointers, then atomically switches `irrigation_garden/package.yaml`. Validate YAML and restart HA to apply. Preparation itself sends no actuator commands and reloads no running engine. Normal original-package startup behavior still applies on restart; any later HA YAML load can activate the prepared version.

Managed files live outside HACS in `/config/irrigation_garden/`. Do not edit the release files or pointer: edited managed files block further staging. Keep custom adapters in separate packages. An interrupted update leaves a complete old pointer; both the current and previous pointer hashes are recorded so a retry can complete an interrupted replacement without accepting arbitrary edits.

For rollback, with watering stopped, point the packages entry directly at a retained `irrigation_garden/releases/<id>/package.yaml`, validate and restart. Restore the full HA backup if settings recovery is needed. Removing the integration/HACS download alone leaves YAML watering active. To uninstall watering, stop cycles/close valves, remove its package include, validate and restart, then remove the assistant/files. Preserve unrelated weather packages.

### Validation scope

Tests use HA 2026.10.2's real YAML loader, native `check_config` and config/options flow manager. They cover original-source equality, migration state preservation, explicit acknowledgment, active-watering refusal, resource collection loading, language updates, edited-file protection, invalid ZIPs, path/symlink boundaries and interrupted commits. Frontend servers and real devices are not started in flow tests. No claim of a completed HACS download or physical migration on a user's HA instance follows from these local tests.

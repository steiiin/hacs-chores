# HACS Chores

Wiederkehrende Haushaltsaufgaben für Home Assistant mit Einstellungen, vier Entitäten je Aufgabe und zwei mitgelieferten Dashboard-Karten.

**Version 0.1.0 – erste Implementierung, noch keine auf einer echten HA-Instanz freigegebene Version.** Zielversion: Home Assistant 2026.9 oder neuer. Python-Logik und Speicherabläufe sind mit 27 Tests geprüft. Python und JavaScript bestehen die Syntaxprüfungen. Der Browser der Entwicklungsumgebung konnte die lokale Vorschau nicht öffnen; eine visuelle Prüfung sowie die Prüfung der HA-Einrichtung, Entitäten und HACS-Installation stehen noch aus. Die mitgelieferten GitHub-Workflows wurden hier nicht ausgeführt. GitHub-Metadaten vor einer HACS-Installation ausfüllen.

## Reicht ein GitHub-Repository?

Ja, **ein öffentliches GitHub-Repository mit dem korrekten Inhalt** reicht für die Verteilung als benutzerdefiniertes HACS-Repository. HACS ist der Installations- und Aktualisierungsweg; die eigentliche Funktion läuft als Home-Assistant-Integration. Dieses Projekt bündelt Integration und Karten in einem Repository, das in HACS als **Integration** hinzugefügt wird.

Benötigt werden insbesondere eine Beschreibung und Topics im GitHub-Repository, eine Nutzungsanleitung, `hacs.json` und `custom_components/hacs_chores/` mit Implementierung und `manifest.json`. Das Integrationsmanifest enthält unter anderem Domain, Name, Version, Dokumentation, Issue-Tracker und Codeowners. Ein `brand/`-Ordner mit Icon ist enthalten. Siehe [HACS allgemein](https://www.hacs.xyz/docs/publish/start/) und [Anforderungen an Integrationen](https://www.hacs.xyz/docs/publish/integration/).

Für die manuelle Aufnahme als benutzerdefiniertes Repository ist keine vorherige Aufnahme in den HACS-Standardkatalog nötig. Ein GitHub-Release ist für diesen Weg empfohlen, aber optional. Für den Standardkatalog sind zusätzlich erfolgreiche HACS- und Hassfest-Prüfungen, ein Release und die Einreichung bei `hacs/default` vorgesehen: [HACS-Standardkatalog](https://www.hacs.xyz/docs/publish/include/).

## Funktionen

- Aufgaben und Mitglieder unter **Einstellungen → Geräte & Dienste → HACS Chores → Konfigurieren** erstellen, bearbeiten und löschen.
- Aufgabe: Kategorie, Titel, ausführliche Beschreibung, Wiederholung, Priorität, geschätzter Aufwand in Minuten und Aktivierung/Pause.
- Mitglied: Name, Farbe `#RRGGBB`, Aktivierung/Pause. Identitäten bleiben bei Umbenennungen stabil.
- Pro Aufgabe ein virtuelles Gerät mit einem Fälligkeitssensor und drei weiteren Sensoren.
- Übersicht mit anpassbarer Breite, unterschiedlich hohen Kacheln im CSS-Grid, Kategorieauswahl und optionaler Beschränkung auf fällige Aufgaben.
- Antippen öffnet Beschreibung und Mitgliederauswahl. Erfolgreiches Abhaken löst eine kurze Animation aus; die Aufgabe wechselt zu ihrem nächsten Termin. Nicht fällige Aufgaben zeigen ihre Informationen, können aber noch nicht erledigt werden.
- Rückgängig für die zuletzt gebuchte Erledigung einer Aufgabe innerhalb von zehn Minuten, sofern der Terminplan nicht zwischenzeitlich geändert wurde.
- Statistik über die letzten **14 × 24 Stunden**, mit Aufwand, Anzahl, Anteil am Gesamtaufwand und häufigsten Aufgaben je Mitglied.
- Verlauf in Home Assistants persistentem Speicher. Die Statistik benötigt keine Recorder-Historie.
- Abgesicherte Doppelbuchung: Jede Erledigung muss den zuvor angezeigten Fälligkeitstermin mitliefern. Veraltete Klicks werden abgelehnt. Änderungen werden vor der Bestätigung gespeichert; bei Speicherfehlern wird der In-Memory-Zustand zurückgesetzt.
- Lokaler Betrieb ohne zusätzliches Docker-Image, externen Dienst, CDN oder JavaScript-Buildschritt.

Die erste Oberfläche ist auf Deutsch ausgelegt. Es gibt englische Grundtexte für die Einrichtung; Auswahlbeschriftungen und Karten sind noch nicht vollständig mehrsprachig.

## Terminregeln

| Auswahl | Beispiel | Verhalten |
| --- | --- | --- |
| Alle N Tage, fester Kalender | Täglich; alle drei Tage | Am Startdatum verankert, jeweils zur gewählten Uhrzeit |
| Bestimmte Wochentage | Jeden Dienstag; Montag und Donnerstag | Auswahl eines oder mehrerer Wochentage |
| Monatlich an einem Tag | Am 15. jedes Monats | Tage 29–31 werden in kürzeren Monaten auf den letzten Tag gesetzt |
| Monatlich an einem Wochentag | Jeden letzten Freitag | Erster, zweiter, dritter, vierter oder letzter Wochentag im Monat |
| N Tage nach Erledigung | Drei Tage nach dem Saugen | Datum der tatsächlichen Erledigung plus N Kalendertage, zur gewählten Uhrzeit |

Das Startdatum ist der erste mögliche Kalendertag. Bei einem wöchentlichen Plan wird der erste gewählte Wochentag ab diesem Datum verwendet. Liegt der erste Termin schon in der Vergangenheit, ist die Aufgabe sofort fällig.

**Festgelegte Standardregeln:**

1. Eine versäumte Aufgabe bleibt einmal offen. Es werden keine separaten Rückstände für jeden verpassten Tag angelegt.
2. Feste Termine bleiben am Kalender ausgerichtet. Wird eine Dienstagsaufgabe am Mittwoch erledigt, ist der nächste Termin wieder Dienstag.
3. Nach dem Erledigen wird der nächste Termin strikt nach der Erledigungszeit gewählt. Bei fester Wiederholung werden zwischenzeitlich versäumte Wiederholungen übersprungen.
4. Fälligkeit wird alle 30 Sekunden und unmittelbar nach Erledigungen aktualisiert. Home Assistants konfigurierte Zeitzone ist maßgeblich, nicht die Zeitzone des Browsers.
5. Die Zeitumstellung erhält die lokale Uhrzeit. Eine nicht vorhandene Uhrzeit im Frühjahr wird um die Zeitlücke nach hinten verschoben; eine doppelte Uhrzeit im Herbst wird einmal, beim ersten Auftreten, verwendet.
6. Änderungen des Terminplans berechnen die Fälligkeit ab dem heutigen lokalen Tagesbeginn neu. Titel, Kategorie, Priorität und Aufwand ändern einen bestehenden Termin nicht.
7. Pausierte Aufgaben bleiben gespeichert, sind nicht fällig und werden in der Übersicht ausgeblendet. Beim Wiederaktivieren kann der alte Termin überfällig sein.
8. Sortierung: Fälligkeit aufsteigend; bei exakt gleichem Zeitpunkt Priorität absteigend; anschließend Titel. Priorität: Niedrig, Normal, Hoch, Dringend.

Freie RRULE-Eingabe, jährliche Termine, Feiertagsausnahmen und der fünfte Wochentag eines Monats sind in dieser ersten Version nicht enthalten. Die Beispiele „täglich“, „jeden Dienstag“ und „letzter Freitag im Monat“ sind vollständig in der Terminlogik implementiert.

## Installation zum Testen

1. `custom_components/hacs_chores` in das Home-Assistant-Konfigurationsverzeichnis kopieren. Das Ergebnis muss `<config>/custom_components/hacs_chores/manifest.json` enthalten.
2. Home Assistant neu starten.
3. **Einstellungen → Geräte & Dienste → Integration hinzufügen → HACS Chores**.
4. Über **Konfigurieren** zuerst Mitglieder, dann Aufgaben hinzufügen. Jede Speicherung schließt den Dialog und lädt die Integration neu; für weitere Einträge den Dialog erneut öffnen.
5. Die folgende JavaScript-Ressource einmal hinzufügen. Die Ressource wird von der Integration bereitgestellt, aber nicht automatisch in die Dashboard-Ressourcen eingetragen.

**Dashboard im Speichermodus:** Unter **Einstellungen → Dashboards → Ressourcen** eine Ressource vom Typ **JavaScript-Modul** hinzufügen. Falls der Menüpunkt fehlt, den erweiterten Modus im Benutzerprofil aktivieren:

```text
/hacs_chores/chores-cards.js?v=0.1.0
```

**Ressourcen im YAML-Modus:** In die bestehende Lovelace-Konfiguration integrieren, keinen zweiten `lovelace:`-Block anlegen:

```yaml
lovelace:
  resource_mode: yaml
  resources:
    - url: /hacs_chores/chores-cards.js?v=0.1.0
      type: module
```

Siehe [Home Assistant: Dashboard-Ressourcen](https://www.home-assistant.io/dashboards/dashboards/#resources).

6. Browser neu laden. Die beiden Karten können über die benutzerdefinierten Karten oder manuell per YAML eingefügt werden:

```yaml
type: custom:hacs-chores-card
title: Unser Haushalt
```

```yaml
type: custom:hacs-chores-stats-card
title: Unser Einsatz
```

Optionale Konfiguration der Aufgabenkarte:

```yaml
type: custom:hacs-chores-card
title: Jetzt zu tun
due_only: true
category: Putzen
```

Ohne `due_only` zeigt die Karte alle aktiven Aufgaben einschließlich zukünftiger Termine. Ohne `category` startet sie mit allen Kategorien. Die Kategorie kann in der Karte gewechselt werden. In einem schmalen Dashboard-Bereich ergibt sich eine Spalte; für mehrere Kacheln nebeneinander einen breiteren Abschnitt verwenden. Ein eigener visueller Konfigurationseditor für die Karten ist noch nicht enthalten.

## Veröffentlichung über HACS

Ein GitHub-Repository wurde in dieser Sitzung **nicht erstellt oder veröffentlicht**.

1. Ein öffentliches Repository anlegen, z. B. `hacs-chores`, mit Beschreibung, aktivierten Issues und Topics wie `home-assistant`, `hacs` und `chores`.
2. Im Projektverzeichnis den echten GitHub-Namen einsetzen:

   ```sh
   python scripts/configure_repository.py DEIN_GITHUB_NAME/hacs-chores
   ```

   Das Skript ersetzt `REPLACE_OWNER` in Dokumentation und Issue-Tracker und setzt `codeowners`. Solange diese Platzhalter vorhanden sind, ist dies ein Quellcodepaket, noch kein fertiges HACS-Repository. Bei einem Organisationsrepository `codeowners` gegebenenfalls anschließend auf den tatsächlichen Betreuer bzw. ein GitHub-Team setzen.

3. Den Inhalt dieses Verzeichnisses in die Wurzel des Repositorys übertragen. `custom_components` muss direkt auf der obersten Ebene liegen.
4. Die mitgelieferten GitHub-Workflows prüfen. HACS benötigt die tatsächlichen Repository-Metadaten; eventuell gemeldete Fehler vor Veröffentlichung beheben.
5. Nach einem erfolgreichen Test auf einer separaten HA-Instanz ein Release `v0.1.0` erstellen. Bei späteren Releases Manifest-Version und Ressourcen-URL entsprechend erhöhen.
6. In HACS das Repository unter **Benutzerdefinierte Repositories**, Typ **Integration**, hinzufügen und installieren. Danach gelten die oben beschriebenen Schritte für Neustart, Einrichtung und Dashboard-Ressource.

Das ZIP ist ein vollständiges **Repository-Quellcodepaket**, kein eigens konfiguriertes HACS-`zip_release`. HACS installiert die Dateien aus `custom_components/hacs_chores/` des Repositorys. Ein zweites Repository für die Karten ist nicht erforderlich.

## Entitäten und Aktionen

Die Hierarchie in der Oberfläche ist **HACS Chores → Staubsaugen (Wohnzimmer) → Entität**. Entitäts-IDs selbst sind flach. Bei der ersten Erstellung sind beispielsweise folgende IDs zu erwarten; Home Assistant kann bei Namenskonflikten Ziffern ergänzen, und Benutzer können IDs umbenennen.

| Information | Beispiel-ID | Zustand |
| --- | --- | --- |
| Fällig | `binary_sensor.staubsaugen_wohnzimmer_is_due` | `on` / `off` |
| Nächster offener Termin | `sensor.staubsaugen_wohnzimmer_next_due` | Zeitstempel |
| Zuletzt erledigt | `sensor.staubsaugen_wohnzimmer_last_completed` | Zeitstempel; anfangs unbekannt |
| Zuletzt erledigt von | `sensor.staubsaugen_wohnzimmer_last_completed_by` | Name; anfangs unbekannt |

Bei Überfälligkeit bleibt `next_due` der noch offene Termin in der Vergangenheit. Erst eine Erledigung verschiebt ihn zum nächsten Termin. Die Entitätsattribute enthalten unter anderem stabile `task_id`, Kategorie, Priorität, Aufwand und `due_at`.

Die Aktion `hacs_chores.complete` erwartet `task_id`, `member_id` und den **unveränderten** `due_at`-Wert aus den Sensorattributen. Die Karten liefern diese Werte automatisch. Die Mitglieds-ID steht nach einer Erledigung im Attribut `member_id`; für Automationen ist sie außerdem über die authentifizierte Snapshot-Schnittstelle verfügbar. `hacs_chores.undo` erwartet eine `completion_id`, die der WebSocket-Abschluss zurückgibt.

Beispiel für eine Fälligkeitsautomation, deren Aktion an den eigenen Haushalt angepasst werden kann:

```yaml
alias: Wohnzimmer saugen ist fällig
triggers:
  - trigger: state
    entity_id: binary_sensor.staubsaugen_wohnzimmer_is_due
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      title: Haushalt
      message: Das Wohnzimmer muss gesaugt werden.
```

## Statistik und Speicherung

„Aufwand“ ist hier die Summe der bei jeder Erledigung hinterlegten Minuten. Es findet keine tatsächliche Zeitmessung statt. Eine Aufgabe mit 20 Minuten zählt daher viermal so viel zum Aufwandsanteil wie eine Aufgabe mit fünf Minuten. Zusätzlich zeigt die Statistik die Anzahl der Erledigungen und die häufigsten Aufgaben, sortiert nach Häufigkeit.

Jede Erledigung speichert Aufgaben-ID, Mitglieds-ID, Zeitpunkt, zugehörigen Fälligkeitstermin sowie damaligen Titel, Kategorie, Name, Farbe und Aufwand. Eine spätere Aufwandänderung verändert vergangene Erledigungen nicht. Gelöschte oder deaktivierte Mitglieder mit Aktivität im Zeitfenster erscheinen weiterhin in der Statistik, als inaktiv markiert. Gelöschte Aufgaben bleiben im Verlauf nachvollziehbar. Ein Rückgängig-Ereignis entfernt den Beitrag aus der Statistik und stellt den vorherigen Fälligkeitstermin wieder her.

Aufgaben und Mitglieder liegen in den Optionen des HA-Konfigurationseintrags. Fälligkeiten und vollständiger Erledigungsverlauf liegen in `.storage/hacs_chores.<entry_id>`. Der Verlauf wird in dieser Version nicht automatisch gekürzt. Vollständige Sicherungen des HA-Konfigurationsverzeichnisses schließen diese Dateien ein. Das Entfernen der gesamten Integration löscht ihren eigenen Verlaufsspeicher.

Ein Haushalt pro HA-Instanz. Die Mitglieder sind frei wählbare Namen für das gemeinsame Dashboard und keine Benutzerkonten. Jeder authentifizierte HA-Benutzer mit Zugriff auf die Karten kann für jedes aktive Mitglied abhaken. Der angemeldete HA-Benutzer wird separat im Verlauf hinterlegt. Die Konfiguration läuft über Home Assistants Integrationseinstellungen. Eigene Rollen, PIN-Abfragen, Zuweisungen, Belohnungen und Freigabeabläufe sind nicht Bestandteil dieser Version.

## Entwicklung und offene Integrationsprüfung

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components
node --check custom_components/hacs_chores/frontend/chores-cards.js
```

Die Tests benötigen nur die Python-Standardbibliothek und Zeitzonendaten. Unter Windows bei Bedarf `tzdata` installieren. Die Tests für Speicherfehler und parallele Erledigungen verwenden den echten Coordinator-Mutationscode mit kleinen Ersatzobjekten an den HA-Grenzen; sie ersetzen keinen Test auf einer HA-Instanz.

Lokale Karten-Vorschau mit fiktiven Daten:

```sh
python -m http.server 8765 --bind 127.0.0.1
```

Anschließend im eigenen Browser `http://127.0.0.1:8765/tests/preview.html` öffnen. Die Vorschau verwendet die tatsächlich mitgelieferte Kartendatei. Sie bietet eine 375-Pixel-Ansicht, Themewechsel und einen simulierten Speicherfehler. Alle Änderungen erfolgen nur in den Beispieldaten im Browser; diese Seite ist kein HA-Backendtest.

Vor einem als stabil bezeichneten Release auf einer HA-Testinstanz prüfen:

- Einrichtung, Hinzufügen/Bearbeiten/Löschen, Neuladen und korrekte Registrierung aller vier Entitäten.
- Karten im Dashboard, Browser/Companion-App, unterschiedliche Breiten und Themes, Tastaturbedienung und Dialoge.
- Abhaken auf zwei Geräten, Fehleranzeige, Rückgängig und Live-Aktualisierung beider Karten.
- HA-Neustart mit einer offenen bzw. gerade erledigten Aufgabe und Wiederherstellung einer Sicherung.
- Installation und Update über das konkrete HACS-Repository sowie beide GitHub-Validierungen.

## Technische Quellen

- [Home Assistant: Integrationsmanifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant: Options Flow](https://developers.home-assistant.io/docs/core/integration/options_flow/)
- [Home Assistant: Custom Cards](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/)
- [Home Assistant: WebSocket-Erweiterungen](https://developers.home-assistant.io/docs/frontend/extending/websocket-api/)
- [Home Assistant: asynchrone statische HTTP-Pfade](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/)
- [Home Assistant: lokale Brand-Dateien](https://developers.home-assistant.io/docs/creating_integration_file_structure/)

Stand der Prüfung: 11. September 2026. Das Paket enthält eine ursprüngliche Implementierung für den beschriebenen Haushalt, keine Kopie eines bestehenden Chores-Projekts.

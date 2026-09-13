# HACS Chores

Wiederkehrende Haushaltsaufgaben für Home Assistant mit Einstellungen, vier Entitäten je Aufgabe und drei mitgelieferten Dashboard-Karten.

**Version 0.2.1 – noch keine auf einer echten HA-Instanz freigegebene Version.** Zielversion: Home Assistant 2026.9 oder neuer. Python-Logik und Speicherabläufe sind mit 29 Tests geprüft. Python und JavaScript bestehen die Syntaxprüfungen; die lokale Kartenvorschau wurde breit und schmal visuell geprüft. Die Prüfung der HA-Einrichtung, Entitäten und HACS-Installation steht noch aus. Die mitgelieferten GitHub-Workflows wurden hier nicht ausgeführt. GitHub-Metadaten vor einer HACS-Installation ausfüllen.

## Reicht ein GitHub-Repository?

Ja, **ein öffentliches GitHub-Repository mit dem korrekten Inhalt** reicht für die Verteilung als benutzerdefiniertes HACS-Repository. HACS ist der Installations- und Aktualisierungsweg; die eigentliche Funktion läuft als Home-Assistant-Integration. Dieses Projekt bündelt Integration und Karten in einem Repository, das in HACS als **Integration** hinzugefügt wird.

Benötigt werden insbesondere eine Beschreibung und Topics im GitHub-Repository, eine Nutzungsanleitung, `hacs.json` und `custom_components/hacs_chores/` mit Implementierung und `manifest.json`. Das Integrationsmanifest enthält unter anderem Domain, Name, Version, Dokumentation, Issue-Tracker und Codeowners. Ein `brand/`-Ordner mit Icon ist enthalten. Siehe [HACS allgemein](https://www.hacs.xyz/docs/publish/start/) und [Anforderungen an Integrationen](https://www.hacs.xyz/docs/publish/integration/).

Für die manuelle Aufnahme als benutzerdefiniertes Repository ist keine vorherige Aufnahme in den HACS-Standardkatalog nötig. Ein GitHub-Release ist für diesen Weg empfohlen, aber optional. Für den Standardkatalog sind zusätzlich erfolgreiche HACS- und Hassfest-Prüfungen, ein Release und die Einreichung bei `hacs/default` vorgesehen: [HACS-Standardkatalog](https://www.hacs.xyz/docs/publish/include/).

## Funktionen

- Aufgaben und Mitglieder unter **Einstellungen → Geräte & Dienste → HACS Chores → Konfigurieren** erstellen, bearbeiten und löschen.
- Aufgabe: Kategorie, Titel, ausführliche Beschreibung, Wiederholung, Priorität, geschätzter Aufwand in Minuten, Aktivierung/Pause und optional „Bei Bedarf erledigen lassen“.
- Mitglied: Name, Farbe `#RRGGBB`, Aktivierung/Pause. Identitäten bleiben bei Umbenennungen stabil.
- Pro Aufgabe ein virtuelles Gerät mit einem Fälligkeitssensor und drei weiteren Sensoren; zusätzlich zwei haushaltsweite Entitäten für die Anzahl offener Aufgaben und deren Verfügbarkeit als Binärwert.
- Automatisch geladene Dashboard-Karten; keine manuelle JavaScript-Ressource erforderlich.
- Übersicht mit anpassbarer Breite, unterschiedlich hohen Kacheln im CSS-Grid, Kategorieauswahl und optionaler Beschränkung auf fällige Aufgaben.
- Kompaktkarte mit ein bis vier Rasterzeilen, Navigation zur Aufgabenansicht und einer konfigurierbaren Anzahl direkt abhakbarer Aufgaben. Ohne aktuell erledigbare Aufgaben wird sie gedimmt und deaktiviert.
- Antippen öffnet Beschreibung und Mitgliederauswahl. Erfolgreiches Abhaken löst eine kurze Animation aus; die Aufgabe wechselt zu ihrem nächsten Termin. Nicht fällige Aufgaben können nur erledigt werden, wenn „Bei Bedarf erledigen lassen“ aktiviert ist.
- Rückgängig für die zuletzt gebuchte Erledigung einer Aufgabe innerhalb von zehn Minuten, sofern der Terminplan nicht zwischenzeitlich geändert wurde.
- Statistik über die letzten **14 × 24 Stunden**, mit Aufwand, Anzahl, Anteil am Gesamtaufwand und häufigsten Aufgaben je Mitglied.
- Verlauf in Home Assistants persistentem Speicher. Die Statistik benötigt keine Recorder-Historie.
- Abgesicherte Doppelbuchung: Jede Erledigung muss den zuvor angezeigten Fälligkeitstermin mitliefern. Veraltete Klicks werden abgelehnt. Änderungen werden vor der Bestätigung gespeichert; bei Speicherfehlern wird der In-Memory-Zustand zurückgesetzt.
- Lokaler Betrieb ohne zusätzliches Docker-Image, externen Dienst, CDN oder JavaScript-Buildschritt.

Die erste Oberfläche ist auf Deutsch ausgelegt. Es gibt englische Grundtexte für die Einrichtung; Auswahlbeschriftungen und Karten sind noch nicht vollständig mehrsprachig.

## Dashboard-Karten

Nach dem Einrichten der Integration erscheinen **HACS Chores – Aufgaben**, **HACS Chores – Kompakt** und **HACS Chores – Statistik** automatisch im Dashboard-Karteneditor. Die Integration lädt das mitgelieferte JavaScript selbst; unter **Einstellungen → Dashboards → Ressourcen** ist kein manueller Eintrag nötig.

Die Karten können alternativ direkt per YAML eingefügt werden:

```yaml
type: custom:hacs-chores-card
title: Unser Haushalt
```

```yaml
type: custom:hacs-chores-stats-card
title: Unser Einsatz
```

Die Kompaktkarte lässt sich in einer Abschnittsansicht auf ein bis vier Rasterzeilen skalieren. Ein Klick auf die Kartenfläche navigiert zu `navigation_path`; die kleinen Aufgabenkarten öffnen direkt die Auswahl „Wer hat die Aufgabe erledigt?“.

```yaml
type: custom:hacs-chores-quick-card
title: Aufgaben
navigation_path: /lovelace/chores
max_tasks: 3
```

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
9. Bei „Bei Bedarf erledigen lassen“ kann eine Aufgabe auch vor ihrem Termin abgehakt werden. Nach jeder Erledigung ist dieselbe Aufgabe 30 Minuten lang gesperrt, um versehentliche Doppelbuchungen zu verhindern.

Freie RRULE-Eingabe, jährliche Termine, Feiertagsausnahmen und der fünfte Wochentag eines Monats sind in dieser ersten Version nicht enthalten. Die Beispiele „täglich“, „jeden Dienstag“ und „letzter Freitag im Monat“ sind vollständig in der Terminlogik implementiert.

## Entitäten und Aktionen

Die Hierarchie in der Oberfläche ist **HACS Chores → Staubsaugen (Wohnzimmer) → Entität**. Entitäts-IDs selbst sind flach. Bei der ersten Erstellung sind beispielsweise folgende IDs zu erwarten; Home Assistant kann bei Namenskonflikten Ziffern ergänzen, und Benutzer können IDs umbenennen.

| Information | Beispiel-ID | Zustand |
| --- | --- | --- |
| Fällig | `binary_sensor.staubsaugen_wohnzimmer_is_due` | `on` / `off` |
| Nächster offener Termin | `sensor.staubsaugen_wohnzimmer_next_due` | Zeitstempel |
| Zuletzt erledigt | `sensor.staubsaugen_wohnzimmer_last_completed` | Zeitstempel; anfangs unbekannt |
| Zuletzt erledigt von | `sensor.staubsaugen_wohnzimmer_last_completed_by` | Name; anfangs unbekannt |

Zusätzlich stellt das zentrale Gerät **HACS Chores** zwei haushaltsweite Entitäten bereit:

| Information | Erwartete ID | Zustand |
| --- | --- | --- |
| Offene Aufgaben | `sensor.hacs_chores_open_chores` | Anzahl der aktuell erledigbaren Aufgaben |
| Aufgaben zu erledigen | `binary_sensor.hacs_chores_chores_to_do` | `on`, sobald mindestens eine Aufgabe erledigbar ist; sonst `off` |

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

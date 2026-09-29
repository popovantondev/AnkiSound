# Änderungen

## 3.4.11

- Die App-Grafik wird auch auf GitHub Pages und in den herunterladbaren Anleitungen korrekt angezeigt. Screenshots der Anleitung enthalten keine macOS-Aufnahmesteuerung mehr.

## 3.4.10

- Build-Nummer und Symbolressource folgen der App-Version. Ein neuer App-Pfad ermöglicht die Prüfung ohne den alten Symbolcache.

## 3.4.9

- Das Dock-Symbol wird nicht mehr zur Laufzeit ersetzt; macOS verwendet vom Start bis zum Ende ausschließlich AppIcon.icns.

## 3.4.8

- Eine dauerhafte eindeutige Bundle-ID verhindert, dass macOS beim Schließen eine alte Testkopie mit veraltetem Dock-Symbol startet.

## 3.4.7

- Das Dock verwendet direkt die transparente AppIcon.icns-Datei und nicht mehr einen nicht vorhandenen Asset-Katalog.

## 3.4.6

- Das Schließen des Fensters beendet die App ohne doppelte Terminierung und ohne einen kurzzeitig zusätzlichen Dock-Eintrag.

## 3.4.5

- Die Abkürzungen B2B, B2C und B2A werden als Kennungen vorgelesen und nicht mehr zur manuellen Prüfung übersprungen.

## 3.4.4

- Eigene Sprach-Tags funktionieren auch bei beliebigen Decknamen. Leere Tag-Felder sind erlaubt; kyrillische Hinweise werden vor der nicht-russischen Sprachausgabe ausgelassen.

## 3.4.3

- Nach dem Erstellen der Audios kann ein ersetzter Export sicher neu verknüpft werden, wenn jedes ausgewählte Kartenfeld exakt übereinstimmt. Der neue Lernstand bleibt dabei erhalten.

## 3.4.2

- Ein bereits geladenes, pausiertes Projekt wird auch dann fortgesetzt, wenn die Datei am selben Pfad später ersetzt wurde.

## 3.4.1

- Ein macOS-PermissionError beim Abtrennen eines aus dem Fenster gestarteten Hintergrundprozesses unterbricht die Sprachausgabe nicht mehr.

## 3.4.0

- Beim Stimmenwechsel spielt ein optionales Beispiel sofort ab. Zwei Karten der aktuellen Auswahl können in einem eigenen Fenster angehört und dort gestoppt werden. Ohne Hintergrundauftrag beendet das Schließen des Hauptfensters die Anwendung vollständig.

## 3.3.0

- Russische Sprachausgabe mit Kseniya als Standard; fünf russische Stimmen, RU-Tags und Sprachauswahl je Feld. Gemeinsame Hörbeispiele in drei Oberflächensprachen verwenden vorhandene WAV-Dateien wieder.

## 3.2.5

- Stimmenwahl für Deutsch, Französisch, Englisch und Spanisch. Standard: DE M5, FR M1, EN M1 und ES M1; F1–F5 und M1–M5 stehen je Sprache bereit.
- Eigene exakte Tags je Sprache, Hörbeispiele im Fenster und ein vom Fenster unabhängiger Hintergrundprozess.

## 0.6.0

- Englische und spanische Stimmen; Stapel und Felder direkt aus dem Export; das Tag sound gilt ausschließlich im zweiten Modus.
- Deutsche Standardoberfläche, Englisch und Russisch; drei Auswahlarten, vollständige Anleitungen, sichere Wiederaufnahme und geprüftes Anwendungspaket.

## 0.4.0 — 2026-09-08

- Separater, fortsetzbarer `.apkg`-Export mit lokal erzeugter Sprache.
- Deutsche Stimme M5 und französische Stimme M1.
- Nur Felder mit vorhandenem `[sound:…]`-Verweis werden ersetzt.
- Prüfung, dass Karten und Wiederholungsverlauf im fertigen Paket unverändert bleiben.
- Unterstützung der Schreibweisen `3MM`, `90er` und `CO2`.

## 0.2.0 — 2026-09-08

- Weibliche deutsche und französische Stimmen.
- Ruhigeres Tempo und Pausen zwischen Überschrift und Beispiel.
- Stille Passagen werden nicht gekürzt; Anfangs- und Endpausen wurden ergänzt.
- Sprachabschnitte und letzte Aufnahmen in gemeinsamen Spuren bleiben vollständig erhalten.
- Verdächtige Enden führen zu einer begrenzten Wiederholung der Synthese.
- Die ursprüngliche WAV-Abtastrate bleibt beim Zusammenführen von Spuren erhalten.
- Französische kombinierende Akzentzeichen werden korrekt normalisiert.
- Zusätzliche lokale Prüfung des gesprochenen Texts mit unabhängiger Erkennung.

## 0.1.0 — 2026-09-08

- Testweise Vertonung von 30 Feldern aus einer Kopie eines Anki-Exports.
- Deutsche Vorderseite und französische Vorderseite / deutsche Rückseite.
- Nur Felder mit einem vorhandenen Audioverweis werden ausgewählt.
- Verifizierte Zahlen, Daten, Uhrzeiten, Beträge, Prozente, Bereiche und Indizes werden normalisiert.
- Lokale Hörseite, einzelne Aufnahmen und drei gemeinsame Spuren.
- Unveränderte Quellexporte werden geprüft; jeder Lauf erstellt einen neuen Ergebnisordner.
- Installationsprogramm mit festgelegten Abhängigkeiten und Prüfung der Modellarchive.

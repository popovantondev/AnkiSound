# Sprachqualität und Diagnose

Eine gültige WAV-Datei beweist nicht, dass jedes Wort richtig klingt. Hören Sie die erzeugte Aufnahme vor dem Import an, besonders bei Abkürzungen, gemischten Sprachen, Zahlen und ungewöhnlichen Zeichen.

## Text und Kartensicherheit

- HTML und vorhandene Audioverweise werden aus dem Text für die Synthese entfernt; der ursprüngliche Kartentext bleibt im Quellexport unverändert.
- Die Normalisierung verändert nur den Text, der an die Sprachsynthese geht. Sie schreibt keine Wörter in der Karte um.
- Wenn nach dem Entfernen nicht unterstützter oder fremdsprachiger Hinweise kein sprechbarer Text übrig bleibt, wird die Karte zur Prüfung übersprungen statt leere Sprache zu erzeugen.
- Lange Texte werden in Abschnitte geteilt und mit Pausen zusammengesetzt. Die fertige WAV-Datei wird geprüft, bevor sie eine vorhandene Audiodatei ersetzen darf.

## Anhören und prüfen

Nutzen Sie das Stimmenbeispiel in der App und die Vorschau für bis zu zwei ausgewählte Karten. Schließen Sie das Vorschaufenster oder ändern Sie die Auswahl, um die Wiedergabe zu stoppen. Klingt ein Ergebnis undeutlich oder unvollständig, importieren Sie es nicht. Prüfen Sie den Kartentext und versuchen Sie eine passende Stimme.

Die Metadaten eines lokalen Auftrags im Ordner `output/` enthalten Stimme, Geschwindigkeit, den genauen Synthesetext, Versuche, Audiodauer und Prüfsummen. Behandeln Sie Auftragsordner und Protokolle als privat und hängen Sie sie keiner Fehlermeldung an.

## Problem melden

Nennen Sie App-Version, Sprechsprache und Stimme, macOS-Version sowie Wörter oder Zeichen, die falsch klangen. Verwenden Sie nach Möglichkeit ein künstliches Beispiel. Senden Sie niemals einen Anki-Export, eine persönliche Karte, erzeugte Audiodateien, lokale Pfade oder einen Auftragsordner.

# Mitwirken

Vielen Dank für Ihr Interesse an Anki SOUND. Eröffnen Sie für größere Änderungen zuerst ein Issue, damit Umfang und Auswirkungen auf die Datensicherheit geklärt werden können. GitHub bietet Vorlagen für Issues und Pull Requests auf Deutsch, Englisch und Russisch.

## Lokale Prüfungen

Verwenden Sie die Projektumgebung:

```sh
.venv/bin/python -m unittest discover -s Tests -v
.venv/bin/python -m compileall -q Sources scripts Tests
git diff --check
```

Die native macOS-App benötigt Xcode Command Line Tools. Bauen Sie in einen neuen Pfad, damit keine vorhandene App ersetzt wird:

```sh
.venv/bin/python scripts/build_app.py --output 'previews/Anki SOUND review.app'
```

Bei Änderungen an Auswahl, Synthese oder Paketierung ist zusätzlich ein manueller macOS-Smoketest mit einem künstlichen Anki-Export erforderlich. Verwenden Sie in automatisierten Prüfungen kein persönliches Anki-Profil oder Sammlung. Die optionale Integration mit `scripts/verify_with_anki.py` benötigt ein entbehrliches Sammlungsverzeichnis.

Tests dürfen keine externen Sprachdienste, kostenpflichtigen Anfragen oder persönlichen Dateien verwenden. Nehmen Sie keine Exporte, Audios, Stimmenmodelle, Protokolle, Caches, lokalen Pfade oder App-Bundles in Commits auf.

## Pull Requests

Beschreiben Sie die sichtbare Änderung, Auswirkungen auf den Datenschutz, die Prüfungen und die getestete macOS-Version. Hängen Sie keine Anki-Exporte, Kartentexte, Audios, Protokolle, Zugangsdaten oder privaten Pfade an.

# Drittkomponenten und Sprachmodelle

## Python-Komponenten

| Komponente | Version | Lizenz und Quelle |
| --- | --- | --- |
| sherpa-onnx, sherpa-onnx-core | 1.13.7 | Apache-2.0; https://github.com/k2-fsa/sherpa-onnx |
| numpy | 1.26.4 | BSD-3-Clause und enthaltene Hinweise; https://numpy.org/doc/1.26/license.html |
| num2words | 0.5.14 | LGPL-2.1; https://github.com/savoirfairelinux/num2words |
| docopt | 0.6.2 | MIT; https://github.com/docopt/docopt |
| zstandard | 0.25.0 | BSD-3-Clause und zstd-Hinweise; https://github.com/indygreg/python-zstandard |
| PyTorch | 2.8.0 | BSD-artig; https://github.com/pytorch/pytorch/blob/v2.8.0/LICENSE |

Das Paket enthält die Anwendung und den Projektquellcode, jedoch weder Python noch Pakete oder Modellgewichte. `SETUP.command` installiert festgelegte Versionen und das in `Resources/models.json` per SHA-256 geprüfte Spracharchiv. Weitere native Komponenten und Lizenzhinweise befinden sich in den installierten Paketen. Eine spätere eigenständige Distribution muss deren vollständige Lizenzhinweise gesondert enthalten.

## Stimmen und Modelle

**Supertonic 3:** `sherpa-onnx-supertonic-3-tts-int8-2026-05-11`. DE M5 (sid 9), FR M1 (sid 5), EN M1 (sid 5), ES M1 (sid 5). Ausgabe: 44.100 Hz. Der heruntergeladene Softwarehinweis nennt MIT und Supertone Inc. Die Bedingungen der Modellgewichte stellt der Anbieter bereit: https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE . Modellquelle: https://huggingface.co/Supertone/supertonic-3 . Die Reihenfolge der Stimmen ist dokumentiert unter https://github.com/k2-fsa/sherpa-onnx/blob/v1.13.7/scripts/supertonic/generate_voices_bin.py . Archiv: https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models .

**Russische Stimmen:** Silero `v5_5_ru`, 48.000 Hz. Standard: Kseniya; außerdem Xenia, Baya, Aidar und Eugene. Download: https://models.silero.ai/models/tts/ru/v5_5_ru.pt . Der genaue SHA-256-Wert ist in `Resources/models.json` festgelegt und wird vor dem Laden geprüft. Die russischen Modellgewichte unterliegen **CC BY-NC 4.0** (Namensnennung, nicht kommerziell), nicht MIT. Sie werden separat heruntergeladen und sind nicht im Paket enthalten. Quelle und Bedingungen: https://github.com/snakers4/silero-models#v5 und https://github.com/snakers4/silero-models/blob/master/LICENSE . Namensnennung: Silero Team.

## Dateiformat

Anki MediaEntries-Schema: https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto . Anki wird nur für optionale Integrationstests verwendet und ist nicht Teil der Anwendung.

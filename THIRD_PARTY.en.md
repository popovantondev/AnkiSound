# Third-party components and voice models

## Python components

| Component | Version | License and source |
| --- | --- | --- |
| sherpa-onnx, sherpa-onnx-core | 1.13.7 | Apache-2.0; https://github.com/k2-fsa/sherpa-onnx |
| numpy | 1.26.4 | BSD-3-Clause and bundled notices; https://numpy.org/doc/1.26/license.html |
| num2words | 0.5.14 | LGPL-2.1; https://github.com/savoirfairelinux/num2words |
| docopt | 0.6.2 | MIT; https://github.com/docopt/docopt |
| zstandard | 0.25.0 | BSD-3-Clause and bundled zstd notices; https://github.com/indygreg/python-zstandard |
| PyTorch | 2.8.0 | BSD-style; https://github.com/pytorch/pytorch/blob/v2.8.0/LICENSE |

The package includes the app and project source, but not Python, packages or model weights. `SETUP.command` installs pinned versions and the voice archive whose SHA-256 is checked against `Resources/models.json`. Additional native components and their notices are included in the installed packages. A future fully bundled distribution must include their complete license notices separately.

## Voices and models

**Supertonic 3:** `sherpa-onnx-supertonic-3-tts-int8-2026-05-11`. DE M5 (sid 9), FR M1 (sid 5), EN M1 (sid 5), ES M1 (sid 5). Output: 44,100 Hz. The downloaded software notice says MIT, Supertone Inc. The model publisher provides separate terms for the model weights: https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE . Model source: https://huggingface.co/Supertone/supertonic-3 . Voice ordering: https://github.com/k2-fsa/sherpa-onnx/blob/v1.13.7/scripts/supertonic/generate_voices_bin.py . Archive: https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models .

**Russian voices:** Silero `v5_5_ru`, 48,000 Hz. Default: Kseniya; also Xenia, Baya, Aidar and Eugene. Download: https://models.silero.ai/models/tts/ru/v5_5_ru.pt . The exact SHA-256 is pinned in `Resources/models.json` and checked before loading. Russian model weights use **CC BY-NC 4.0** (attribution, noncommercial), not MIT. They are downloaded separately and are not bundled. Source and terms: https://github.com/snakers4/silero-models#v5 and https://github.com/snakers4/silero-models/blob/master/LICENSE . Attribution: Silero Team.

## File format

Anki MediaEntries schema: https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto . Anki is used only for optional integration tests and is not included in the application.

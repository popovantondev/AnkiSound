# Сторонние компоненты и модели голосов

## Компоненты Python

| Компонент | Версия | Лицензия и источник |
| --- | --- | --- |
| sherpa-onnx, sherpa-onnx-core | 1.13.7 | Apache-2.0; https://github.com/k2-fsa/sherpa-onnx |
| numpy | 1.26.4 | BSD-3-Clause и сопутствующие уведомления; https://numpy.org/doc/1.26/license.html |
| num2words | 0.5.14 | LGPL-2.1; https://github.com/savoirfairelinux/num2words |
| docopt | 0.6.2 | MIT; https://github.com/docopt/docopt |
| zstandard | 0.25.0 | BSD-3-Clause и уведомления zstd; https://github.com/indygreg/python-zstandard |
| PyTorch | 2.8.0 | BSD-подобная; https://github.com/pytorch/pytorch/blob/v2.8.0/LICENSE |

В пакет входят приложение и исходники проекта, но не Python, пакеты и веса моделей. `SETUP.command` устанавливает закреплённые версии и голосовой архив, SHA-256 которого проверяется по `Resources/models.json`. Установленные пакеты содержат уведомления о других нативных компонентах. Для будущего автономного дистрибутива их полные лицензионные уведомления нужно добавить отдельно.

## Голоса и модели

**Supertonic 3:** `sherpa-onnx-supertonic-3-tts-int8-2026-05-11`. DE M5 (sid 9), FR M1 (sid 5), EN M1 (sid 5), ES M1 (sid 5). Частота вывода: 44 100 Гц. Уведомление для загруженного программного компонента указывает MIT и Supertone Inc. Условия для весов модели публикует её поставщик: https://huggingface.co/Supertone/supertonic-3/blob/main/LICENSE . Источник модели: https://huggingface.co/Supertone/supertonic-3 . Порядок голосов: https://github.com/k2-fsa/sherpa-onnx/blob/v1.13.7/scripts/supertonic/generate_voices_bin.py . Архив: https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models .

**Русские голоса:** Silero `v5_5_ru`, 48 000 Гц. По умолчанию Kseniya; также Xenia, Baya, Aidar и Eugene. Загрузка: https://models.silero.ai/models/tts/ru/v5_5_ru.pt . Точная SHA-256-сумма закреплена в `Resources/models.json` и проверяется перед загрузкой. На веса русской модели распространяется **CC BY-NC 4.0** (указание авторства, некоммерческое использование), а не MIT. Они скачиваются отдельно и не включены в дистрибутив. Источник и условия: https://github.com/snakers4/silero-models#v5 и https://github.com/snakers4/silero-models/blob/master/LICENSE . Авторство: Silero Team.

## Формат файлов

Схема Anki MediaEntries: https://github.com/ankitects/anki/blob/main/proto/anki/import_export.proto . Anki используется только для необязательных интеграционных проверок и не включён в программу.

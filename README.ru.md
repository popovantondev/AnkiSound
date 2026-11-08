<!-- ppk-readme:head:start -->
<a href="https://popovantondev.github.io/AnkiSound/index-ru.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/header-ru-dark.c8b0e616.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/header-ru-light.5fec37be.svg" width="880" height="188" alt="Anki SOUND — Добавляет локальную озвучку карточкам Anki. macOS 13+ · Apple Silicon, Выпуск 3.4.11"></picture></a>
<!-- ppk-readme:head:end -->

# Anki SOUND

**Русский** · [Deutsch](README.md) · [English](README.en.md)

<!-- ppk-readme:body:start -->
<p>
<a href="https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-download-ru-dark.affc69e0.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-download-ru-light.24a1b0f4.svg" width="120" height="36" alt="Скачать"></picture></a>
<a href="https://popovantondev.github.io/AnkiSound/index-ru.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-website-ru-dark.7e39ca1c.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-website-ru-light.a5222752.svg" width="92" height="36" alt="Сайт"></picture></a>
<a href="https://popovantondev.github.io/AnkiSound/Guide-ru.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-guide-ru-dark.b54c4109.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-guide-ru-light.2b2eddf7.svg" width="161" height="36" alt="Руководство"></picture></a>
<a href="https://github.com/popovantondev/AnkiSound/issues/new/choose"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-bug-ru-dark.26c735f7.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-bug-ru-light.e0ebc8ac.svg" width="234" height="36" alt="Сообщить об ошибке"></picture></a>
</p>

<p><a href="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/images/guide-ru.png"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/preview-ru-dark.208cf4ad.webp"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/preview-ru-light.3b70a2ac.webp" width="880" height="516" alt="Интерфейс программы Anki SOUND"></picture></a><br>
<sub><a href="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/images/guide-ru.png">Снимок целиком</a></sub></p>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/divider-dark.893eb84c.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/divider-light.e4d22663.svg" width="880" height="6" alt="Разделитель"></picture>
<!-- ppk-readme:body:end -->

<!-- public-release:start -->
Добавляет локальную озвучку выбранным карточкам Anki и сохраняет отдельный проверенный пакет.

**macOS 13+ · Apple Silicon · Выпуск 3.4.11**

**[Скачать](https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11)** · **[Инструкция](https://popovantondev.github.io/AnkiSound/Guide-ru.html)** · **[Сообщить об ошибке](https://github.com/popovantondev/AnkiSound/issues/new/choose)**

**Требования и ограничения:** Python 3.9–3.12; интернет для первоначальной установки зависимостей и моделей. Приложение не нотарифицировано Apple.

**Первые шаги:** Распакуйте всю папку в доступное для записи место. Выполните SETUP.command, затем OPEN.command; выберите экспорт .apkg.

**Файлы приложения:**

- [`Anki_SOUND-v3.4.11-macOS-AppleSilicon.zip`](https://github.com/popovantondev/AnkiSound/releases/download/v3.4.11/Anki_SOUND-v3.4.11-macOS-AppleSilicon.zip)

**Контрольные суммы:** [`SHA256SUMS.txt`](https://github.com/popovantondev/AnkiSound/releases/download/v3.4.11/SHA256SUMS.txt)
<!-- public-release:end -->

**Разборчивая локальная озвучка выбранных карточек Anki. Исходная коллекция остаётся нетронутой.**

Anki SOUND — нативная программа для macOS. Она читает экспорт Anki `.apkg`, создаёт озвучку локально и формирует отдельный проверенный пакет. Можно выбрать карточки с уже добавленным звуком, карточки с языковыми тегами или конкретную колоду.

## Как это работает

```mermaid
flowchart LR
    A[Экспорт Anki] --> B[Выбрать карточки и поля]
    B --> C[Локальный синтез речи]
    C --> D[Проверить медиа и обучение]
    D --> E[Новый пакет Anki]
    A -. Исходник не меняется .-> F[Исходный экспорт]
```

Поддерживаются немецкая, французская, английская, испанская и русская озвучки. Голоса по умолчанию: DE M5, FR M1, EN M1, ES M1 и RU Kseniya. Интерфейс доступен на немецком, английском и русском языках; по умолчанию выбран немецкий. Голос запоминается отдельно для каждого языка. Перед обработкой можно прослушать выбранные карточки.

## Скачать и установить

Скачайте пакет macOS на странице [GitHub Releases](https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11) и распакуйте всю папку в место, доступное для записи. Приложение должно оставаться рядом с этой папкой.

1. Запустите `SETUP.command`. Для установки закреплённых зависимостей и моделей голосов нужны Python 3.9–3.12 и интернет.
2. Откройте Anki SOUND командой `OPEN.command`.
3. Экспортируйте колоду из Anki в `.apkg`, выберите режим озвучки, прослушайте фрагмент и запустите обработку.

Приложение подписано локальной подписью, но не нотарифицировано Apple. При первом запуске macOS может его заблокировать. Проверьте источник и контрольную сумму пакета, затем следуйте инструкции для отдельного приложения в [руководстве](https://popovantondev.github.io/AnkiSound/Guide-ru.html). Не отключайте Gatekeeper глобально.

## Режимы отбора

- **Заменить существующий звук:** сначала добавьте аудио в Anki любым удобным способом. Anki SOUND заменяет только существующие ссылки `[sound:…]`.
- **Карточки с тегом:** задайте отдельный точный тег для каждого языка. Для распознанных названий колод язык задают колода и поле; нужен соответствующий тег. В неизвестной колоде ровно один однозначный тег может определить язык только для `Front`. Несколько совпавших языковых тегов неоднозначны, такая карточка пропускается.
- **Выбранная колода:** явно задайте колоду, поле и язык озвучки.

В распознанных французских колодах `FR` соответствует `Front`, а `DE` — `Back`. Например, `fr-audio` выбирает французский `Front`, а `de-audio` — немецкий `Back`. В неизвестной колоде тег `custom-de` может определить немецкий язык для `Front`; сочетание `custom-de` и `custom-en` неоднозначно и пропускается. Для `Back` неизвестной колоды язык не определяется — выберите режим «Выбранная колода» и задайте язык явно. Карточки без тега пропускаются, тег сравнивается как точное слово. Можно прослушать до двух карточек из текущего отбора. При закрытии окна или изменении отбора предпрослушивание останавливается.

## Данные и ограничения

- Исходный `.apkg` и установленный профиль Anki не меняются. Программа создаёт отдельный экспорт и проверяет медиа и данные обучения.
- Синтез речи работает локально. При установке скачиваются закреплённые зависимости и модели голосов; они не входят в репозиторий или пакет релиза.
- Локальные данные задания хранят точный текст синтеза, голос, настройки, длительность и контрольные суммы. Считайте папки заданий и журналы личными; подробности — в разделе [«Качество и диагностика озвучки»](docs/AUDIO_QA.ru.md).
- Для весов русской модели действуют отдельные условия **CC BY-NC 4.0**. Они скачиваются отдельно. Подробности: [сторонние компоненты и лицензии моделей](THIRD_PARTY.ru.md).
- Произношение смешанного текста, сокращений и необычных символов может отличаться от ожидаемого. Прослушайте результат и проверьте пропущенные карточки.

## Документация

- [Русская инструкция](https://popovantondev.github.io/AnkiSound/Guide-ru.html)
- [Инструкция на немецком](https://popovantondev.github.io/AnkiSound/Guide-de.html)
- [Инструкция на английском](https://popovantondev.github.io/AnkiSound/Guide-en.html)
- [История изменений](CHANGELOG.ru.md)
- [Сторонние компоненты и лицензии моделей](THIRD_PARTY.ru.md)
- [Участие в разработке](CONTRIBUTING.ru.md) · [Политика безопасности](SECURITY.ru.md) · [Права](LICENSE.ru.md)

## Сборка и тесты

Локальные проверки описаны в [Участие в разработке](CONTRIBUTING.ru.md). Для сборки нативного приложения macOS нужны Xcode Command Line Tools. Python-зависимости и модели устанавливаются отдельно.

## Права на исходный код

Исходный код опубликован для просмотра в портфолио. Неизменённый релиз можно скачивать и запускать для личного использования; копировать, изменять и распространять исходный код нельзя. Открытой лицензии нет. См. [права](LICENSE.ru.md). На сторонние программы и модели голосов распространяются собственные условия.

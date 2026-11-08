<!-- ppk-readme:head:start -->
<a href="https://popovantondev.github.io/AnkiSound/index-en.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/header-en-dark.51c4a5c9.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/header-en-light.b348a185.svg" width="880" height="188" alt="Anki SOUND — Adds local speech to your Anki cards. macOS 13+ · Apple Silicon, Release 3.4.11"></picture></a>
<!-- ppk-readme:head:end -->

# Anki SOUND

[Русский](README.ru.md) · [Deutsch](README.md) · **English**

<!-- ppk-readme:body:start -->
<p>
<a href="https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-download-en-dark.7a0ebdfb.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-download-en-light.493515ba.svg" width="136" height="36" alt="Download"></picture></a>
<a href="https://popovantondev.github.io/AnkiSound/index-en.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-website-en-dark.b2ee205a.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-website-en-light.11a77c56.svg" width="120" height="36" alt="Website"></picture></a>
<a href="https://popovantondev.github.io/AnkiSound/Guide-en.html"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-guide-en-dark.e6fb8ccf.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-guide-en-light.9782fe6a.svg" width="141" height="36" alt="User guide"></picture></a>
<a href="https://github.com/popovantondev/AnkiSound/issues/new/choose"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-bug-en-dark.7ed896ca.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/btn-bug-en-light.d248abdf.svg" width="196" height="36" alt="Report a problem"></picture></a>
</p>

<p><a href="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/images/guide-en.png"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/preview-en-dark.50dc244b.webp"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/preview-en-light.4bf28c6e.webp" width="880" height="516" alt="Anki SOUND interface"></picture></a><br>
<sub><a href="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/images/guide-en.png">Full screenshot</a></sub></p>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/divider-dark.893eb84c.svg"><img src="https://raw.githubusercontent.com/popovantondev/AnkiSound/main/docs/readme/divider-light.e4d22663.svg" width="880" height="6" alt="Divider"></picture>
<!-- ppk-readme:body:end -->

<!-- public-release:start -->
Add local speech to selected Anki cards and save a separately verified package.

**macOS 13+ · Apple Silicon · Release 3.4.11**

**[Download](https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11)** · **[User guide](https://popovantondev.github.io/AnkiSound/Guide-en.html)** · **[Report a problem](https://github.com/popovantondev/AnkiSound/issues/new/choose)**

**Requirements and limitations:** Python 3.9–3.12; internet for initial dependency and voice-model setup. Not notarized by Apple.

**First steps:** Extract the complete folder to a writable location. Run SETUP.command, then OPEN.command and select an .apkg export.

**Application files:**

- [`Anki_SOUND-v3.4.11-macOS-AppleSilicon.zip`](https://github.com/popovantondev/AnkiSound/releases/download/v3.4.11/Anki_SOUND-v3.4.11-macOS-AppleSilicon.zip)

**Checksums:** [`SHA256SUMS.txt`](https://github.com/popovantondev/AnkiSound/releases/download/v3.4.11/SHA256SUMS.txt)
<!-- public-release:end -->

**Add clear, local speech to selected Anki cards. Keep your original collection unchanged.**

Anki SOUND is a native macOS app that reads an Anki `.apkg` export, generates speech locally, and creates a separate verified package. Choose cards that already contain audio, cards with language-specific tags, or cards in a selected deck.

## How it works

```mermaid
flowchart LR
    A[Anki export] --> B[Choose cards and fields]
    B --> C[Local speech synthesis]
    C --> D[Verify media and learning data]
    D --> E[New Anki package]
    A -. original stays unchanged .-> F[Source export]
```

The app supports German, French, English, Spanish and Russian speech. Default voices are DE M5, FR M1, EN M1, ES M1 and RU Kseniya. The interface is available in German, English and Russian, with German selected by default. Voice choices are saved per language; selected cards can be previewed before processing.

## Download and install

Download the macOS package from [GitHub Releases](https://github.com/popovantondev/AnkiSound/releases/tag/v3.4.11), extract the complete folder to a writable location, and keep the app together with that folder.

1. Run `SETUP.command`. Setup needs Python 3.9–3.12 and an internet connection to install pinned dependencies and download voice models.
2. Run `OPEN.command` to launch Anki SOUND.
3. Export a deck from Anki as `.apkg`, choose a selection mode, listen to the preview, and start when ready.

The app is ad-hoc signed and not notarized by Apple. macOS may block the first launch. Review the package and checksum, then follow the per-app instructions in [the user guide](https://popovantondev.github.io/AnkiSound/Guide-en.html). Do not disable Gatekeeper globally.

## Selection modes

- **Existing audio:** add audio in Anki using your preferred method; Anki SOUND replaces only existing `[sound:…]` references.
- **Language tags:** configure one exact tag for each language. For recognized deck roots, the deck and field determine the language and the matching tag is required. In an unrecognized deck, one unambiguous tag can infer the language for `Front` only; multiple matching language tags are skipped.
- **Selected deck:** select the deck, field and speech language explicitly.

Recognized French decks map `FR` to the front and `DE` to the back. For example, `fr-audio` selects French `Front`, while `de-audio` selects German `Back`. For an unrecognized deck, `custom-de` on `Front` can select German; `custom-de` plus `custom-en` is ambiguous and skipped. An unrecognized `Back` does not infer a language; use Selected deck to choose explicitly. Untagged cards are skipped and tag matching uses exact tokens. The app can preview up to two currently selected cards and stops that preview when the window closes or the selection changes.

## Data and limitations

- The input `.apkg` and installed Anki profile are not modified. The app writes a separate output package and verifies its media and learning data.
- Speech synthesis runs locally. Setup downloads the pinned runtime dependencies and voice models; they are not bundled in the repository or release package.
- Local job metadata stores the exact text sent to synthesis, voice settings, lengths and checksums. Treat job folders and logs as private; see [speech quality and diagnostics](docs/AUDIO_QA.en.md).
- Russian voice weights have their own **CC BY-NC 4.0** terms and are downloaded separately. See [third-party components and model terms](THIRD_PARTY.en.md).
- Speech quality can vary for mixed-language text, abbreviations and unusual symbols. Preview the result and review skipped cards before importing.

## Documentation

- [English user guide](https://popovantondev.github.io/AnkiSound/Guide-en.html)
- [German user guide](https://popovantondev.github.io/AnkiSound/Guide-de.html)
- [Russian user guide](https://popovantondev.github.io/AnkiSound/Guide-ru.html)
- [Change history](CHANGELOG.en.md)
- [Third-party components and model terms](THIRD_PARTY.en.md)
- [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Rights](LICENSE)

## Build and test

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks. The native macOS app requires Xcode Command Line Tools; Python dependencies and models are installed separately.

## Source code rights

The source code is published for viewing as a portfolio. An unmodified release may be downloaded and run for personal use; copying, modifying and redistributing the source code is not permitted. There is no open-source license. See [Rights](LICENSE). Third-party software and voice models have separate terms.

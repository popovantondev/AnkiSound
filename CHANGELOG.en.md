# Changelog

## 3.4.11

- The app icon now loads on GitHub Pages and in downloaded guides. Guide screenshots no longer include the macOS capture control.

## 3.4.10

- Build numbers and icon resources now follow the app version. A fresh app path allows verification without the old icon cache.

## 3.4.9

- The Dock icon is no longer replaced at runtime; macOS uses AppIcon.icns consistently from launch through shutdown.

## 3.4.8

- A permanent unique bundle identifier prevents macOS from switching to an old test copy with a stale Dock icon during shutdown.

## 3.4.7

- The Dock now uses the transparent AppIcon.icns resource directly instead of a missing asset catalog.

## 3.4.6

- Closing the window quits the app through the standard macOS path, avoiding duplicate termination and a transient extra Dock item.

## 3.4.5

- B2B, B2C and B2A abbreviations are spoken as identifiers instead of being skipped for manual review.

## 3.4.4

- Custom language tags work with arbitrary deck names. Empty tag fields are allowed, and Cyrillic hints are omitted before non-Russian speech generation.

## 3.4.3

- After audio generation, a replaced export can be safely rebased when every selected card field matches exactly. Its newer learning state is preserved.

## 3.4.2

- A loaded paused job can resume even when the file at the same path was later replaced.

## 3.4.1

- A macOS PermissionError while detaching a background process launched from the window no longer stops speech generation.

## 3.4.0

- An optional sample plays immediately when a voice changes. Two cards from the current selection can be heard and stopped in a separate window. Closing the main window fully quits the app when no background job is active.

## 3.3.0

- Russian speech with Kseniya by default; five Russian voices, RU tags and per-field language selection. Shared sample pages in three interface languages reuse existing WAV files.

## 3.2.5

- Voice selection for German, French, English and Spanish. Defaults: DE M5, FR M1, EN M1 and ES M1; F1–F5 and M1–M5 are available for every language.
- Separate exact tags per language, in-app listening samples and a background worker independent of the window.

## 0.6.0

- English and Spanish voices; deck and field lists read from the export; the sound tag applies only in the second mode.
- German default interface, with English and Russian; three selection modes, complete guides, safe resume and a verified app package.

## 0.4.0 — 2026-09-08

- A separate, resumable `.apkg` export with locally generated speech.
- German M5 and French M1 voices.
- Only fields with an existing `[sound:…]` reference are replaced.
- Verification that cards and review history remain unchanged in the finished package.
- Support for `3MM`, `90er` and `CO2` notation.

## 0.2.0 — 2026-09-08

- Female German and French voices.
- Calmer pacing and pauses between a heading and its example.
- Quiet passages are preserved; opening and ending pauses are added.
- Speech segments and final recordings in shared tracks remain complete.
- Suspicious endings trigger a limited synthesis retry.
- The original WAV sample rate is preserved when tracks are combined.
- French combining accents are normalized correctly.
- Additional local verification of spoken text with independent recognition.

## 0.1.0 — 2026-09-08

- Trial speech generation for 30 fields from a copy of an Anki export.
- German front side and French front / German back sides.
- Only fields with an existing audio reference are selected.
- Verified numbers, dates, times, amounts, percentages, ranges and indices are normalized.
- Local listening page, individual recordings and three shared tracks.
- Source-export preservation is checked; each run creates a new output folder.
- Installer with pinned dependencies and model archive verification.

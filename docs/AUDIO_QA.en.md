# Speech quality and diagnostics

A valid WAV file does not prove that every word sounds correct. Listen to the generated audio before importing the package, especially for abbreviations, mixed-language text, numbers and unusual symbols.

## Text and card safety

- HTML and existing sound references are removed from the text sent to synthesis; the original card text stays unchanged in the source export.
- Speech normalization changes only the text sent to synthesis. It does not rewrite the words in a card.
- If removing unsupported or foreign-script hints leaves no speakable text, the card is skipped for review instead of generating empty speech.
- Long input is split for synthesis and reassembled with pauses. The finished WAV is validated before it can replace existing audio.

## Listen and inspect

Use the in-app voice sample and the preview for up to two selected cards. Close the preview or change the selection to stop playback. If a result sounds unclear or incomplete, do not import it; review the card text and try a suitable voice.

Generated job metadata in the local `output/` folder records the voice, speed, exact text sent to synthesis, attempts, audio lengths and checksums. Treat job folders and logs as private: do not attach or upload them with an issue report.

## Before reporting a problem

Report the app version, speech language and voice, macOS version, and the words or symbols that did not sound right. Use a synthetic example when possible. Never send an Anki package, a personal card, generated audio, a local path or a job folder.

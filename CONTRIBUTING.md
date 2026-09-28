# Contributing

Thanks for helping improve Anki SOUND. Open an issue first for large changes so the user-facing behavior and data-safety impact can be discussed before implementation. GitHub provides issue and pull-request templates in English, German and Russian.

## Local checks

Use the project environment:

```sh
.venv/bin/python -m unittest discover -s Tests -v
.venv/bin/python -m compileall -q Sources scripts Tests
git diff --check
```

The native macOS app requires Xcode Command Line Tools. Build to a new path so an existing app is not replaced:

```sh
.venv/bin/python scripts/build_app.py --output 'previews/Anki SOUND review.app'
```

For changes to selection, synthesis or packaging, also perform a manual macOS smoke test with a synthetic Anki export. Do not use a personal Anki profile or collection in automated checks. The optional `scripts/verify_with_anki.py` integration check requires a disposable collection directory.

Tests must not call external speech services, make paid requests, or inspect personal files. Keep user exports, audio, voice models, logs, caches, local paths and generated app bundles out of commits.

## Pull requests

Describe the user-visible change, data-safety impact, tests, and macOS version checked. Do not attach Anki exports, card text, audio, logs, credentials, or private paths.

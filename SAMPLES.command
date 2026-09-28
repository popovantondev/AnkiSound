#!/bin/zsh
set -euo pipefail
cd -- "$(dirname -- "$0")"
page="$(.venv/bin/python Sources/voice_options.py | tail -n 1)"
open "$page"

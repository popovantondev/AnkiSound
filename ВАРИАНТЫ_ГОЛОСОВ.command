#!/bin/zsh
set -euo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
page="$($base/.venv/bin/python "$base/Sources/voice_options.py" | tail -n 1)"
open "$page"

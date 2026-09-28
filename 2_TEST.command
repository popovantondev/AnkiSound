#!/bin/zsh
set -eu
cd -- "${0:A:h}"
.venv/bin/python scripts/launch.py "$@"

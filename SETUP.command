#!/bin/zsh
set -euo pipefail
cd -- "$(dirname -- "$0")"
for interpreter in /usr/bin/python3 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 /usr/local/bin/python3.11; do
    if [[ -x "$interpreter" ]] && "$interpreter" -c 'import sys; raise SystemExit(not ((3,9) <= sys.version_info[:2] <= (3,12)))' 2>/dev/null; then
        exec "$interpreter" scripts/install.py
    fi
done
open docs/Guide-de.html
exit 1

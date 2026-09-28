#!/bin/zsh
set -euo pipefail
base="$(cd "$(dirname "$0")" && pwd)"
source_file="$(osascript -e 'POSIX path of (choose file with prompt "Выберите свежий экспорт Anki (.apkg)")')"
exec "$base/.venv/bin/python" "$base/Sources/batch_export.py" "$source_file"

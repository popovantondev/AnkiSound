"""Open an existing report or select an export for a new preview."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = json.loads((ROOT / 'Resources/ru.json').read_text())


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'open':
        reports = sorted((ROOT / 'output').glob('preview-*/index.html'))
        if not reports:
            raise FileNotFoundError(TEXT['no_report'])
        subprocess.run(['open', str(reports[-1])], check=True)
        return
    sources = list((ROOT / 'data').glob('*.colpkg'))
    if len(sys.argv) > 1:
        source = Path(sys.argv[1]).expanduser().resolve(strict=True)
    elif len(sources) == 1:
        source = sources[0]
    else:
        script = 'POSIX path of (choose file with prompt ' + json.dumps(TEXT['select_export'], ensure_ascii=False) + ')'
        result = subprocess.run(['osascript', '-e', script], text=True, capture_output=True)
        if result.returncode:
            return
        source = Path(result.stdout.strip())
    subprocess.run([str(ROOT / '.venv/bin/python'), str(ROOT / 'Sources/preview.py'), str(source), '--open'], check=True)


if __name__ == '__main__':
    main()

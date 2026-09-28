"""Create an entirely local listening report. No Anki write API is used."""
import argparse
import html
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from string import Template

from audio import create_engine, generate, concatenate
from collection import candidates, choose_samples, extract_collection, sha256

ROOT = Path(__file__).resolve().parents[1]
TEXT = json.loads((ROOT / 'Resources/ru.json').read_text())
SETTINGS = json.loads((ROOT / 'Resources/speech.json').read_text())


def atomic_text(path, content):
    temporary = path.with_suffix(path.suffix + '.partial')
    with temporary.open('x', encoding='utf-8') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise FileExistsError('Result already exists')
    temporary.rename(path)


def report(records, directory):
    escape = html.escape
    sections = []
    for group, name in TEXT['groups'].items():
        group_records = [r for r in records if r['group'] == group]
        if not group_records:
            continue
        combined = group + '.wav'
        concatenate(group_records, directory, directory / combined, SETTINGS['playlist_gap_seconds'])
        sections.append('<h2>' + escape(name) + '</h2><div class="playlist">' + escape(TEXT['playlist']) +
                        '<audio controls preload="none" src="' + combined + '"></audio></div>')
        for record in group_records:
            sections.append('<article class="sample"><div class="badge">' + escape(TEXT['sample']) + ' ' + str(record['index']) + ' · ' +
                            escape(TEXT['categories'][record['category']]) + '</div><p>' + escape(record['original']) +
                            '</p><audio controls preload="none" src="' + record['audio'] + '" aria-label="' +
                            escape(TEXT['sample']) + ' ' + str(record['index']) + '"></audio><details><summary>' +
                            escape(TEXT['spoken']) + '</summary><p class="spoken">' + escape(record['generated_text']) + '</p></details></article>')
    template = Template((ROOT / 'Resources/report.html').read_text())
    result = template.substitute(title=escape(TEXT['title']), intro=escape(TEXT['intro']),
                                 help=escape(TEXT['help']), sections='\n'.join(sections))
    atomic_text(directory / 'index.html', result)


def run(source):
    source = source.resolve(strict=True)
    before = sha256(source)
    output_root = ROOT / 'output'
    output_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('preview-%Y%m%d-%H%M%S-'), dir=output_root))
    started = time.monotonic()
    database = directory / 'source.sqlite3'
    try:
        extract_collection(source, database)
        records, counts = candidates(database)
        selected = choose_samples(records)
    finally:
        database.unlink(missing_ok=True)
    if len(selected) != 30:
        raise ValueError('Expected 30 representative samples in the configured deck groups')
    atomic_text(directory / 'selection.json', json.dumps({'source_sha256': before, 'counts': counts, 'samples': selected}, ensure_ascii=False, indent=2))
    engine, current_language = None, None
    for index, record in enumerate(selected, 1):
        if current_language != record['language']:
            del engine
            engine = create_engine(ROOT, SETTINGS, record['language'])
            current_language = record['language']
        record['index'] = index
        record['audio'] = f'{index:02d}-{record["group"]}.wav'
        record.update(generate(engine, record['spoken'], record['language'], directory / record['audio'], SETTINGS))
        print(TEXT['progress'].format(current=index, total=len(selected)), flush=True)
    if sha256(source) != before:
        raise ValueError('Source changed during processing')
    report(selected, directory)
    manifest = {'version': (ROOT / 'VERSION').read_text().strip(), 'source_sha256': before,
                'source_unchanged': True, 'speech_settings': SETTINGS, 'counts': counts, 'samples': selected,
                'elapsed_seconds': round(time.monotonic() - started, 3)}
    atomic_text(directory / 'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    print(TEXT['done'], flush=True)
    return directory / 'index.html'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    try:
        page = run(args.source)
    except KeyboardInterrupt:
        print(TEXT['cancelled'], file=sys.stderr)
        return 130
    except Exception as error:
        print(TEXT['error'] + ' (' + type(error).__name__ + ')', file=sys.stderr)
        return 1
    if args.open:
        import subprocess
        subprocess.run(['open', str(page)], check=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

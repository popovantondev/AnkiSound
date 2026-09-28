"""Create up to two temporary local listening samples for the current selection."""
import argparse
import json
import os
import tempfile
from pathlib import Path

from audio import concatenate, create_engine, generate
from batch_export import effective_settings
from collection import candidates, extract_collection, sha256
from normalize import normalize

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_LIMIT = 2


def selected_records(database, selection):
    records, _ = candidates(database, selection)
    chosen = []
    for record in sorted(records, key=lambda item: (item['note_id'], item['field_order'])):
        if len(record['original']) < 4 or len(record['original']) > 400:
            continue
        try:
            record = dict(record, spoken=normalize(record['speech_source'], record['language']))
        except ValueError:
            continue
        chosen.append(record)
        if len(chosen) == SAMPLE_LIMIT:
            break
    return chosen


def run(source, selection):
    source = Path(source).resolve(strict=True)
    output = ROOT / '.cache'
    output.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix='card-listen-', dir=output))
    database = directory / 'source.sqlite3'
    source_hash = sha256(source)
    try:
        extract_collection(source, database)
        records = selected_records(database, selection)
    finally:
        database.unlink(missing_ok=True)
    if not records:
        raise ValueError('No eligible cards in the current selection')
    settings = effective_settings(selection)
    engines = {}
    for index, record in enumerate(records, 1):
        language = record['language']
        if language not in engines:
            engines[language] = create_engine(ROOT, settings, language)
        engine = engines[language]
        record['audio'] = f'{index:02d}.wav'
        generate(engine, record['spoken'], language, directory / record['audio'], settings)
    if sha256(source) != source_hash:
        raise ValueError('Source changed while preparing listening samples')
    combined = directory / 'selected-cards.wav'
    concatenate(records, directory, combined, settings['playlist_gap_seconds'])
    print(json.dumps({'audio': str(combined), 'count': len(records)}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--selection', required=True)
    args = parser.parse_args()
    selection = json.loads(args.selection)
    if not isinstance(selection, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in selection.items()):
        raise ValueError('Invalid listening selection')
    run(args.source, selection)


if __name__ == '__main__':
    main()

"""Optional integration check with an installed Anki Python runtime."""
import argparse
import json
from pathlib import Path
from anki.collection import Collection
from anki.import_export_pb2 import (
    ExportAnkiPackageOptions, ExportLimit, ImportAnkiPackageRequest,
    ImportAnkiPackageOptions,
)

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['create', 'check'])
parser.add_argument('directory', type=Path)
parser.add_argument('--package', type=Path)
parser.add_argument('--language', choices=['de', 'ru'], default='de')
args = parser.parse_args()
args.directory.mkdir(parents=True, exist_ok=True)
if args.action == 'create':
    database = args.directory / 'source.anki2'
    if database.exists():
        raise FileExistsError('Fixture already exists')
    collection = Collection(str(database))
    try:
        deck = collection.decks.id('Русский' if args.language == 'ru' else 'Deutsch')
        model = collection.models.by_name('Basic')
        examples = [('Добрый день. [sound:original.wav]', []), ('Привет! Урок начинается в 13:05.', ['sound'])] if args.language == 'ru' else [('Guten Tag. [sound:original.wav]', []), ('Bonjour.', ['sound'])]
        for text, tags in examples:
            note = collection.new_note(model)
            note['Front'] = text
            note['Back'] = 'Translation'
            note.tags = tags
            collection.add_note(note, deck)
        collection.export_anki_package(
            out_path=str(args.directory / 'sample.apkg'),
            options=ExportAnkiPackageOptions(with_scheduling=True, with_deck_configs=True, with_media=True, legacy=False),
            limit=ExportLimit(whole_collection={}),
        )
    finally:
        collection.close()
else:
    database = args.directory / 'import.anki2'
    if database.exists():
        raise FileExistsError('Import fixture already exists')
    collection = Collection(str(database))
    try:
        result = collection.import_anki_package(ImportAnkiPackageRequest(
            package_path=str(args.package),
            options=ImportAnkiPackageOptions(update_notes=1, update_notetypes=1, with_scheduling=True, with_deck_configs=True),
        ))
        count = collection.db.scalar('select count(*) from notes')
        assert count == 2, count
        media = list(Path(collection.media.dir()).glob('*.wav'))
        assert media, 'No audio was imported'
        assert all(path.read_bytes().startswith(b'RIFF') for path in media)
        print(json.dumps({'notes': count, 'imported_wav': len(media)}))
    finally:
        collection.close()

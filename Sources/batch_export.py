"""Create a resumable, separately packaged Anki export with local speech."""
import argparse
from copy import deepcopy
import fcntl
import signal
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
import wave
from datetime import datetime
from pathlib import Path

import zstandard

from audio import create_engine, generate
from collection import candidates, extract_collection, sha256
from normalize import SOUND, normalize
from package_media import decode, encode, entries, append_media
from russian_speech import RUSSIAN_VOICES

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / 'Resources/speech.json').read_text())
CHECKPOINT_EVERY = 25
VOICE_IDS = {'F1': 0, 'F2': 1, 'F3': 2, 'F4': 3, 'F5': 4,
             'M1': 5, 'M2': 6, 'M3': 7, 'M4': 8, 'M5': 9}


def effective_settings(selection):
    """Keep the exact selected speakers with the job so resume is reproducible."""
    settings = deepcopy(SETTINGS)
    for language in ('de', 'fr', 'en', 'es'):
        voice = selection.get('voice_' + language, settings['voices'][language]['name'])
        if voice not in VOICE_IDS:
            raise ValueError('Unknown voice')
        settings['voices'][language]['speaker_id'] = VOICE_IDS[voice]
        settings['voices'][language]['name'] = voice
    russian = selection.get('voice_ru', settings['voices']['ru']['name'])
    if russian not in RUSSIAN_VOICES:
        raise ValueError('Unknown Russian voice')
    settings['voices']['ru'].update(name=russian, speaker_id=russian.lower())
    return settings


def compatible_settings(saved, current):
    return all(current.get(key) == value for key, value in saved.items() if key != 'voices') and all(
        current['voices'].get(language) == voice for language, voice in saved['voices'].items()
    )


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + str(os.getpid()) + '.partial')
    temporary.unlink(missing_ok=True)
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def digest_rows(database, table):
    connection = sqlite3.connect(database)
    try:
        columns = [row[1] for row in connection.execute('pragma table_info(' + table + ')')]
        digest = hashlib.sha256()
        for row in connection.execute('select * from ' + table + ' order by id'):
            digest.update(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode())
        return {'columns': columns, 'rows': connection.execute('select count(*) from ' + table).fetchone()[0],
                'sha256': digest.hexdigest()}
    finally:
        connection.close()


def new_audio_name(record):
    return 'anki_sound_{language}_{note}_{field}.wav'.format(
        language=record['language'], note=record['note_id'], field=record['field_order'])


def prepare_records(database, selection=None):
    records, counts = candidates(database, selection)
    accepted, rejected = [], []
    for record in records:
        if record.get('sound_count', 1) > 1:
            rejected.append({'note_id': record['note_id'], 'field_order': record['field_order'], 'reason': 'multiple_audio'})
            continue
        try:
            record = dict(record, spoken=normalize(record['speech_source'], record['language']))
        except ValueError as error:
            rejected.append({'note_id': record['note_id'], 'field_order': record['field_order'],
                             'reason': type(error).__name__})
            continue
        record['audio'] = new_audio_name(record)
        accepted.append(record)
    return accepted, counts, rejected


def language_tag_selection(values):
    selection = {}
    for language in ('de', 'fr', 'en', 'es', 'ru'):
        tag = values.get(language, 'sound').strip()
        if tag and any(character.isspace() for character in tag):
            raise ValueError('Tag names cannot contain spaces')
        selection['tag_' + language] = tag
    return selection


def create_job(source, selection=None, settings=None):
    selection = selection or {'mode': 'existing'}
    settings = settings or SETTINGS
    source = source.resolve(strict=True)
    output_root = ROOT / 'output'
    output_root.mkdir(exist_ok=True)
    source_hash = sha256(source)
    with zipfile.ZipFile(source) as archive:
        if 'meta' not in archive.namelist() or archive.read('meta') != b'\x08\x03':
            raise ValueError('Please export using the current Anki format')
    legacy = output_root / ('batch-' + source_hash[:16])
    if (legacy / 'state.json').exists() and selection == {'mode': 'existing'}:
        if compatible_settings(load_state(legacy)['settings'], settings):
            return legacy
    fingerprint = hashlib.sha256(json.dumps([settings, selection], sort_keys=True).encode()).hexdigest()[:12]
    job = output_root / ('batch-' + source_hash[:16] + '-' + fingerprint)
    with (output_root / 'prepare.lock').open('a+') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        if (job / 'state.json').exists():
            return job
        with tempfile.TemporaryDirectory(prefix='prepare-', dir=output_root) as folder:
            temporary = Path(folder)
            database = temporary / 'collection.sqlite3'
            extract_collection(source, database)
            records, counts, rejected = prepare_records(database, selection)
            if not records:
                raise ValueError('No eligible fields; check deck, field and tag')
            for record in records:
                record['audio'] = fingerprint + '_' + record['audio']
            (temporary / 'media').mkdir()
            atomic_json(temporary / 'state.json', {
                'source': str(source), 'source_sha256': source_hash, 'created_at': datetime.now().isoformat(),
                'settings': settings, 'selection': selection, 'counts': counts,
                'records': records, 'rejected': rejected, 'completed': [],
            })
            temporary.rename(job)
    return job


def load_state(job):
    return json.loads((job / 'state.json').read_text())


def resume_job(path):
    """Return a prepared job inside this project's output directory only."""
    job = Path(path).resolve(strict=True)
    if job.parent != (ROOT / 'output').resolve() or not (job / 'state.json').is_file():
        raise ValueError('Invalid saved job')
    return job


def acquire_run_lock(job):
    """Reject a second writer while allowing recovery after a stopped process."""
    lock = (job / 'worker.lock').open('a+')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise RuntimeError('Audio generation is already running')
    atomic_json(job / 'running.json', {'pid': os.getpid()})
    return lock


def update_field(database, record):
    connection = sqlite3.connect(database)
    try:
        row = connection.execute('select flds from notes where id=?', (record['note_id'],)).fetchone()
        if row is None:
            raise ValueError('Note is missing from work copy')
        fields = row[0].split('\x1f')
        original = fields[record['field_order']]
        if hashlib.sha256(original.encode()).hexdigest() != record['field_sha256']:
            expected = '[sound:' + record['audio'] + ']'
            if expected in original:
                return
            raise ValueError('Field changed unexpectedly in work copy')
        updated = replacement(original, record)
        if updated == original:
            raise ValueError('Expected sound tag is missing')
        fields[record['field_order']] = updated
        connection.execute('update notes set flds=? where id=?', ('\x1f'.join(fields), record['note_id']))
        connection.commit()
    finally:
        connection.close()


def replacement(original, record):
    tag = '[sound:' + record['audio'] + ']'
    if SOUND.search(original):
        return SOUND.sub(tag, original)
    if record.get('allow_new'):
        return original + ' ' + tag
    raise ValueError('Expected sound tag is missing')


def validate_wav(path):
    with wave.open(str(path), 'rb') as audio:
        frames = audio.getnframes()
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or frames == 0:
            raise ValueError('Invalid saved audio')
        if len(audio.readframes(frames)) != frames * 2:
            raise ValueError('Truncated saved audio')


def synthesize(job):
    state = load_state(job)
    settings = state['settings']
    completed = set(state['completed'])
    engines = {}
    total = len(state['records'])
    for position, record in enumerate(state['records'], 1):
        key = str(position - 1)
        destination = job / 'media' / record['audio']
        if key in completed:
            validate_wav(destination)
            continue
        if (job / 'pause.request').exists():
            (job / 'pause.request').unlink()
            state['completed'] = sorted(completed, key=int)
            atomic_json(job / 'state.json', state)
            raise KeyboardInterrupt
        engine = engines.get(record['language'])
        if engine is None:
            engine = create_engine(ROOT, settings, record['language'])
            engines[record['language']] = engine
        if not destination.exists():
            generate(engine, record['spoken'], record['language'], destination, settings)
        validate_wav(destination)
        update_field(job / 'collection.sqlite3', record)
        completed.add(key)
        if len(completed) % CHECKPOINT_EVERY == 0 or len(completed) == total:
            state['completed'] = sorted(completed, key=int)
            atomic_json(job / 'state.json', state)
        if len(completed) % CHECKPOINT_EVERY == 0 or len(completed) == total:
            print(json.dumps({'event': 'progress', 'done': len(completed), 'total': total}), flush=True)
    return state


def rebase_collection(job, source):
    """Apply saved audio replacements to a newer export after exact field checks."""
    state = load_state(job)
    source_hash = sha256(source)
    rebased = job / ('rebased-' + source_hash[:16] + '.sqlite3')
    if rebased.exists():
        return rebased
    temporary = job / (rebased.name + '.partial')
    try:
        extract_collection(source, temporary)
        connection = sqlite3.connect(temporary)
        try:
            for record in state['records']:
                row = connection.execute('select flds from notes where id=?', (record['note_id'],)).fetchone()
                if row is None:
                    raise ValueError('Selected note is missing from the replacement export')
                fields = row[0].split('\x1f')
                original = fields[record['field_order']]
                if hashlib.sha256(original.encode()).hexdigest() != record['field_sha256']:
                    expected = '[sound:' + record['audio'] + ']'
                    if expected in original:
                        continue
                    raise ValueError('Selected card text changed in the replacement export')
                fields[record['field_order']] = replacement(original, record)
                connection.execute('update notes set flds=? where id=?', ('\x1f'.join(fields), record['note_id']))
            connection.commit()
        finally:
            connection.close()
        temporary.rename(rebased)
        return rebased
    finally:
        temporary.unlink(missing_ok=True)


def package(job):
    state = load_state(job)
    if len(state['completed']) != len(state['records']):
        raise ValueError('Synthesis is not complete')
    source = Path(state['source'])
    database = job / 'collection.sqlite3'
    if sha256(source) != state['source_sha256']:
        database = rebase_collection(job, source)
    final = job / 'Anki SOUND.apkg'
    if final.exists():
        if (job / 'result.json').exists():
            return final
        verify(job, final)
        return final
    with zipfile.ZipFile(source) as archive:
        if archive.read('meta') != b'\x08\x03':
            raise ValueError('Current Anki export format is required')
        media = bytearray(decode(archive.read('media')))
        next_index = len(entries(media))
        numbered = []
        for record in state['records']:
            media.extend(append_media(b'', record['audio'], (job / 'media' / record['audio']).read_bytes()))
            numbered.append((str(next_index), job / 'media' / record['audio']))
            next_index += 1
        descriptor, compressed_name = tempfile.mkstemp(prefix='collection.', suffix='.anki21b', dir=job)
        os.close(descriptor)
        compressed = Path(compressed_name)
        try:
            with database.open('rb') as source_db, compressed.open('wb') as target:
                with zstandard.ZstdCompressor(level=10).stream_writer(target) as compressor:
                    shutil.copyfileobj(source_db, compressor)
            descriptor, temporary_name = tempfile.mkstemp(prefix=final.name + '.', suffix='.partial', dir=final.parent)
            os.close(descriptor)
            temporary = Path(temporary_name)
            try:
                with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
                    for item in archive.infolist():
                        if item.filename in ('collection.anki21b', 'media'):
                            continue
                        output.writestr(item, archive.read(item.filename))
                    output.write(compressed, 'collection.anki21b')
                    output.writestr('media', encode(media))
                    for index, path in numbered:
                        output.writestr(index, encode(path.read_bytes()), compress_type=zipfile.ZIP_STORED)
                if zipfile.ZipFile(temporary).testzip() is not None:
                    raise ValueError('Generated package is corrupt')
                verify(job, temporary)
                os.link(temporary, final)
            finally:
                temporary.unlink(missing_ok=True)
        finally:
            compressed.unlink(missing_ok=True)
    return final


def verify(job, final):
    state = load_state(job)
    database = job / 'verified.sqlite3'
    database.unlink(missing_ok=True)
    original = job / 'original-check.sqlite3'
    original.unlink(missing_ok=True)
    extract_collection(Path(state['source']), original)
    extract_collection(final, database)
    try:
        if digest_rows(original, 'cards') != digest_rows(database, 'cards'):
            raise ValueError('Card scheduling changed in package')
        if digest_rows(original, 'revlog') != digest_rows(database, 'revlog'):
            raise ValueError('Review history changed in package')
        sounds = [record['audio'] for record in state['records']]
        if len(set(sounds)) != len(sounds):
            raise ValueError('Unexpected field count after packaging')
        with zipfile.ZipFile(final) as archive:
            media = entries(decode(archive.read('media')))
            with zipfile.ZipFile(state['source']) as source:
                original_media = entries(decode(source.read('media')))
                if media[:len(original_media)] != original_media:
                    raise ValueError('Original media map changed')
                for name in source.namelist():
                    if name not in ('media', 'collection.anki21b') and source.read(name) != archive.read(name):
                        raise ValueError('Original package entry changed')
            offset = len(media) - len(sounds)
            if offset != len(original_media):
                raise ValueError('Audio map is incomplete')
            for index, name in enumerate(sounds, offset):
                data = decode(archive.read(str(index)))
                expected = (job / 'media' / name).read_bytes()
                if data != expected or entries(append_media(b'', name, data))[0] != media[index]:
                    raise ValueError('Audio checksum mismatch')
        before, after = sqlite3.connect(original), sqlite3.connect(database)
        # SQLite requires a registered collation to scan Anki's WITHOUT ROWID tables.
        # These scans use no text predicates; raw row equality is checked below.
        for connection in (before, after):
            connection.create_collation('unicase', lambda a, b: (a > b) - (a < b))
        replacements = {}
        for record in state['records']:
            replacements.setdefault(record['note_id'], {})[record['field_order']] = record
        try:
            tables = before.execute("select name,sql from sqlite_master where type='table' order by name").fetchall()
            if tables != after.execute("select name,sql from sqlite_master where type='table' order by name").fetchall():
                raise ValueError('Database schema changed')
            from collections import Counter
            for table, _ in tables:
                if table in ('notes', 'cards', 'revlog'):
                    continue
                quoted = '"' + table.replace('"', '""') + '"'
                # Compare raw values, independent of Anki's custom text collations.
                if Counter(before.execute('select * from ' + quoted)) != Counter(after.execute('select * from ' + quoted)):
                    raise ValueError('Unselected data changed')
            columns = [r[1] for r in before.execute('pragma table_info(notes)')]
            fi = columns.index('flds')
            old_rows = before.execute('select * from notes order by id')
            new_rows = after.execute('select * from notes order by id')
            import itertools
            for old, new in itertools.zip_longest(old_rows, new_rows):
                if old is None or new is None:
                    raise ValueError('Note count changed')
                expected = list(old)
                fields = old[fi].split('\x1f')
                for order, record in replacements.get(old[0], {}).items():
                    fields[order] = replacement(fields[order], record)
                expected[fi] = '\x1f'.join(fields)
                if tuple(expected) != new:
                    raise ValueError('Unexpected note modification')
        finally:
            before.close()
            after.close()
    finally:
        database.unlink(missing_ok=True)
        original.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--package-only', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--resume-job', type=Path)
    parser.add_argument('--mode', choices=['existing', 'tag', 'deck'], default='existing')
    parser.add_argument('--deck', default='')
    parser.add_argument('--field', default='*')
    parser.add_argument('--language', choices=['de', 'fr', 'en', 'es', 'ru'], default='de')
    parser.add_argument('--back-language', choices=['de', 'fr', 'en', 'es', 'ru'], default='de')
    for language in ('de', 'fr', 'en', 'es', 'ru'):
        parser.add_argument('--tag-' + language, default='sound')
    for language in ('de', 'fr', 'en', 'es'):
        parser.add_argument('--voice-' + language, choices=sorted(VOICE_IDS))
    parser.add_argument('--voice-ru', choices=RUSSIAN_VOICES)
    args = parser.parse_args()
    if args.detach:
        try:
            os.setsid()
        except PermissionError:
            # macOS can make the GUI-launched child a process-group leader.
            # The parent caffeinate process still keeps this worker independent.
            pass
    selection = {'mode': args.mode}
    if args.mode != 'existing':
        selection.update(deck=args.deck, field=args.field, language=args.language, back_language=args.back_language)
    elif args.deck or args.field != '*':
        selection.update(deck=args.deck, field=args.field)
    for language in ('de', 'fr', 'en', 'es', 'ru'):
        value = getattr(args, 'voice_' + language)
        if value:
            selection['voice_' + language] = value
    if args.mode == 'tag':
        selection.update(language_tag_selection({
            language: getattr(args, 'tag_' + language)
            for language in ('de', 'fr', 'en', 'es', 'ru')
        }))
    if args.mode == 'deck' and not args.deck.strip():
        raise ValueError('Select a deck')
    job = resume_job(args.resume_job) if args.resume_job else create_job(args.source, selection, effective_settings(selection))
    lock = acquire_run_lock(job)
    try:
        state = load_state(job)
        print(json.dumps({'event': 'prepared', 'job': job.name, 'total': len(state['records']), 'skipped': len(state['rejected'])}), flush=True)
        if not args.package_only:
            synthesize(job)
        final = package(job)
        atomic_json(job / 'result.json', {'path': str(final), 'verified': True})
        print(json.dumps({'event': 'complete'}), flush=True)
    finally:
        (job / 'running.json').unlink(missing_ok=True)
        lock.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(json.dumps({'event': 'paused'}), flush=True)
        raise SystemExit(130)
    except Exception as error:
        print(json.dumps({'event': 'error', 'code': type(error).__name__}), flush=True)
        raise SystemExit(1)

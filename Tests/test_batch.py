import hashlib
import io
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zipfile
import zstandard
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
import batch_export as batch
from package_media import encode, decode, entries, append_media


class BatchTests(unittest.TestCase):
    def test_empty_language_tag_is_allowed_and_whitespace_is_trimmed(self):
        selection = batch.language_tag_selection({'de': '  ', 'fr': ' fr-audio '})
        self.assertEqual(selection['tag_de'], '')
        self.assertEqual(selection['tag_fr'], 'fr-audio')
        self.assertEqual(selection['tag_en'], 'sound')

    def test_language_tag_with_spaces_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cannot contain spaces'):
            batch.language_tag_selection({'de': 'two words'})

    def test_lock_rejects_second_writer_and_recovers(self):
        with tempfile.TemporaryDirectory() as temp:
            job = Path(temp)
            lock = batch.acquire_run_lock(job)
            with self.assertRaises(RuntimeError):
                batch.acquire_run_lock(job)
            lock.close()
            batch.acquire_run_lock(job).close()

    def test_resume_job_is_limited_to_project_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            valid = root / 'output' / 'batch-fixture'
            valid.mkdir(parents=True)
            (valid / 'state.json').write_text('{}')
            outside = root / 'other'
            outside.mkdir()
            (outside / 'state.json').write_text('{}')
            with patch.object(batch, 'ROOT', root):
                self.assertEqual(batch.resume_job(valid), valid.resolve())
                with self.assertRaises(ValueError):
                    batch.resume_job(outside)

    def test_rebase_replaces_only_matching_card_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            job = root / 'job'; job.mkdir()
            replacement = root / 'replacement.apkg'; replacement.write_bytes(b'replacement')
            database = root / 'replacement.sqlite3'
            connection = sqlite3.connect(database)
            connection.execute('create table notes(id integer primary key, flds text)')
            original = 'Hallo [sound:old.wav]'
            connection.execute('insert into notes values(1, ?)', (original,))
            connection.commit(); connection.close()
            record = {'note_id': 1, 'field_order': 0, 'audio': 'new.wav', 'allow_new': False,
                      'field_sha256': hashlib.sha256(original.encode()).hexdigest()}
            batch.atomic_json(job / 'state.json', {'records': [record]})
            with patch.object(batch, 'extract_collection', side_effect=lambda source, target: shutil.copyfile(database, target)):
                rebased = batch.rebase_collection(job, replacement)
            checked = sqlite3.connect(rebased)
            self.assertEqual(checked.execute('select flds from notes').fetchone()[0], 'Hallo [sound:new.wav]')
            checked.close()

    def test_package_preserves_scheduling_and_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            db = root / 'fixture.sqlite3'
            c = sqlite3.connect(db)
            c.create_collation('unicase', lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower()))
            c.executescript('''
                create table decks(id integer,name text);
                create table fields(ntid integer,ord integer,name text);
                create table settings(name text collate unicase primary key,value blob) without rowid;
                insert into settings values('Keep',X'0102');
                create table cards(id integer,nid integer,did integer,odid integer,due integer);
                create table revlog(id integer,cid integer,ivl integer);
                create table notes(id integer,mid integer,flds text);
                insert into decks values(1,'!Немецкий');
                insert into fields values(1,0,'Front'),(1,1,'Back');
                insert into cards values(1,10,1,0,456);
                insert into revlog values(1,1,42);
            ''')
            field = 'Hallo [sound:old.wav]'
            c.execute('insert into notes values(10,1,?)', (field+'\x1fUntouched',))
            c.commit(); c.close()
            source = root / 'input.apkg'
            old_audio = b'original audio'
            with zipfile.ZipFile(source, 'w') as z:
                z.writestr('meta', b'\x08\x03')
                z.writestr('collection.anki21b', encode(db.read_bytes()))
                z.writestr('media', encode(append_media(b'', 'old.wav', old_audio)))
                z.writestr('0', encode(old_audio))
            original_hash = batch.sha256(source)
            with patch.object(batch, 'ROOT', root):
                job = batch.create_job(source)
                state = batch.load_state(job)
                record = state['records'][0]
                audio = b'RIFF test audio bytes'
                (job / 'media' / record['audio']).write_bytes(audio)
                batch.update_field(job / 'collection.sqlite3', record)
                batch.update_field(job / 'collection.sqlite3', record)
                state['completed'] = ['0']
                batch.atomic_json(job / 'state.json', state)
                result = batch.package(job)
                self.assertEqual(batch.sha256(source), original_hash)
                with zipfile.ZipFile(result) as z:
                    self.assertEqual(decode(z.read('0')), old_audio)
                    self.assertEqual(decode(z.read('1')), audio)
                    self.assertEqual(len(entries(decode(z.read('media')))), 2)
                    packaged_db = root / 'packaged.sqlite3'
                    with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(z.read('collection.anki21b'))) as reader:
                        packaged_db.write_bytes(reader.read())
                packaged = sqlite3.connect(packaged_db)
                self.assertEqual(packaged.execute('select due from cards where id=1').fetchone()[0], 456)
                self.assertEqual(packaged.execute('select ivl from revlog where id=1').fetchone()[0], 42)
                packaged.close()
                self.assertEqual(batch.package(job), result)

    def test_new_audio_requires_explicit_selection(self):
        record = {'audio': 'new.wav'}
        with self.assertRaises(ValueError):
            batch.replacement('Untouched', record)
        record['allow_new'] = True
        self.assertEqual(batch.replacement('Hallo', record), 'Hallo [sound:new.wav]')

    def test_wave_validation_rejects_partial_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            import wave
            path = Path(folder) / 'sample.wav'
            with wave.open(str(path), 'wb') as audio:
                audio.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
                audio.writeframes(b'\0' * 1000)
            batch.validate_wav(path)
            path.write_bytes(path.read_bytes()[:-10])
            with self.assertRaises(ValueError):
                batch.validate_wav(path)


if __name__ == '__main__':
    unittest.main()

import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
from batch_export import effective_settings, prepare_records, SETTINGS, compatible_settings
from collection import candidates, field_language
from normalize import normalize
from russian_speech import text_chunks, MAX_TEXT_CHARS
from voice_options import reuse_sample, MODEL, SPEED, EXAMPLES


class RussianTests(unittest.TestCase):
    def test_default_and_independent_voice_selection(self):
        self.assertEqual(effective_settings({})['voices']['ru']['name'], 'Kseniya')
        changed = effective_settings({'voice_ru': 'Eugene'})
        self.assertEqual(changed['voices']['ru']['speaker_id'], 'eugene')
        self.assertEqual(changed['voices']['de'], SETTINGS['voices']['de'])
        self.assertEqual(SETTINGS['voices']['ru']['name'], 'Kseniya')
        with self.assertRaises(ValueError):
            effective_settings({'voice_ru': 'M1'})
        old = dict(SETTINGS, voices={k: v for k, v in SETTINGS['voices'].items() if k != 'ru'})
        self.assertTrue(compatible_settings(old, SETTINGS))

    def test_russian_numbers_and_unsupported_text(self):
        self.assertEqual(normalize('Цена — 25 рублей.', 'ru'), 'Цена — двадцать пять рублей.')
        self.assertIn('двадцать пять рублей', normalize('25 ₽', 'ru'))
        self.assertIn('процента', normalize('22%', 'ru'))
        self.assertNotRegex(normalize('Дата 08.09.2026, время 13:05.', 'ru'), r'\d')
        for text in ('Нужно 10 mg.', '31.02.2026', '25:99', 'Взять 1/2 таблетки'):
            with self.assertRaises(ValueError):
                normalize(text, 'ru')

    def test_long_text_keeps_every_word_and_final_sentence(self):
        text = 'Это длинный пример. ' * 100 + 'Последнее слово.'
        chunks = list(text_chunks(text))
        self.assertEqual(' '.join(chunks).split(), text.split())
        self.assertTrue(all(len(chunk) <= MAX_TEXT_CHARS for chunk in chunks))
        self.assertEqual(chunks[-1], 'Последнее слово.')

    def test_russian_selection_accepts_cyrillic_only_when_requested(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'collection.sqlite3'
            conn = sqlite3.connect(database)
            conn.executescript('''
                create table decks(id integer,name text);
                create table fields(ntid integer,ord integer,name text);
                create table cards(id integer,nid integer,did integer,odid integer);
                create table notes(id integer,mid integer,flds text,tags text);
                insert into decks values(1,'Русский'),(2,'Deutsch');
                insert into fields values(1,0,'Front'),(1,1,'Back');
                insert into cards values(1,1,1,0),(2,2,1,0),(3,3,2,0);
            ''')
            conn.executemany('insert into notes values(?,1,?,?)', [
                (1, 'Привет [sound:old.wav]\x1fОбратная сторона', ' speak-ru '),
                (2, 'Добрый день\x1fПеревод', ' speak-ru-extra '),
                (3, 'Привет [sound:old.wav]\x1fПеревод', ' speak-ru '),
            ])
            conn.commit(); conn.close()
            original = database.read_bytes()
            rows, _ = candidates(database)
            self.assertEqual([(r['note_id'], r['language']) for r in rows], [(1, 'ru')])
            records, _, rejected = prepare_records(database, {'mode': 'tag', 'tag_ru': 'speak-ru', 'field': '*'})
            self.assertEqual([(r['note_id'], r['language']) for r in records], [(1, 'ru')])
            self.assertEqual(rejected, [])
            rows, _ = candidates(database, {'mode': 'deck', 'deck': 'Русский', 'field': 'Back', 'language': 'ru'})
            self.assertEqual([r['note_id'] for r in rows], [1, 2])
            self.assertEqual(original, database.read_bytes())
        self.assertEqual(field_language({'Russisch'}, 'Front'), ('ru_front', 'ru'))

    def test_existing_samples_are_reused_only_with_valid_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / 'M1-de.wav'; audio.write_bytes(b'saved sample')
            manifest = {'voice_model': MODEL, 'speed': SPEED, 'examples': EXAMPLES,
                        'voices': [{'code': 'M1', 'de': {'audio': audio.name, 'sha256': hashlib.sha256(audio.read_bytes()).hexdigest()}}]}
            target = root / 'copy.wav'
            self.assertIsNotNone(reuse_sample(root, manifest, {'code': 'M1'}, 'de', target))
            self.assertEqual(target.read_bytes(), audio.read_bytes())
            audio.write_bytes(b'corrupted')
            self.assertIsNone(reuse_sample(root, manifest, {'code': 'M1'}, 'de', target))

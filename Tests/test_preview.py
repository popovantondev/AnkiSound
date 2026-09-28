import hashlib
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
from normalize import clean_text, normalize
from collection import candidates, extract_collection, field_language


class SpeechTests(unittest.TestCase):
    def test_numbers_in_context(self):
        cases = [
            ('de', '20:00 Uhr', 'zwanzig Uhr'),
            ('de', '19:30 Uhr', 'neunzehn Uhr dreißig'),
            ('de', 'ab 13.00 Uhr', 'ab dreizehn Uhr'),
            ('de', 'am 09.05.2025', 'am neunten Mai zweitausendfünfundzwanzig'),
            ('de', '09.05', 'neunter Mai'),
            ('de', 'am 09.05.2025.', 'am neunten Mai zweitausendfünfundzwanzig.'),
            ('de', '2,5 kg', 'zwei Komma fünf Kilogramm'),
            ('de', '15,00 €', 'fünfzehn Euro'),
            ('de', '€ 300, -', 'dreihundert Euro'),
            ('de', '1,01 €', 'ein Euro ein Cent'),
            ('de', '2.000 Euro', 'zweitausend Euro'),
            ('de', '25%', 'fünfundzwanzig Prozent'),
            ('de', 'B2-Niveau', 'B zwei-Niveau'),
            ('de', '11–15', 'elf bis fünfzehn'),
            ('de', '2. Klasse', 'zweite Klasse'),
            ('de', 'vom 3. bis 8. Mai', 'vom dritten bis achten Mai'),
            ('de', 'zum 30. März', 'zum dreißigsten März'),
            ('de', 'Postleitzahl ist 05606.', 'Postleitzahl ist null fünf sechs null sechs.'),
            ('de', '3MM Kaution', 'drei M M Kaution'),
            ('de', 'Mitte der 90er Jahre', 'Mitte der neunziger Jahre'),
            ('de', 'den CO2-Ausstoß reduzieren', 'den C O zwei-Ausstoß reduzieren'),
            ('de', 'Business-to-Business, B2B', 'Business-to-Business, B zwei B'),
            ('de', 'B2C und B2A', 'B zwei C und B zwei A'),
            ('fr', 'Mon code postal est 55606.', 'Mon code postal est cinq cinq six zéro six.'),
            ('fr', 'Il est 19:30.', 'Il est dix-neuf heures trente.'),
            ('fr', '1:00', 'une heure'),
            ('fr', 'du 3 au 8 mai', 'du trois au huit mai'),
            ('fr', 'le 1 août', 'le premier août'),
            ('fr', 'En 2026', 'En deux mille vingt-six'),
            ('fr', 'une branche Git.', 'une branche guite.'),
            ('fr', '15,25 €', 'quinze euros vingt-cinq centimes'),
            ('fr', '2,5 kg', 'deux virgule cinq kilogrammes'),
            ('fr', '25%', 'vingt-cinq pour cent'),
        ]
        for language, source, expected in cases:
            with self.subTest(source=source, language=language):
                self.assertEqual(normalize(source, language), expected)

    def test_invalid_numbers_require_review(self):
        for source in ('31.02.2025', '25:99'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                normalize(source, 'de')

    def test_cancelled_export_cleans_up_its_own_files(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'input.colpkg', Path(temp) / 'output.sqlite3'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('collection.anki21', b'SQLite format 3\0' + bytes(100))
            before = source.read_bytes()
            with patch('shutil.copyfileobj', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                extract_collection(source, target)
            self.assertEqual(list(Path(temp).iterdir()), [source])
            self.assertEqual(source.read_bytes(), before)

    def test_failed_export_preserves_existing_temporary_files(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'bad.colpkg', Path(temp) / 'output.sqlite3'
            previous = target.with_suffix('.partial')
            previous.write_bytes(b'preserve this file')
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('collection.anki21', b'invalid database')
            with self.assertRaises(ValueError):
                extract_collection(source, target)
            self.assertFalse(target.exists())
            self.assertEqual(previous.read_bytes(), b'preserve this file')
            self.assertEqual(sorted(p.name for p in Path(temp).iterdir()), ['bad.colpkg', 'output.partial'])

    def test_html_is_not_spoken(self):
        field = '<style>x{width:100%}</style><div>Guten <b>Tag</b>.</div><br>[sound:old.mp3]<script>42</script>&amp; tschüss'
        self.assertEqual(clean_text(field), 'Guten Tag. & tschüss')

    def test_mixed_decks_and_unspecified_fields_are_excluded(self):
        self.assertIsNone(field_language({'!Немецкий', 'Французский'}, 'Front'))
        self.assertIsNone(field_language({'!Немецкий'}, 'Back'))
        self.assertEqual(field_language({'Французский'}, 'Back'), ('fr_back', 'de'))

    def test_only_sounded_fields_are_selected_and_source_stays_identical(self):
        with tempfile.TemporaryDirectory() as temp:
            database = Path(temp) / 'source.sqlite3'
            conn = sqlite3.connect(database)
            conn.executescript('''
                create table decks(id integer,name text);
                create table fields(ntid integer,ord integer,name text);
                create table cards(nid integer,did integer,odid integer);
                create table notes(id integer,mid integer,flds text);
                insert into decks values(1,'Французский'),(2,'!Немецкий');
                insert into fields values(1,0,'Front'),(1,1,'Back');
                insert into cards values(10,1,0),(10,1,0),(11,2,0);
            ''')
            conn.executemany('insert into notes values(?,1,?)', [
                (10, 'Bonjour [sound:old.wav]\x1fGuten Tag'),
                (11, 'Ohne Ton\x1fIgnored [sound:old.wav]'),
            ])
            conn.commit()
            conn.close()
            before = database.read_bytes()
            records, counts = candidates(database)
            self.assertEqual([(r['note_id'], r['field'], r['language']) for r in records], [(10, 'Front', 'fr')])
            self.assertEqual(database.read_bytes(), before)
            self.assertEqual(counts['without_sound'], 2)

    def test_export_source_is_unchanged_and_existing_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'input.colpkg', Path(temp) / 'output.sqlite3'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('collection.anki21', b'SQLite format 3\0' + bytes(100))
            before = source.read_bytes()
            extract_collection(source, target)
            self.assertEqual(source.read_bytes(), before)
            result = target.read_bytes()
            with self.assertRaises(FileExistsError):
                extract_collection(source, target)
            self.assertEqual(target.read_bytes(), result)


if __name__ == '__main__':
    unittest.main()

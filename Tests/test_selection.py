import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
from collection import candidates


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'collection.sqlite3'
        conn = sqlite3.connect(self.path)
        conn.executescript("""
            create table decks(id integer,name text);
            create table fields(ntid integer,ord integer,name text);
            create table cards(id integer,nid integer,did integer,odid integer);
            create table notes(id integer,mid integer,flds text,tags text);
            insert into decks values(1,'Deutsch'),(2,'Queue'),(3,'Other'),(4,'French'),(5,'Umschulung Wörter');
            insert into fields values(1,0,'Front'),(1,1,'Back');
            insert into cards values(1,10,1,0),(2,11,2,0),(3,12,2,0),(4,12,3,0),(5,13,2,0),(6,14,4,0),
                (7,15,3,0),(8,16,3,0),(9,17,5,0);
        """)
        conn.executemany('insert into notes values(?,1,?,?)', [
            (10, 'Hallo [sound:old.wav]\x1fBack', ''),
            (11, 'Bonjour\x1fBack', ' sound '),
            (12, 'Salut\x1fBack', ''),
            (13, 'Merci\x1fBack', ' soundish '),
            (14, 'Bonjour\x1fBack', ' fr-audio de-audio '),
            (15, 'Hallo. Привет перевод.\x1fÜbersetzung', ' custom-de '),
            (16, 'Только русский текст.\x1fÜbersetzung', ' custom-de '),
            (17, 'Guten Morgen.\x1fÜbersetzung', ' custom-de ')
        ])
        conn.commit(); conn.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_default_leaves_unsounded_notes_untouched(self):
        records, _ = candidates(self.path)
        self.assertEqual([r['note_id'] for r in records], [10])

    def test_exact_tag_selects_only_tagged_target_fields(self):
        records, _ = candidates(self.path, {'mode':'tag', 'field':'Front', 'tag_fr':'fr-audio'})
        self.assertEqual([(r['note_id'], r['language'], r['allow_new']) for r in records], [(14,'fr',True)])

    def test_arbitrary_deck_uses_one_exact_language_tag_on_front_only(self):
        records, _ = candidates(self.path, {
            'mode': 'tag', 'field': '*', 'tag_de': 'custom-de', 'tag_en': '',
            'tag_fr': '', 'tag_es': '', 'tag_ru': '',
        })
        self.assertEqual([(r['note_id'], r['field'], r['language'], r['original']) for r in records], [
            (15, 'Front', 'de', 'Hallo.'), (17, 'Front', 'de', 'Guten Morgen.'),
        ])

    def test_ambiguous_custom_tags_do_not_guess_language(self):
        connection = sqlite3.connect(self.path)
        connection.execute("update notes set tags='custom-de custom-en' where id=15")
        connection.commit()
        connection.close()
        records, _ = candidates(self.path, {
            'mode': 'tag', 'field': '*', 'tag_de': 'custom-de', 'tag_en': 'custom-en',
            'tag_fr': '', 'tag_es': '', 'tag_ru': '', 'deck': 'Other',
        })
        self.assertEqual(records, [])

    def test_cyrillic_only_front_is_skipped_for_non_russian_tag(self):
        records, counts = candidates(self.path, {
            'mode': 'tag', 'field': 'Front', 'tag_de': 'custom-de',
            'tag_fr': '', 'tag_en': '', 'tag_es': '', 'tag_ru': '',
        })
        self.assertNotIn(16, [record['note_id'] for record in records])
        self.assertEqual(counts.get('empty_or_mixed_language'), 1)

    def test_deck_excludes_notes_shared_outside_selection(self):
        records, _ = candidates(self.path, {'mode':'deck', 'deck':'Queue', 'field':'Front', 'language':'fr'})
        self.assertEqual([r['note_id'] for r in records], [11, 13])

    def test_selection_does_not_change_source(self):
        original = self.path.read_bytes()
        candidates(self.path, {'mode':'deck', 'deck':'Queue', 'field':'Back', 'language':'de'})
        self.assertEqual(self.path.read_bytes(), original)

    def test_tag_mode_does_not_touch_untagged_audio(self):
        records, _ = candidates(self.path, {'mode':'tag', 'field':'*', 'tag_fr':'fr-audio', 'tag_de':'de-audio'})
        self.assertEqual([(r['note_id'], r['field'], r['language']) for r in records], [(14,'Front','fr'), (14,'Back','de')])

    def test_existing_audio_can_be_limited_to_deck(self):
        records, _ = candidates(self.path, {'mode':'existing', 'deck':'Queue', 'field':'Front'})
        self.assertEqual(records, [])

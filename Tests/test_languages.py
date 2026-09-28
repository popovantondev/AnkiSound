import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
from normalize import normalize
from collection import field_language
from batch_export import compatible_settings, effective_settings


class LanguagesTests(unittest.TestCase):
    def test_en_es_numbers(self):
        self.assertEqual(normalize('The price is $25.50.', 'en'), 'The price is twenty-five dollars and fifty cents.')
        self.assertEqual(normalize('El precio es 25,50 €.', 'es'), 'El precio es veinticinco euros con cincuenta céntimos.')
        self.assertEqual(normalize('25%', 'es'), 'veinticinco por ciento')
        self.assertEqual(normalize('13:05', 'en'), 'thirteen oh five')
        self.assertEqual(normalize('13:05', 'es'), 'trece y cinco')
        self.assertEqual(normalize('B2', 'en'), 'B two')
        self.assertEqual(normalize('B2', 'es'), 'B dos')

    def test_ambiguous_dates_are_not_guessed(self):
        for language in ('en','es'):
            with self.assertRaises(ValueError):
                normalize('01/02/2025', language)
            with self.assertRaises(ValueError):
                normalize('25:77', language)

    def test_deck_language_aliases(self):
        self.assertEqual(field_language({'English'}, 'Front'), ('en_front','en'))
        self.assertEqual(field_language({'Español'}, 'Front'), ('es_front','es'))
        self.assertEqual(field_language({'Umschulung Wörter'}, 'Front'), ('de_front','de'))
        self.assertEqual(field_language({'ПРАВИЛА немецкого'}, 'Front'), ('de_front','de'))
        self.assertIsNone(field_language({'English','Español'}, 'Front'))

    def test_adding_languages_does_not_invalidate_saved_voice_settings(self):
        saved = {'steps':12, 'voices':{'de':{'name':'M5'}}}
        current = {'steps':12, 'voices':{'de':{'name':'M5'}, 'en':{'name':'M1'}}}
        self.assertTrue(compatible_settings(saved, current))
        current['voices']['de']['name'] = 'M1'
        self.assertFalse(compatible_settings(saved, current))

    def test_selected_voice_is_saved_for_each_language(self):
        settings = effective_settings({'voice_de': 'M5', 'voice_es': 'F1'})
        self.assertEqual(settings['voices']['de']['speaker_id'], 9)
        self.assertEqual(settings['voices']['es']['speaker_id'], 0)
        self.assertEqual(settings['voices']['fr']['name'], 'M1')

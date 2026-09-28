import json
import unittest
from pathlib import Path


class LocalizationTests(unittest.TestCase):
    def test_all_languages_have_matching_nonempty_resources(self):
        root = Path(__file__).resolve().parents[1]
        languages = [json.loads((root / 'Resources/Interface' / (lang + '.json')).read_text()) for lang in ('de', 'en', 'ru')]
        self.assertEqual(set(languages[0]), set(languages[1]))
        self.assertEqual(set(languages[0]), set(languages[2]))
        for language in languages:
            self.assertTrue(all(isinstance(v, str) and v.strip() for v in language.values()))
        for lang in ('de', 'en', 'ru'):
            guide = (root / 'docs' / ('Guide-' + lang + '.html')).read_text()
            self.assertIn('SETUP.command', guide)
            self.assertIn('sound', guide)
            self.assertIn('3.9', guide)

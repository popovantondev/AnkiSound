import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
from card_listen import SAMPLE_LIMIT, selected_records


class CardListeningTests(unittest.TestCase):
    def test_uses_only_two_eligible_records_in_stable_order(self):
        records = [
            {'note_id': 3, 'field_order': 0, 'original': 'Third card', 'speech_source': 'Third card', 'language': 'en'},
            {'note_id': 1, 'field_order': 1, 'original': 'bad', 'speech_source': 'bad', 'language': 'en'},
            {'note_id': 1, 'field_order': 0, 'original': 'First card', 'speech_source': 'First card', 'language': 'en'},
            {'note_id': 2, 'field_order': 0, 'original': 'Second card', 'speech_source': 'Second card', 'language': 'en'},
        ]
        with patch('card_listen.candidates', return_value=(records, {})), patch('card_listen.normalize', side_effect=lambda text, language: text + ' spoken'):
            chosen = selected_records('unused.sqlite3', {'mode': 'existing'})
        self.assertEqual(len(chosen), SAMPLE_LIMIT)
        self.assertEqual([record['note_id'] for record in chosen], [1, 2])
        self.assertEqual(chosen[0]['spoken'], 'First card spoken')

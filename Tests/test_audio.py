import hashlib
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Sources'))
from audio import UnfinishedAudio, concatenate, generate, save_complete_audio, write_pcm
from normalize import clean_text

SETTINGS = json.loads((ROOT / 'Resources/speech.json').read_text())


class AudioTests(unittest.TestCase):
    def test_quiet_consonants_and_full_sample_sequence_are_preserved(self):
        samples = np.concatenate((np.full(200, .2), np.full(300, .005), np.full(150, -.15), np.zeros(200))).astype(np.float32)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'complete.wav'
            metadata = save_complete_audio(samples, 1000, path, SETTINGS)
            with wave.open(str(path)) as stream:
                pcm = stream.readframes(stream.getnframes())
            lead, trail = metadata['leading_frames'], metadata['trailing_frames']
            spoken = pcm[lead * 2:-trail * 2]
            expected = (samples * 2 * 32767).astype('<i2').tobytes()
            self.assertEqual(spoken, expected)
            self.assertEqual(hashlib.sha256(spoken).hexdigest(), metadata['speech_pcm_sha256'])
            self.assertEqual(metadata['saved_frames'], len(samples) + lead + trail)
            self.assertEqual(pcm[-trail * 2:], bytes(trail * 2))

    def test_unfinished_waveform_is_rejected_before_publishing(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'bad.wav'
            with self.assertRaises(UnfinishedAudio):
                save_complete_audio(np.full(1000, .1), 1000, target, SETTINGS)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_playlist_preserves_every_frame_including_last_recording(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = b'\x11\x01' * 100, b'\x22\x02' * 175
            write_pcm(root / 'one.wav', first, 1000)
            write_pcm(root / 'two.wav', second, 1000)
            concatenate([{'audio': 'one.wav'}, {'audio': 'two.wav'}], root, root / 'all.wav', .35)
            with wave.open(str(root / 'all.wav')) as stream:
                self.assertEqual(stream.readframes(stream.getnframes()), first + bytes(700) + second)
                self.assertEqual(stream.getnframes(), 625)

    def test_existing_audio_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'existing.wav'
            target.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                write_pcm(target, b'\0\0', 22050)
            self.assertEqual(target.read_bytes(), b'original')

    def test_truncated_synthesis_is_retried_without_dropping_final_sentence(self):
        class Engine:
            def __init__(self): self.calls = []
            def generate(self, text, config):
                self.calls.append((text, config.silence_scale, config.speed))
                samples = np.full(300, .2)
                if len(self.calls) > 1:
                    samples = np.concatenate((samples, np.zeros(200)))
                return SimpleNamespace(samples=samples, sample_rate=1000)
        engine = Engine()
        with tempfile.TemporaryDirectory() as temp:
            metadata = generate(engine, 'Erster Satz. Letztes Wort', 'de', Path(temp) / 'test.wav', SETTINGS)
            self.assertEqual(metadata['attempts'], 2)
            self.assertEqual(len(engine.calls), 2)
            for text, silence, speed in engine.calls:
                self.assertEqual(text, 'Erster Satz. Letztes Wort.')
                self.assertEqual(silence, 1.0)
                self.assertAlmostEqual(speed, .82, places=6)

    def test_different_sample_rates_are_not_silently_resampled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_pcm(root / 'one.wav', bytes(100), 22050)
            write_pcm(root / 'two.wav', bytes(100), 44100)
            with self.assertRaises(ValueError):
                concatenate([{'audio': 'one.wav'}, {'audio': 'two.wav'}], root, root / 'all.wav', .35)
            self.assertFalse((root / 'all.wav').exists())

    def test_block_pauses_do_not_damage_french_accents(self):
        text = '<div>e\u0301cole</div><div>Une le\u00adçon.</div>'
        self.assertEqual(clean_text(text), 'école Une leçon.')
        self.assertEqual(clean_text(text, pause_blocks=True), 'école. Une leçon.')


if __name__ == '__main__':
    unittest.main()

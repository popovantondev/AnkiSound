"""Offline Russian synthesis with a locally installed Silero model."""
import re
import hashlib
from pathlib import Path

import numpy as np

RUSSIAN_VOICES = ('Kseniya', 'Xenia', 'Baya', 'Aidar', 'Eugene')
SAMPLE_RATE = 48000
MAX_TEXT_CHARS = 450


def text_chunks(text):
    # Keep every word while staying below the model's per-request text limit.
    for sentence in re.split(r'(?<=[.!?…])\s+', text):
        words, size = [], 0
        for word in sentence.split():
            if len(word) > MAX_TEXT_CHARS:
                raise ValueError('Russian word exceeds the model text limit')
            if words and size + len(word) + 1 > MAX_TEXT_CHARS:
                yield ' '.join(words)
                words, size = [], 0
            words.append(word)
            size += len(word) + 1
        if words:
            yield ' '.join(words)


class RussianSpeech:
    def __init__(self, model_path, expected_sha256):
        digest = hashlib.sha256()
        with Path(model_path).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError('Russian model checksum mismatch')
        import torch
        self.torch = torch
        torch.set_num_threads(2)
        self.model = torch.package.PackageImporter(str(Path(model_path))).load_pickle('tts_models', 'model')
        self.model.to(torch.device('cpu'))

    def synthesize(self, text, voice):
        if voice not in RUSSIAN_VOICES:
            raise ValueError('Unknown Russian voice')
        chunks = []
        with self.torch.inference_mode():
            for chunk in text_chunks(text):
                audio = self.model.apply_tts(text=chunk, speaker=voice.lower(), sample_rate=SAMPLE_RATE,
                                             put_accent=True, put_yo=True)
                if chunks:
                    chunks.append(np.zeros(round(SAMPLE_RATE * 0.2), dtype=np.float32))
                chunks.append(audio.detach().cpu().numpy())
        if not chunks:
            raise ValueError('Empty Russian speech text')
        return np.concatenate(chunks), SAMPLE_RATE

"""Synthesize complete speech and preserve every generated sample when saving."""
import hashlib
import json
import os
import re
import tempfile
import time
import wave
from pathlib import Path

import numpy as np


def complete_sentence(text):
    text = text.strip()
    if not text:
        raise ValueError('Empty speech text')
    if not re.search(r'[.!?…][\]»”\"\')]*$', text):
        text += '.'
    return text


def create_engine(root, settings, language):
    voice = settings['voices'][language]
    if voice['backend'] == 'silero':
        from russian_speech import RussianSpeech
        metadata = json.loads((root / 'Resources/models.json').read_text())[voice['model']]
        return RussianSpeech(root / 'models' / voice['model'] / voice['model_file'], metadata['sha256'])
    import sherpa_onnx
    folder = root / 'models' / voice['model']
    if voice['backend'] == 'supertonic':
        model = sherpa_onnx.OfflineTtsModelConfig(
            supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
                duration_predictor=str(folder / 'duration_predictor.int8.onnx'),
                text_encoder=str(folder / 'text_encoder.int8.onnx'),
                vector_estimator=str(folder / 'vector_estimator.int8.onnx'),
                vocoder=str(folder / 'vocoder.int8.onnx'),
                tts_json=str(folder / 'tts.json'),
                unicode_indexer=str(folder / 'unicode_indexer.bin'),
                voice_style=str(folder / 'voice.bin'),
            ), num_threads=2, provider='cpu')
    elif voice['backend'] == 'piper':
        model = sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(folder / voice['model_file']), tokens=str(folder / 'tokens.txt'),
                data_dir=str(folder / 'espeak-ng-data'),
            ), num_threads=2, provider='cpu')
    else:
        raise ValueError('Unsupported voice engine')
    config = sherpa_onnx.OfflineTtsConfig(model=model, max_num_sentences=1, silence_scale=1.0)
    if not config.validate():
        raise ValueError('Voice configuration is invalid')
    return sherpa_onnx.OfflineTts(config)


def generation_config(language, settings):
    import sherpa_onnx
    voice = settings['voices'][language]
    config = sherpa_onnx.GenerationConfig()
    config.sid = voice['speaker_id']
    config.speed = voice['speed']
    config.num_steps = settings['steps']
    # Quiet consonants and sentence endings must never be shortened.
    config.silence_scale = 1.0
    config.extra = {'lang': language}
    return config


def write_pcm(destination, pcm, rate):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Audio already exists')
    descriptor, name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.partial', dir=destination.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        with wave.open(str(temporary), 'wb') as output:
            output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
            output.writeframes(pcm)
        # Hard linking atomically publishes a complete file without replacing a result.
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


class UnfinishedAudio(ValueError):
    pass


def save_complete_audio(samples, rate, destination, settings):
    samples = np.asarray(samples, dtype=np.float32)
    if samples.ndim != 1 or not len(samples) or not np.isfinite(samples).all():
        raise ValueError('Invalid audio')
    peak = float(np.max(np.abs(samples)))
    if peak < 0.001:
        raise ValueError('Silent audio')
    active = np.flatnonzero(np.abs(samples) > 0.01)
    tail = (len(samples) - 1 - active[-1]) / rate if len(active) else len(samples) / rate
    # Padding cannot recover a missing phoneme: reject a visibly unfinished waveform.
    if tail < settings['minimum_source_tail_seconds']:
        raise UnfinishedAudio('Speech is active at the end of the generated waveform')
    gain = min(2.0, 0.95 / peak)
    speech_pcm = (samples * gain * 32767).astype('<i2').tobytes()
    lead = round(rate * settings['leading_seconds'])
    trail = round(rate * settings['trailing_seconds'])
    pcm = b'\0\0' * lead + speech_pcm + b'\0\0' * trail
    write_pcm(destination, pcm, rate)
    return {'duration': round(len(pcm) / (2 * rate), 3), 'speech_duration': round(len(samples) / rate, 3),
            'source_frames': len(samples), 'saved_frames': len(pcm) // 2,
            'leading_frames': lead, 'trailing_frames': trail,
            'source_tail_seconds': round(float(tail), 4), 'sample_rate': rate,
            'gain': round(gain, 4), 'speech_pcm_sha256': hashlib.sha256(speech_pcm).hexdigest(),
            'sha256': hashlib.sha256(Path(destination).read_bytes()).hexdigest()}


def generate(engine, text, language, destination, settings):
    started = time.monotonic()
    spoken = complete_sentence(text)
    for attempt in range(1, settings['maximum_attempts'] + 1):
        if settings['voices'][language]['backend'] == 'silero':
            samples, rate = engine.synthesize(spoken, settings['voices'][language]['name'])
        else:
            audio = engine.generate(spoken, generation_config(language, settings))
            samples, rate = audio.samples, audio.sample_rate
        try:
            result = save_complete_audio(samples, rate, destination, settings)
            break
        except UnfinishedAudio:
            if attempt == settings['maximum_attempts']:
                raise
    result['attempts'] = attempt
    result.update(generation_seconds=round(time.monotonic() - started, 3), generated_text=spoken,
                  voice=settings['voices'][language]['name'], speed=settings['voices'][language]['speed'])
    return result


def concatenate(records, directory, destination, gap_seconds):
    if not records:
        raise ValueError('Empty playlist')
    rate, chunks = None, []
    for index, record in enumerate(records):
        with wave.open(str(directory / record['audio']), 'rb') as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                raise ValueError('Unsupported audio format')
            if rate is None:
                rate = source.getframerate()
            if source.getframerate() != rate:
                raise ValueError('Playlist sample rates must match')
            pcm = source.readframes(source.getnframes())
        if index:
            chunks.append(b'\0\0' * round(rate * gap_seconds))
        chunks.append(pcm)
    write_pcm(destination, b''.join(chunks), rate)

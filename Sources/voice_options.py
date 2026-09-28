"""Create multilingual listening pages, reusing verified saved samples."""
import argparse
import hashlib
import html
import json
import os
import shutil
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from audio import create_engine, generate
from normalize import normalize
from russian_speech import RUSSIAN_VOICES

ROOT = Path(__file__).resolve().parents[1]
BASE_SETTINGS = json.loads((ROOT / 'Resources/speech.json').read_text())
MODEL = BASE_SETTINGS['voices']['de']['model']
SPEED = 0.88
LANGUAGES = ('de', 'fr', 'en', 'es')
EXAMPLES = {
    'de': 'Entschuldigung, ist hier noch frei?',
    'fr': 'Bonjour. Je parle allemand.',
    'en': 'Hello. The lesson starts at thirteen oh five. The price is twenty-five dollars.',
    'es': 'Hola. La clase empieza a las trece y cinco. El precio es veinticinco euros.',
    'ru': 'Привет! Это пример русской озвучки. Урок начинается в 13:05. До встречи!',
}
VOICES = [(f'F{i + 1}', i, 'femaleVoices') for i in range(5)] + [(f'M{i + 1}', i + 5, 'maleVoices') for i in range(5)]


def atomic_text(path, content):
    temporary = path.with_suffix(path.suffix + '.partial')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def settings_for(code, speaker_id):
    settings = deepcopy(BASE_SETTINGS)
    for language in LANGUAGES:
        settings['voices'][language].update(speaker_id=speaker_id, name=code, speed=SPEED)
    return settings


def report(records, directory):
    for language in ('de', 'en', 'ru'):
        labels = json.loads((ROOT / 'Resources/Interface' / (language + '.json')).read_text())
        groups = []
        for group in ('femaleVoices', 'maleVoices', 'russianVoices'):
            cards = []
            for record in records:
                if record['gender'] != group:
                    continue
                rows = []
                for speech in (*LANGUAGES, 'ru'):
                    if speech not in record:
                        continue
                    item = record[speech]
                    rows.append('<h3>' + html.escape(labels[speech]) + '</h3><p>' +
                                html.escape(item.get('generated_text', EXAMPLES[speech])) +
                                '</p><audio controls preload="none" src="' + html.escape(item['audio'], quote=True) + '"></audio>')
                cards.append('<article><h2>' + html.escape(record['code']) + '</h2>' + ''.join(rows) + '</article>')
            groups.append('<section><h1>' + html.escape(labels[group]) + '</h1><div class="grid">' + ''.join(cards) + '</div></section>')
        page = ('<!doctype html><html lang="' + language + '"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                '<title>' + html.escape(labels['sampleTitle']) + '</title><style>'
                'body{font:17px system-ui;max-width:1100px;margin:36px auto;padding:0 20px;color:#17202a;background:#f7f8fa}'
                '.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}'
                'article{background:#fff;border-radius:14px;padding:18px}h2{margin:0}h3{font-size:15px;margin:22px 0 6px}'
                'p{line-height:1.45}audio{width:100%}nav a{margin-right:20px}</style>'
                '<nav><a href="index-de.html">Deutsch</a><a href="index-en.html">English</a><a href="index-ru.html">Русский</a></nav>'
                '<h1>' + html.escape(labels['sampleTitle']) + '</h1><p>' + html.escape(labels['sampleNote']) + '</p>' + ''.join(groups) + '</html>')
        atomic_text(directory / ('index-' + language + '.html'), page)
        if language == 'ru':
            atomic_text(directory / 'index.html', page)


def reuse_sample(directory, manifest, record, language, destination):
    if not directory or manifest.get('voice_model') != MODEL or manifest.get('speed') != SPEED:
        return None
    if manifest.get('examples', {}).get(language) != EXAMPLES[language]:
        return None
    saved = next((item for item in manifest.get('voices', []) if item['code'] == record['code']), {})
    sample = saved.get(language)
    if not sample or Path(sample['audio']).name != sample['audio']:
        return None
    path = directory / sample['audio']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != sample.get('sha256'):
        return None
    shutil.copyfile(path, destination)
    return dict(sample, audio=destination.name)


def run(reuse=None):
    output_root = ROOT / 'output'
    output_root.mkdir(exist_ok=True)
    manifest = json.loads((reuse / 'manifest.json').read_text()) if reuse else {}
    directory = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('voice-options-%Y%m%d-%H%M%S-'), dir=output_root))
    records, engine = [], None
    for code, speaker_id, gender in VOICES:
        settings = settings_for(code, speaker_id)
        record = {'code': code, 'speaker_id': speaker_id, 'gender': gender}
        for language in LANGUAGES:
            destination = directory / f'{code}-{language}.wav'
            sample = reuse_sample(reuse, manifest, record, language, destination)
            if sample is None:
                if engine is None:
                    engine = create_engine(ROOT, settings, language)
                sample = generate(engine, EXAMPLES[language], language, destination, settings)
                sample['audio'] = destination.name
            record[language] = sample
        records.append(record)
        print(json.dumps({'voice': code}), flush=True)
    russian_engine = create_engine(ROOT, BASE_SETTINGS, 'ru')
    for voice in RUSSIAN_VOICES:
        settings = deepcopy(BASE_SETTINGS)
        settings['voices']['ru'].update(name=voice, speaker_id=voice.lower())
        destination = directory / f'{voice}-ru.wav'
        sample = generate(russian_engine, normalize(EXAMPLES['ru'], 'ru'), 'ru', destination, settings)
        sample['audio'] = destination.name
        records.append({'code': voice, 'gender': 'russianVoices', 'ru': sample})
        print(json.dumps({'voice': voice}), flush=True)
    report(records, directory)
    atomic_text(directory / 'manifest.json', json.dumps({'voice_model': MODEL, 'russian_model': BASE_SETTINGS['voices']['ru']['model'],
                'speed': SPEED, 'examples': EXAMPLES, 'voices': records, 'anki_collection_changed': False}, ensure_ascii=False, indent=2))
    print(directory / 'index.html')
    return directory


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse', type=Path)
    args = parser.parse_args()
    run(args.reuse)

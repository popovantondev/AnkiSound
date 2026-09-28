"""Install pinned public dependencies and verified voice assets."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = os.environ.get('ANKI_SOUND_LANGUAGE', 'de')
MESSAGES = json.loads((ROOT / 'Resources/setup.json').read_text())
TEXT = MESSAGES.get(LANGUAGE, MESSAGES['de'])


def download_model(name, metadata):
    folder = ROOT / 'models' / name
    if folder.is_dir():
        required = [folder / filename for filename in metadata['required']]
        if not all(path.exists() for path in required):
            raise ValueError('Existing model is incomplete')
        return
    cache = ROOT / '.cache'
    cache.mkdir(exist_ok=True)
    archive_name = metadata.get('filename', name + '.tar.bz2')
    url = metadata.get('url', 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/' + archive_name)
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        temporary = Path(temporary)
        archive = temporary / archive_name
        digest = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=60) as source, archive.open('xb') as target:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != metadata['sha256']:
            raise ValueError('Model checksum mismatch')
        if metadata.get('format') == 'file':
            extracted = temporary / folder.name
            extracted.mkdir()
            archive.rename(extracted / archive_name)
            extracted.rename(folder)
            return
        with tarfile.open(archive) as package:
            for member in package.getmembers():
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts or not (member.isdir() or member.isfile()):
                    raise ValueError('Unsafe model archive')
            package.extractall(temporary)
        extracted = temporary / folder.name
        if not all((extracted / filename).is_file() for filename in metadata['required']):
            raise ValueError('Model file is missing')
        extracted.rename(folder)


def main():
    if not (3, 9) <= sys.version_info[:2] <= (3, 12):
        raise RuntimeError('Python 3.9–3.12 is required')
    print(TEXT['install'], flush=True)
    environment = ROOT / '.venv'
    if not environment.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(environment)], check=True)
    interpreter = environment / 'bin/python'
    subprocess.run([str(interpreter), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir',
                    '-r', str(ROOT / 'requirements.txt')], check=True)
    (ROOT / 'models').mkdir(exist_ok=True)
    used = {v['model'] for v in json.loads((ROOT / 'Resources/speech.json').read_text())['voices'].values()}
    for name, expected in json.loads((ROOT / 'Resources/models.json').read_text()).items():
        if name not in used:
            continue
        download_model(name, expected)
    print(TEXT['ready'])


if __name__ == '__main__':
    main()

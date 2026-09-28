"""Package a verified source release without private data or installed models."""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def validate_application(info, version):
    if info.get('CFBundleShortVersionString') != version:
        raise ValueError('Invalid portable application version')
    project_root = info.get('ProjectRootRelative')
    if not isinstance(project_root, str) or not project_root or Path(project_root).is_absolute():
        raise ValueError('Invalid portable application project path')


def main():
    version = (ROOT / 'VERSION').read_text().strip()
    if git('branch', '--show-current') != 'main' or git('status', '--porcelain'):
        raise RuntimeError('Release requires a clean main branch')
    destination = ROOT / 'releases' / ('v' + version)
    if destination.exists() or git('tag', '--list', 'v' + version):
        raise FileExistsError('Release version already exists')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_app.py')], check=True)
    destination.parent.mkdir(exist_ok=True)
    (ROOT / '.cache').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='release-', dir=ROOT / '.cache') as temporary:
        temporary = Path(temporary)
        output = temporary / 'output'
        output.mkdir()
        prefix = 'Anki_SOUND-v' + version
        archive = output / (prefix + '-source.zip')
        subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=zip', '--prefix=' + prefix + '/',
                        '--output=' + str(archive), 'HEAD'], check=True)
        with zipfile.ZipFile(archive) as package:
            if package.testzip():
                raise ValueError('Invalid release archive')
            package.extractall(temporary / 'check')
        checkout = temporary / 'check' / prefix
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'Tests', '-v'], cwd=checkout, check=True)
        subprocess.run([sys.executable, '-m', 'compileall', '-q', 'Sources', 'scripts', 'Tests'], cwd=checkout, check=True)
        application = checkout / 'previews' / 'Anki SOUND.app'
        application.parent.mkdir()
        shutil.copytree(ROOT / 'previews' / 'Anki SOUND.app', application)
        import plistlib
        with (application / 'Contents/Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        validate_application(info, version)
        for language in ('de', 'en', 'ru'):
            if not (checkout / 'docs' / ('Guide-' + language + '.html')).exists():
                raise ValueError('Missing user guide')
        package = output / (prefix + '-macOS-AppleSilicon.zip')
        with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for file in sorted(checkout.rglob('*')):
                if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc':
                    bundle.write(file, str(file.relative_to(checkout.parent)))
        with zipfile.ZipFile(package) as bundle:
            if bundle.testzip():
                raise ValueError('Invalid application package')
        metadata = {'version': version, 'commit': git('rev-parse', 'HEAD'),
                    'platform': platform.system() + ' ' + platform.mac_ver()[0] + ' ' + platform.machine(),
                    'python': platform.python_version(), 'contents': 'Native application and source; setup instructions included. Python, dependencies and models installed separately. No user data.'}
        (output / 'BUILD_INFO.txt').write_text(json.dumps(metadata, indent=2) + '\n')
        shutil.copyfile(ROOT / 'CHANGELOG.md', output / 'RELEASE_NOTES.md')
        checksums = []
        for path in sorted(output.iterdir()):
            checksums.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
        (output / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n')
        output.rename(destination)
    subprocess.run(['git', '-C', str(ROOT), 'tag', '-a', 'v' + version, '-m', 'Release ' + version], check=True)
    backup_root = ROOT / 'backups'
    backup_root.mkdir(exist_ok=True)
    backup = backup_root / datetime.now().strftime('Anki_SOUND-%Y%m%d-%H%M%S-%f.bundle')
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'create', str(backup), '--all'], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'verify', str(backup)], check=True)
    print('Release and verified backup created.')


if __name__ == '__main__':
    main()

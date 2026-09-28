"""Build a local macOS prototype using system frameworks."""
import plistlib
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path)
args = parser.parse_args()
version = (ROOT / 'VERSION').read_text().strip()
app = args.output.resolve() if args.output else ROOT / 'previews' / 'Anki SOUND.app'
icon_name = 'AppIcon-' + version
contents = app / 'Contents'
(contents / 'MacOS').mkdir(parents=True, exist_ok=True)
(contents / 'Resources').mkdir(exist_ok=True)
subprocess.run(['xcrun', 'swiftc', '-target', 'arm64-apple-macosx13.0', str(ROOT / 'Sources/App.swift'), '-o', str(contents / 'MacOS/AnkiSound'), '-framework', 'Cocoa'], check=True)
with (contents / 'Info.plist').open('wb') as stream:
    plistlib.dump({'CFBundleExecutable': 'AnkiSound', 'CFBundleIdentifier': 'de.antonpopov.AnkiSound',
                  'CFBundleName': 'Anki SOUND', 'CFBundlePackageType': 'APPL', 'CFBundleVersion': version,
                  'CFBundleShortVersionString': version, 'NSHighResolutionCapable': True,
                  'ProjectRootRelative': os.path.relpath(ROOT, app.parent), 'CFBundleIconFile': icon_name + '.icns',
                  'CFBundleDevelopmentRegion': 'de', 'CFBundleLocalizations': ['de', 'en', 'ru']}, stream)
shutil.copytree(ROOT / 'Resources/Interface', contents / 'Resources/Interface', dirs_exist_ok=True)
source = ROOT / 'Assets/AppIcon.png'
if source.exists():
    iconset = ROOT / '.cache/AppIcon.iconset'
    iconset.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = size * scale
            suffix = '@2x' if scale == 2 else ''
            subprocess.run(['sips', '-z', str(pixels), str(pixels), str(source), '--out', str(iconset / f'icon_{size}x{size}{suffix}.png')], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(contents / 'Resources' / (icon_name + '.icns'))], check=True)
subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True)
print(app)

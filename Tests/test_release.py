import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import release


class ReleaseTests(unittest.TestCase):
    def test_portable_application_metadata_accepts_relative_project_root(self):
        release.validate_application({
            'CFBundleShortVersionString': '3.4.10',
            'ProjectRootRelative': '../..',
        }, '3.4.10')

    def test_portable_application_metadata_rejects_wrong_version(self):
        with self.assertRaisesRegex(ValueError, 'version'):
            release.validate_application({
                'CFBundleShortVersionString': '3.4.3',
                'ProjectRootRelative': '../..',
            }, '3.4.10')

    def test_portable_application_metadata_rejects_absolute_project_path(self):
        with self.assertRaisesRegex(ValueError, 'project path'):
            release.validate_application({
                'CFBundleShortVersionString': '3.4.10',
                'ProjectRootRelative': str(Path(__file__).resolve().parents[1]),
            }, '3.4.10')


if __name__ == '__main__':
    unittest.main()

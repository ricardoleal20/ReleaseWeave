"""Distribution regressions use actual archives and bytes, never remote publishing."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / 'scripts/dist.py'


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.binary = self.root / 'releaseweave'
        self.binary.write_bytes(b'test executable bytes')
        self.binary.chmod(0o755)
        self.output = self.root / 'out'

    def invoke(self, *args):
        return subprocess.run([sys.executable, str(DIST), *args], cwd=REPO, text=True, capture_output=True)

    def package(self, target):
        result = self.invoke('package', '--binary', str(self.binary), '--tag', 'v0.2.0', '--target', target, '--output', str(self.output))
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(result.stdout.strip())

    def test_posix_archive_contains_executable_license_and_both_examples(self):
        path = self.package('aarch64-apple-darwin')
        with tarfile.open(path) as archive:
            base = 'releaseweave-v0.2.0-aarch64-apple-darwin/'
            self.assertEqual(archive.extractfile(base + 'releaseweave').read(), self.binary.read_bytes())
            self.assertTrue(archive.getmember(base + 'releaseweave').mode & 0o111)
            self.assertIn(base + 'LICENSE', archive.getnames())
            self.assertIn(base + 'docs/QUICKSTART.md', archive.getnames())
            self.assertIn(base + 'examples/single-repo/Cargo.toml', archive.getnames())
            self.assertIn(base + 'examples/monorepo/packages/web/package.json', archive.getnames())

    def test_windows_archive_contains_exe(self):
        path = self.package('x86_64-pc-windows-msvc')
        with zipfile.ZipFile(path) as archive:
            self.assertIn('releaseweave-v0.2.0-x86_64-pc-windows-msvc/releaseweave.exe', archive.namelist())

    def test_unsupported_target_and_unsafe_tag_are_rejected(self):
        for tag, target in [('v0.2.0/../bad', 'aarch64-apple-darwin'), ('v0.2.0', '../bad')]:
            result = self.invoke('package', '--binary', str(self.binary), '--tag', tag, '--target', target, '--output', str(self.output))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(self.output.exists())

    def test_checksums_cover_all_files_and_detect_corruption(self):
        self.output.mkdir()
        asset = self.output / 'asset.tar.gz'
        asset.write_bytes(b'archive')
        result = self.invoke('checksums', '--directory', str(self.output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(hashlib.sha256(b'archive').hexdigest(), (self.output / 'SHA256SUMS').read_text())
        self.assertEqual(self.invoke('verify', '--directory', str(self.output)).returncode, 0)
        asset.write_bytes(b'corrupt')
        self.assertNotEqual(self.invoke('verify', '--directory', str(self.output)).returncode, 0)

    def test_release_validation_requires_five_archives_and_both_installers(self):
        self.output.mkdir()
        (self.output / 'install.sh').write_text('installer')
        result = self.invoke('verify', '--directory', str(self.output), '--tag', 'v0.2.0')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()

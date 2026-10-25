"""POSIX installer safety checks against real archives served over loopback HTTP."""
import functools
import http.server
from pathlib import Path
import platform
import subprocess
import tempfile
import threading
import unittest
import dist


@unittest.skipIf(platform.system() == 'Windows', 'POSIX installer; native Windows smoke runs in release CI')
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.served = self.root / 'assets'
        self.binary = self.root / 'releaseweave'
        self.binary.write_text('#!/bin/sh\nprintf "releaseweave 0.2.0\\n"\n')
        self.binary.chmod(0o755)
        osname = 'apple-darwin' if platform.system() == 'Darwin' else 'unknown-linux-gnu'
        arch = 'aarch64' if platform.machine() in ['arm64', 'aarch64'] else 'x86_64'
        self.target = arch + '-' + osname
        dist.package(self.binary, 'v0.2.0', self.target, self.served)
        dist.checksums(self.served)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(self.served))
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.prefix = self.root / 'user prefix with spaces'

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def invoke(self, version='v0.2.0'):
        return subprocess.run(['sh', str(dist.REPO / 'install.sh'), '--version', version,
            '--prefix', str(self.prefix), '--base-url', 'http://127.0.0.1:' + str(self.server.server_address[1])], text=True, capture_output=True)

    def test_installs_verified_binary_to_a_prefix_with_spaces(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        binary = self.prefix / 'bin/releaseweave'
        self.assertEqual(subprocess.check_output([str(binary), '--version'], text=True).strip(), 'releaseweave 0.2.0')

    def test_corrupt_archive_does_not_replace_existing_installation(self):
        (self.prefix / 'bin').mkdir(parents=True)
        installed = self.prefix / 'bin/releaseweave'
        installed.write_bytes(b'previous installation')
        next(self.served.glob('*.tar.gz')).write_bytes(b'corrupt')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Checksum mismatch', result.stderr)
        self.assertEqual(installed.read_bytes(), b'previous installation')

    def test_unsafe_version_is_rejected_before_installing(self):
        result = self.invoke('v0.2.0/../../bad')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Invalid release version', result.stderr)
        self.assertFalse(self.prefix.exists())


if __name__ == '__main__':
    unittest.main()

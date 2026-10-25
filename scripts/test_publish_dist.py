"""Publish only complete, remotely verified native distributions; gh is the API boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import dist


class PublishDistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.assets = self.root / 'assets'
        self.assets.mkdir()
        for target in dist.TARGETS:
            (self.assets / dist.asset_name('v0.2.0', target)).write_bytes(b'native asset')
        for name in ['install.sh', 'install.ps1', 'QUICKSTART.md']:
            (self.assets / name).write_text('release document')
        dist.checksums(self.assets)
        self.remote = self.root / 'remote'
        shutil.copytree(self.assets, self.remote)
        self.notes = self.root / 'notes.md'
        self.notes.write_text('First ReleaseWeave release')
        binary_dir = self.root / 'bin'
        binary_dir.mkdir()
        gh = binary_dir / 'gh'
        gh.write_text('''#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
args = sys.argv[1:]
with open(os.environ['GH_CALLS'], 'a') as out:
    out.write(json.dumps(args) + '\\n')
remote = pathlib.Path(os.environ['REMOTE_ASSETS'])
if args[0] == 'api':
    state = os.environ['RELEASE_STATE']
    if state != 'absent':
        print('v0.2.0\\t' + ('true' if state == 'draft' else 'false'))
elif args[:2] == ['release', 'upload']:
    for arg in args[3:]:
        path = pathlib.Path(arg)
        if path.is_file():
            shutil.copyfile(path, remote / path.name)
elif args[:2] == ['release', 'download']:
    destination = pathlib.Path(args[args.index('--dir') + 1])
    destination.mkdir(parents=True, exist_ok=True)
    for path in remote.iterdir():
        shutil.copyfile(path, destination / path.name)
    if os.environ.get('CORRUPT_REMOTE'):
        next(destination.glob('*.tar.gz')).write_bytes(b'corrupt')
''')
        gh.chmod(0o755)
        self.binary_dir = binary_dir

    def invoke(self, state='draft', corrupt=False):
        env = dict(os.environ, PATH=str(self.binary_dir) + os.pathsep + os.environ['PATH'],
            GH_CALLS=str(self.root / 'calls.jsonl'), REMOTE_ASSETS=str(self.remote),
            RELEASE_STATE=state, GH_REPO='ricardoleal20/ReleaseWeave')
        if corrupt:
            env['CORRUPT_REMOTE'] = '1'
        result = subprocess.run([sys.executable, str(dist.REPO / 'scripts/publish_dist.py'),
            '--tag', 'v0.2.0', '--directory', str(self.assets), '--notes', str(self.notes)], env=env, text=True, capture_output=True)
        log = self.root / 'calls.jsonl'
        return result, [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def test_draft_is_published_only_after_download_verification(self):
        result, calls = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        downloaded = next(i for i, call in enumerate(calls) if call[:2] == ['release', 'download'])
        published = next(i for i, call in enumerate(calls) if '--draft=false' in call)
        self.assertLess(downloaded, published)

    def test_corrupt_remote_assets_keep_the_release_in_draft(self):
        result, calls = self.invoke(corrupt=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any('--draft=false' in call for call in calls))

    def test_incomplete_release_never_calls_github(self):
        (self.assets / 'install.ps1').unlink()
        result, calls = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_already_published_release_is_verified_without_overwriting_assets(self):
        result, calls = self.invoke(state='published')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(call[:2] == ['release', 'upload'] for call in calls))
        self.assertFalse(any('--draft=false' in call for call in calls))


if __name__ == '__main__':
    unittest.main()

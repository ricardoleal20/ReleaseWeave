#!/usr/bin/env python3
"""Install a native archive through a local HTTP mirror and run its shipped examples."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import dist


def run(*args):
    return subprocess.run([str(a) for a in args], check=True, text=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    dist.version_from_tag(args.tag)
    with tempfile.TemporaryDirectory(prefix='releaseweave-install-') as tmp:
        root = Path(tmp)
        served = root / 'server'
        served.mkdir()
        shutil.copyfile(args.archive, served / args.archive.name)
        dist.checksums(served)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(served))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        prefix = root / 'installation with spaces'
        url = 'http://127.0.0.1:' + str(server.server_address[1])
        try:
            if sys.platform == 'win32':
                run('pwsh', '-NoProfile', '-File', dist.REPO / 'install.ps1', '-Version', args.tag, '-Prefix', prefix, '-BaseUrl', url)
                binary = prefix / 'bin/releaseweave.exe'
            else:
                run('sh', dist.REPO / 'install.sh', '--version', args.tag, '--prefix', prefix, '--base-url', url)
                binary = prefix / 'bin/releaseweave'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        if run(binary, '--version').strip() != 'releaseweave ' + args.tag[1:]:
            raise ValueError('Installed binary reports the wrong version')
        extracted = root / 'extracted'
        shutil.unpack_archive(str(args.archive), str(extracted))
        package = next(extracted.iterdir())
        for scenario in ['single-repo', 'monorepo']:
            example = package / 'examples' / scenario
            run(binary, '--root', example, 'init', '--yes')
            if scenario == 'single-repo':
                run(binary, '--root', example, 'create', '--bump', 'minor', '--message', 'Release installation smoke test')
                expected = {'hello-release': '1.3.0'}
            else:
                run(binary, '--root', example, 'create', '--package', 'acme-api', '--bump', 'minor', '--message', 'API release')
                run(binary, '--root', example, 'create', '--package', '@acme/web', '--bump', 'patch', '--message', 'Web release')
                expected = {'acme-api': '1.5.0', '@acme/web': '2.1.1'}
            plan = json.loads(run(binary, '--root', example, 'bump', '--json'))
            if {r['package']: r['next_version'] for r in plan['releases']} != expected:
                raise ValueError('Unexpected versions in shipped example: ' + scenario)
        print('Native installer, version and both shipped examples passed')


if __name__ == '__main__':
    main()

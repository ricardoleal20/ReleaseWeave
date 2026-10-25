#!/usr/bin/env python3
"""Upload and remotely verify complete assets before publishing a native release."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import dist


def run(*args):
    return subprocess.run([str(arg) for arg in args], check=True, text=True, capture_output=True).stdout


def downloaded_release(tag, expected_checksums=None):
    with tempfile.TemporaryDirectory(prefix='releaseweave-remote-verify-') as tmp:
        directory = Path(tmp)
        run('gh', 'release', 'download', tag, '--dir', directory)
        dist.verify(directory, tag)
        if expected_checksums is not None and (directory / 'SHA256SUMS').read_bytes() != expected_checksums:
            raise ValueError('Uploaded checksums do not match the prepared distribution')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--notes', required=True, type=Path)
    args = parser.parse_args()
    dist.verify(args.directory, args.tag)
    if not args.notes.is_file():
        raise ValueError('Release notes are missing')
    known = {}
    output = run('gh', 'api', '--paginate', 'repos/{owner}/{repo}/releases',
                 '--jq', '.[] | [.tag_name, .draft] | @tsv')
    for line in output.splitlines():
        tag, draft = line.split('\t')
        known[tag] = draft == 'true'
    if args.tag in known and not known[args.tag]:
        downloaded_release(args.tag)
        print('Existing public release verified; assets left unchanged:', args.tag)
        return
    if args.tag not in known:
        run('gh', 'release', 'create', args.tag, '--verify-tag', '--draft', '--title',
            'ReleaseWeave ' + args.tag, '--notes-file', args.notes)
    else:
        run('gh', 'release', 'edit', args.tag, '--title', 'ReleaseWeave ' + args.tag,
            '--notes-file', args.notes)
    assets = sorted(p for p in args.directory.iterdir() if p.is_file())
    run('gh', 'release', 'upload', args.tag, *assets, '--clobber')
    downloaded_release(args.tag, (args.directory / 'SHA256SUMS').read_bytes())
    run('gh', 'release', 'edit', args.tag, '--draft=false', '--prerelease=false', '--latest')
    print('Published complete, checksummed native release:', args.tag)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        raise SystemExit(detail or str(error))

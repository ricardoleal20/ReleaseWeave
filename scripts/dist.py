#!/usr/bin/env python3
"""Build and verify native ReleaseWeave distribution archives (Python standard library)."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[1]
TARGETS = {
    'x86_64-unknown-linux-gnu': 'tar.gz',
    'aarch64-unknown-linux-gnu': 'tar.gz',
    'x86_64-apple-darwin': 'tar.gz',
    'aarch64-apple-darwin': 'tar.gz',
    'x86_64-pc-windows-msvc': 'zip',
}


def version_from_tag(tag):
    if not re.fullmatch(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', tag):
        raise ValueError('Expected a stable version tag such as v0.2.0')
    return tag[1:]


def asset_name(tag, target):
    version_from_tag(tag)
    if target not in TARGETS:
        raise ValueError('Unsupported distribution target: ' + target)
    return 'releaseweave-' + tag + '-' + target + '.' + TARGETS[target]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def package(binary, tag, target, output):
    name = asset_name(tag, target)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('Binary must be a regular file: ' + str(binary))
    output.mkdir(parents=True, exist_ok=True)
    destination = output / name
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / ('releaseweave-' + tag + '-' + target)
        root.mkdir()
        executable = root / ('releaseweave.exe' if target.endswith('windows-msvc') else 'releaseweave')
        shutil.copyfile(binary, executable)
        executable.chmod(0o755)
        shutil.copyfile(REPO / 'LICENCE', root / 'LICENSE')
        (root / 'README.md').write_text('# ReleaseWeave ' + tag + '\n\nNative executable for ' + target + '. No Rust, Python or Node runtime is required.\n\nRun the executable with --help, or install it using docs/INSTALL.md. Start with docs/QUICKSTART.md and copy examples/single-repo or examples/monorepo to a temporary directory before trying local bumps. LICENSE contains the MIT license.\n\nSource and complete documentation: https://github.com/ricardoleal20/ReleaseWeave/tree/' + tag + '\n', encoding='utf-8')
        (root / 'docs').mkdir()
        for document in ['QUICKSTART.md', 'INSTALL.md']:
            shutil.copyfile(REPO / 'docs' / document, root / 'docs' / document)
        shutil.copytree(REPO / 'examples', root / 'examples',
                        ignore=shutil.ignore_patterns('target', 'Cargo.lock', '.releaseweave', '.changesets', '__pycache__'))
        files = sorted(p for p in root.rglob('*') if p.is_file())
        if any(p.is_symlink() for p in root.rglob('*')):
            raise ValueError('Distribution must not contain symbolic links')
        if destination.suffix == '.zip':
            with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, str(path.relative_to(root.parent)))
        else:
            with tarfile.open(destination, 'w:gz') as archive:
                for path in files:
                    archive.add(path, arcname=str(path.relative_to(root.parent)), recursive=False)
    print(destination.resolve())


def checksums(directory):
    files = sorted(p for p in directory.iterdir() if p.is_file() and p.name != 'SHA256SUMS')
    if not files or any(p.is_symlink() for p in files):
        raise ValueError('Checksum input must contain regular distribution files')
    lines = []
    for path in files:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', path.name):
            raise ValueError('Unsafe distribution filename: ' + path.name)
        lines.append(digest(path) + '  ' + path.name)
    (directory / 'SHA256SUMS').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify(directory, tag=None):
    entries = {}
    for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9_.-]+)', line)
        if not match or match[2] in entries:
            raise ValueError('Invalid or duplicate checksum entry')
        entries[match[2]] = match[1]
    if not entries:
        raise ValueError('Empty SHA256SUMS')
    present = {p.name for p in directory.iterdir() if p.is_file() and p.name != 'SHA256SUMS'}
    if present != set(entries):
        raise ValueError('Checksums must cover every distribution file exactly')
    if tag:
        expected = {asset_name(tag, target) for target in TARGETS} | {'install.sh', 'install.ps1', 'QUICKSTART.md'}
        if not expected.issubset(entries):
            raise ValueError('Incomplete native release: missing ' + ', '.join(sorted(expected - set(entries))))
    for name, expected_digest in entries.items():
        path = directory / name
        if path.is_symlink() or digest(path) != expected_digest:
            raise ValueError('Checksum mismatch: ' + name)
    print('Verified ' + str(len(entries)) + ' distribution files')


def project_version():
    package_section = (REPO / 'Cargo.toml').read_text(encoding='utf-8').split('[package]', 1)[1].split('\n[', 1)[0]
    declared = re.search(r'^version\s*=\s*"([^"]+)"', package_section, re.MULTILINE)
    if not declared:
        raise ValueError('Missing Cargo package version')
    return declared[1]


def verify_version(tag):
    version = version_from_tag(tag)
    if project_version() != version:
        raise ValueError('Release tag does not match Cargo.toml version')
    print(version)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    pack = commands.add_parser('package')
    pack.add_argument('--binary', required=True, type=Path)
    pack.add_argument('--tag', required=True)
    pack.add_argument('--target', required=True)
    pack.add_argument('--output', required=True, type=Path)
    sums = commands.add_parser('checksums')
    sums.add_argument('--directory', required=True, type=Path)
    check = commands.add_parser('verify')
    check.add_argument('--directory', required=True, type=Path)
    check.add_argument('--tag')
    ver = commands.add_parser('verify-version')
    ver.add_argument('--tag', required=True)
    args = parser.parse_args()
    if args.command == 'package':
        package(args.binary, args.tag, args.target, args.output)
    elif args.command == 'checksums':
        checksums(args.directory)
    elif args.command == 'verify':
        verify(args.directory, args.tag)
    else:
        verify_version(args.tag)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, IndexError) as error:
        raise SystemExit(str(error))

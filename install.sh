#!/bin/sh
# Install a checksummed native GitHub Release into a user-selected prefix.
set -eu
releaseweave_tag=latest
releaseweave_prefix="${HOME}/.local"
releaseweave_base=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --version) releaseweave_tag="${2:?--version requires a value}"; shift 2 ;;
    --prefix) releaseweave_prefix="${2:?--prefix requires a value}"; shift 2 ;;
    --base-url) releaseweave_base="${2:?--base-url requires a trusted mirror URL}"; shift 2 ;;
    --help) printf '%s\n' 'Usage: sh install.sh [--version v0.2.0] [--prefix ~/.local] [--base-url TRUSTED_MIRROR]'; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done
if [ "$releaseweave_tag" = latest ]; then
  releaseweave_url=$(curl -fLsS -o /dev/null -w '%{url_effective}' https://github.com/ricardoleal20/ReleaseWeave/releases/latest)
  releaseweave_tag=${releaseweave_url##*/}
fi
case "$releaseweave_tag" in v*) ;; *) releaseweave_tag="v$releaseweave_tag" ;; esac
if ! printf '%s\n' "$releaseweave_tag" | grep -Eq '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'; then
  printf 'Invalid release version: %s\n' "$releaseweave_tag" >&2; exit 1
fi
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64) releaseweave_target=x86_64-unknown-linux-gnu ;;
  Linux/aarch64|Linux/arm64) releaseweave_target=aarch64-unknown-linux-gnu ;;
  Darwin/x86_64) releaseweave_target=x86_64-apple-darwin ;;
  Darwin/arm64|Darwin/aarch64) releaseweave_target=aarch64-apple-darwin ;;
  *) printf '%s\n' 'Unsupported OS/architecture. Use the tagged Cargo source installation.' >&2; exit 1 ;;
esac
releaseweave_asset="releaseweave-$releaseweave_tag-$releaseweave_target.tar.gz"
if [ -z "$releaseweave_base" ]; then
  releaseweave_base="https://github.com/ricardoleal20/ReleaseWeave/releases/download/$releaseweave_tag"
fi
releaseweave_tmp=$(mktemp -d)
trap 'rm -rf "$releaseweave_tmp"' EXIT
trap 'exit 1' HUP INT TERM
curl -fLsS -o "$releaseweave_tmp/$releaseweave_asset" "${releaseweave_base%/}/$releaseweave_asset"
curl -fLsS -o "$releaseweave_tmp/SHA256SUMS" "${releaseweave_base%/}/SHA256SUMS"
releaseweave_expected=$(awk -v name="$releaseweave_asset" '$2 == name && NF == 2 { print $1; count++ } END { if (count != 1) exit 1 }' "$releaseweave_tmp/SHA256SUMS")
if ! printf '%s\n' "$releaseweave_expected" | grep -Eq '^[0-9a-f]{64}$'; then
  printf '%s\n' 'Invalid checksum entry.' >&2; exit 1
fi
if command -v sha256sum >/dev/null 2>&1; then
  releaseweave_actual=$(sha256sum "$releaseweave_tmp/$releaseweave_asset" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  releaseweave_actual=$(shasum -a 256 "$releaseweave_tmp/$releaseweave_asset" | awk '{print $1}')
else
  printf '%s\n' 'Install sha256sum or shasum before installing.' >&2; exit 1
fi
if [ "$releaseweave_actual" != "$releaseweave_expected" ]; then
  printf '%s\n' 'Checksum mismatch; nothing installed.' >&2; exit 1
fi
tar -xzf "$releaseweave_tmp/$releaseweave_asset" -C "$releaseweave_tmp"
releaseweave_binary="$releaseweave_tmp/releaseweave-$releaseweave_tag-$releaseweave_target/releaseweave"
if [ ! -f "$releaseweave_binary" ] || [ -L "$releaseweave_binary" ]; then
  printf '%s\n' 'Archive does not contain the expected executable.' >&2; exit 1
fi
releaseweave_reported=$("$releaseweave_binary" --version)
if [ "$releaseweave_reported" != "releaseweave ${releaseweave_tag#v}" ]; then
  printf '%s\n' 'Executable version does not match the requested release.' >&2; exit 1
fi
mkdir -p "$releaseweave_prefix/bin"
install -m 755 "$releaseweave_binary" "$releaseweave_prefix/bin/releaseweave"
printf 'Installed %s to %s/bin/releaseweave\n' "$releaseweave_tag" "$releaseweave_prefix"
printf 'Add this directory to PATH if needed: %s/bin\n' "$releaseweave_prefix"

# Getting started

ReleaseWeave is a Rust CLI for changeset-driven releases in single repositories and monorepos.

## Install v0.2.0

Download the native archive or installer from https://github.com/ricardoleal20/ReleaseWeave/releases/tag/v0.2.0. Linux and macOS can use:

```sh
curl -fLsS -o install-releaseweave.sh https://github.com/ricardoleal20/ReleaseWeave/releases/download/v0.2.0/install.sh
sh install-releaseweave.sh --version v0.2.0
export PATH="$HOME/.local/bin:$PATH"
```

For pinned source installation:

```sh
cargo install --git https://github.com/ricardoleal20/ReleaseWeave.git --tag v0.2.0 --locked --bin releaseweave
```

Native downloads include the CLI, MIT license, quickstart and both complete example projects. Installers verify SHA256 and the executable version before replacing an installation.

## Run the local PoC

```sh
python3 scripts/demo.py
```

The demo runs both examples on disposable copies, verifies dry-run, and leaves updated manifests, changelogs and JSON evidence under .demo/. Python 3.9+ is needed for this runner only.

## First release

```sh
releaseweave init --yes
releaseweave create --bump minor --message "Add a new feature"
releaseweave plan
releaseweave bump --dry-run
releaseweave bump
releaseweave release --dry-run
```

For a monorepo, initialize with --mode monorepo and select each changed package using --package NAME. Only affected packages receive versions, changelogs and proposed GitHub tags.

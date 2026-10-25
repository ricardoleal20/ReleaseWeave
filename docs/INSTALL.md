# Install ReleaseWeave v0.2.0

The first ReleaseWeave release is distributed as native executables on [GitHub Releases](https://github.com/ricardoleal20/ReleaseWeave/releases/tag/v0.2.0). The CLI does not require Python, Node, API keys or GitHub login at runtime.

## Linux and macOS

Download the installer from the versioned release, then run it:

```sh
curl -fLsS -o install-releaseweave.sh https://github.com/ricardoleal20/ReleaseWeave/releases/download/v0.2.0/install.sh
sh install-releaseweave.sh --version v0.2.0
export PATH="$HOME/.local/bin:$PATH"
releaseweave --version
```

The installer detects x64/ARM64 and downloads the matching archive. It verifies the archive against SHA256SUMS, checks the executable version, then installs to ~/.local/bin. It never edits shell startup files or uses sudo. Select a different destination with --prefix PATH; the executable goes under PATH/bin.

## Windows x64

In PowerShell 7, download and inspect the installer, then run it in a session that permits downloaded scripts:

```powershell
Invoke-WebRequest https://github.com/ricardoleal20/ReleaseWeave/releases/download/v0.2.0/install.ps1 -OutFile install-releaseweave.ps1
pwsh -File ./install-releaseweave.ps1 -Version v0.2.0
$env:Path = "$env:LOCALAPPDATA\ReleaseWeave\bin;$env:Path"
releaseweave --version
```

The installer verifies SHA256 and installs to the user's LocalAppData/ReleaseWeave/bin without editing the persistent PATH. Use -Prefix PATH to choose another location. You can also download the Windows ZIP, verify it with Get-FileHash against SHA256SUMS, extract it, and place releaseweave.exe in a directory on PATH; this avoids running a PowerShell installer script.

## Native downloads

| Platform | Asset suffix |
| --- | --- |
| Linux x64 | x86_64-unknown-linux-gnu.tar.gz |
| Linux ARM64 | aarch64-unknown-linux-gnu.tar.gz |
| macOS Intel | x86_64-apple-darwin.tar.gz |
| macOS Apple Silicon | aarch64-apple-darwin.tar.gz |
| Windows x64 | x86_64-pc-windows-msvc.zip |

Every archive name starts with releaseweave-v0.2.0-. Archives contain the executable, LICENSE, README, docs/QUICKSTART.md and both complete example projects. SHA256SUMS covers all five archives, both installers and the standalone quickstart.

Linux binaries are built on Ubuntu 22.04 (glibc 2.35 baseline). macOS binaries are built on macOS 15 runners; source installation is available for other compatible systems. The first native release is not notarized or Authenticode-signed. Other CPU/OS combinations can build from the exact source tag.

## Install from source with Cargo

```sh
cargo install --git https://github.com/ricardoleal20/ReleaseWeave.git --tag v0.2.0 --locked --bin releaseweave
releaseweave --version
```

The primary executable is releaseweave. To retain scripts using the old name, install --bin changeforge from the same tag. ReleaseWeave is distributed through GitHub Releases and tagged source; these commands do not require a crates.io publication.

## Verify an extracted executable

```sh
./releaseweave --version
./releaseweave --help
```

Expected version: releaseweave 0.2.0. On Windows use ./releaseweave.exe. Copy the bundled examples to a temporary directory before trying changes that write manifests. Continue with [the quickstart](QUICKSTART.md) or [the Spanish PoC guide](POC.md).

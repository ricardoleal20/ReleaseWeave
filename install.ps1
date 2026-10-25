param(
    [string]$Version = 'latest',
    [string]$Prefix = (Join-Path $env:LOCALAPPDATA 'ReleaseWeave'),
    [string]$BaseUrl = ''
)
$ErrorActionPreference = 'Stop'
if ($Version -eq 'latest') {
    $Version = (Invoke-RestMethod 'https://api.github.com/repos/ricardoleal20/ReleaseWeave/releases/latest').tag_name
}
if (-not $Version.StartsWith('v')) { $Version = 'v' + $Version }
if ($Version -notmatch '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$') {
    throw 'Expected a stable release version such as v0.2.0'
}
if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() -ne 'X64') {
    throw 'This installer supports Windows x64. Use the tagged Cargo source installation for other architectures.'
}
$target = 'x86_64-pc-windows-msvc'
$asset = "releaseweave-$Version-$target.zip"
if (-not $BaseUrl) {
    $BaseUrl = "https://github.com/ricardoleal20/ReleaseWeave/releases/download/$Version"
}
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('releaseweave-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    $archive = Join-Path $temporary $asset
    $checksumFile = Join-Path $temporary 'SHA256SUMS'
    Invoke-WebRequest -UseBasicParsing ($BaseUrl.TrimEnd('/') + '/' + $asset) -OutFile $archive
    Invoke-WebRequest -UseBasicParsing ($BaseUrl.TrimEnd('/') + '/SHA256SUMS') -OutFile $checksumFile
    $pattern = '^([0-9a-f]{64})  ' + [regex]::Escape($asset) + '$'
    $entries = @(Get-Content $checksumFile | Where-Object { $_ -cmatch $pattern })
    if ($entries.Count -ne 1) { throw 'Expected exactly one checksum entry for the archive' }
    $expected = [regex]::Match($entries[0], $pattern).Groups[1].Value
    $actual = (Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw 'Checksum mismatch; nothing installed' }
    Expand-Archive -LiteralPath $archive -DestinationPath $temporary
    $binary = Join-Path $temporary "releaseweave-$Version-$target/releaseweave.exe"
    if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw 'Missing executable in archive' }
    $reported = & $binary --version
    if ($LASTEXITCODE -ne 0 -or $reported -ne ('releaseweave ' + $Version.Substring(1))) {
        throw 'Executable version does not match the requested release'
    }
    $binDirectory = Join-Path $Prefix 'bin'
    New-Item -ItemType Directory -Force -Path $binDirectory | Out-Null
    Copy-Item -LiteralPath $binary -Destination (Join-Path $binDirectory 'releaseweave.exe') -Force
    Write-Output "Installed $Version to $binDirectory"
    Write-Output "Add this directory to your user PATH: $binDirectory"
} finally {
    Remove-Item -LiteralPath $temporary -Recurse -Force
}

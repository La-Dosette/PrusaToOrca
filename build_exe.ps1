# Build PrusaToOrca for Windows.
#
# Produces release\PrusaToOrca-v<version>-windows.zip together with a
# SHA256SUMS.txt file. The version comes from version.py so the exe metadata,
# the archive name and the git tag can never drift apart.

$ErrorActionPreference = "Stop"

$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$root = $PSScriptRoot

# Single source of truth for the version.
$version = & $python -c "import sys; sys.path.insert(0, r'$root'); from version import __version__; print(__version__)"
if (-not $version) { throw "Could not read __version__ from version.py" }
Write-Host "Building PrusaToOrca $version"

# Embed publisher/product/version into the PE resource table.
& $python (Join-Path $root "tools\make_version_info.py")

# The .spec is the build recipe; do not pass packaging flags here or the two
# will disagree.
& $python -m PyInstaller --noconfirm --clean (Join-Path $root "PrusaToOrca.spec")

$appDir = Join-Path $root "dist\PrusaToOrca"
if (-not (Test-Path (Join-Path $appDir "PrusaToOrca.exe"))) {
  throw "Build did not produce dist\PrusaToOrca\PrusaToOrca.exe"
}

$releaseDir = Join-Path $root "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null

foreach ($doc in @("CHANGELOG.md", "LICENSE", "PRIVACY.md", "README.md", "SECURITY.md")) {
  $src = Join-Path $root $doc
  if (Test-Path $src) { Copy-Item -Force $src (Join-Path $appDir $doc) }
}

$zipName = "PrusaToOrca-v$version-windows.zip"
$zipPath = Join-Path $releaseDir $zipName
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path $appDir -DestinationPath $zipPath -CompressionLevel Optimal

# Publish checksums alongside the archive so downloads can be verified.
$sumsPath = Join-Path $releaseDir "SHA256SUMS.txt"
$hash = (Get-FileHash -Algorithm SHA256 $zipPath).Hash.ToLower()
"$hash  $zipName" | Out-File -FilePath $sumsPath -Encoding utf8

Write-Host ""
Write-Host "Built  : $zipPath"
Write-Host "SHA256 : $hash"

# Rebuild PyInstaller's bootloader from source and install it.
#
# PyInstaller ships a prebuilt bootloader. Because thousands of real malware
# samples are also built with PyInstaller, that exact binary sits in antivirus
# signature and ML training sets, and every application built with it inherits
# the detection. Windows Defender flagged our v1.1.1 release as
# Program:Win32/Wacapew.A!ml for exactly this reason.
#
# Compiling the bootloader locally produces a binary those models have never
# seen, which removes the false positive. Verified A/B against Defender on the
# same signature version: prebuilt bootloader flagged, self-compiled clean.
#
# Requires a C compiler. GitHub's windows runners ship Visual Studio, so this
# runs unattended in CI.

$ErrorActionPreference = "Stop"

$python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$version = & $python -c "import PyInstaller; print(PyInstaller.__version__)"
if (-not $version) { throw "PyInstaller must be installed before rebuilding its bootloader" }
Write-Host "Rebuilding the bootloader for PyInstaller $version"

# Keep the working directory short: the sdist contains test fixtures with paths
# long enough to break extraction under MAX_PATH.
$work = Join-Path $env:TEMP "pyi-bootloader"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force -Path $work | Out-Null

& $python -m pip download "pyinstaller==$version" --no-binary :all: --no-deps -d $work --quiet
$sdist = Get-ChildItem -Path $work -Filter "pyinstaller-*.tar.gz" | Select-Object -First 1
if (-not $sdist) { throw "Could not download the PyInstaller $version source distribution" }

tar -xzf $sdist.FullName -C $work
$src = Join-Path $work "pyinstaller-$version"

Push-Location (Join-Path $src "bootloader")
try {
    & $python ./waf all
    if ($LASTEXITCODE -ne 0) { throw "waf failed to build the bootloader" }
} finally {
    Pop-Location
}

# Overwrite the prebuilt binaries in the installed package.
$built = Join-Path $src "PyInstaller\bootloader\Windows-64bit-intel"
$installed = & $python -c "import os, PyInstaller; print(os.path.join(os.path.dirname(PyInstaller.__file__), 'bootloader', 'Windows-64bit-intel'))"
if (-not (Test-Path $built)) { throw "waf reported success but produced no binaries in $built" }

Copy-Item -Force (Join-Path $built "*.exe") $installed

$hash = (Get-FileHash -Algorithm SHA256 (Join-Path $installed "runw.exe")).Hash.ToLower()
Write-Host "Installed self-compiled bootloader into $installed"
Write-Host "runw.exe SHA256: $hash"

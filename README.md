# PrusaToOrca

<p align="center">
  <img width="96" height="96" alt="PrusaToOrca logo" src="https://github.com/user-attachments/assets/f4105d2d-c46b-4e49-8309-bb7b00396e9c" />
</p>

<p align="center">
  <strong>Convert PrusaSlicer profiles into OrcaSlicer bundles.</strong><br>
  Export an <code>.ini</code> bundle, convert it, review the result, then import the generated <code>.orca_printer</code> file.
</p>

<p align="center">
  <a href="https://la-dosette.github.io/PrusaToOrca/">Use it in your browser</a>
  &nbsp;|&nbsp;
  <a href="https://github.com/La-Dosette/PrusaToOrca/releases/latest">Download the Windows app</a>
  &nbsp;|&nbsp;
  <a href="SECURITY.md">Security</a>
  &nbsp;|&nbsp;
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## Why this exists

Moving a printer setup from PrusaSlicer to OrcaSlicer involves more than copying
a few values. Printer, filament and process profiles refer to one another, and
some settings do not have a direct equivalent in the other slicer.

PrusaToOrca reads an exported PrusaSlicer bundle and writes a new OrcaSlicer
bundle. It never edits existing OrcaSlicer presets directly. The conversion
report shows which settings were copied exactly, approximated or left unmapped
so that the result can be checked before import.

## Choose a version

### Browser

Open <https://la-dosette.github.io/PrusaToOrca/>, drop in an `.ini` file and
download the converted bundle. The file is processed locally in the tab; there
is no upload or server-side conversion.

The page runs this repository's own [`convert.py`](convert.py) through Pyodide.
It is the same conversion engine used by the desktop application, and parity is
checked in CI by [`tests/test_web_parity.py`](tests/test_web_parity.py).

### Windows

Download `PrusaToOrca-v1.1.2-windows.zip` from the
[latest release](https://github.com/La-Dosette/PrusaToOrca/releases/latest), unzip it anywhere and run
`PrusaToOrca.exe`. No installer or Python setup is required.

The desktop application adds:

- folder and batch conversion;
- preview before writing a bundle;
- strict and loose compatibility modes;
- custom mappings for unsupported keys;
- name prefixes and collision warnings;
- detailed reports and CSV, HTML and PDF exports;
- guided import, automatic backups and conversion history;
- local, anonymized bug-report exports;
- light and dark themes;
- French, English, German, Spanish, Italian, Portuguese, Dutch and Polish.

## Recommended workflow

1. Back up your OrcaSlicer profiles.
2. In PrusaSlicer, export a config bundle as an `.ini` file.
3. Convert the file in the browser or desktop app.
4. Review the report. In the desktop app, check the preview before generating.
5. Generate or download the `.orca_printer` bundle.
6. In OrcaSlicer, open **File > Import > Import Config Bundle**.
7. Select the generated bundle and review the imported presets.

Some PrusaSlicer settings have no OrcaSlicer equivalent. PrusaToOrca reports
these as approximate or ignored instead of silently guessing.

## Security and privacy

The source is public under AGPL-3.0. Windows releases are built by GitHub
Actions, not on a maintainer's computer, and include a SHA-256 checksum and a
signed build provenance attestation.

Release v1.0.0 used PyInstaller's one-file mode. That executable unpacked a
compressed payload into `%TEMP%` and started a second binary, which triggered
six generic machine-learning detections on VirusTotal. No engine named a
malware family and no signature-based engine flagged it. Starting with v1.1.0,
the Windows app ships as a normal folder in a ZIP, without UPX, and includes
proper version metadata.

Read [SECURITY.md](SECURITY.md) for the full analysis and [PRIVACY.md](PRIVACY.md)
for the exact files and network requests used by each version.

### Verify a Windows download

Check the archive against `SHA256SUMS.txt` from the release:

```powershell
Get-FileHash -Algorithm SHA256 .\PrusaToOrca-v1.1.2-windows.zip
```

Verify that GitHub Actions built it from this repository:

```bash
gh attestation verify PrusaToOrca-v1.1.2-windows.zip --repo La-Dosette/PrusaToOrca
```

## Run from source

Requirements:

- Python 3.10 or newer;
- the packages in `requirements.txt`.

```bash
python -m pip install -r requirements.txt
python app.py
```

`tkinterdnd2` provides drag and drop. The file picker still works if it is not
available.

## Command line

The conversion engine can be used without the desktop interface:

```bash
python convert.py profiles.ini
python convert.py profiles.ini --output ./output/
python convert.py profiles.ini --dry-run
python convert.py profiles.ini --compatibility strict
python convert.py profiles.ini --compatibility loose
python convert.py profiles.ini --no-prefix
```

The defaults are deliberately conservative: strict compatibility is enabled,
and generated preset names receive a `PrusaToOrca -` prefix. Disable the prefix
only if you have checked that the imported names cannot collide with existing
OrcaSlicer presets.

## Build the Windows package

On Windows:

```powershell
$env:PYTHON="C:\Path\To\python.exe"
.\build_exe.ps1
```

The script generates the version resource, runs PyInstaller with
[`PrusaToOrca.spec`](PrusaToOrca.spec), creates the ZIP in `release/` and writes
`SHA256SUMS.txt`.

Do not enable PyInstaller one-file mode or UPX, and do not turn off `noarchive`.
All three put an appended archive back into the executable, which is the
packaging behaviour that caused the antivirus false positives.

Published builds also compile PyInstaller's bootloader from source first:

```powershell
.\tools\build_bootloader.ps1
```

This needs a C compiler and is run automatically by the release workflow. The
prebuilt bootloader that PyInstaller ships is shared by every PyInstaller
application, malware included, so it sits in antivirus signature sets and the
detection is inherited. Compiling it locally is what cleared the last Windows
Defender false positive. A build made without this step still works; it is just
more likely to be flagged.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers filename sanitizing, strict and loose compatibility,
multi-printer bundles, dry runs, UTF-8 BOM parsing, custom mappings, safe import
behaviour and browser/desktop parity.

## Project layout

```text
app.py                    Desktop interface
convert.py                Conversion engine and command-line entry point
web/                      Browser interface
tests/                    Unit and parity tests
tools/                    Build helpers
PrusaToOrca.spec          PyInstaller build recipe
build_exe.ps1             Windows packaging script
```

## Contributing

Bug reports, missing mappings and pull requests are welcome. A useful report
includes the affected setting, the expected OrcaSlicer result and, when
possible, a small profile bundle that reproduces the problem. Remove anything
private before attaching files to an issue.

## License

PrusaToOrca is free software under the
[GNU Affero General Public License v3.0](LICENSE).

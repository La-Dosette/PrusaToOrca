# Security

## Why your antivirus may flag PrusaToOrca

PrusaToOrca is a Python application packaged for Windows with PyInstaller and
distributed without a code-signing certificate. That combination is routinely
flagged by machine-learning antivirus engines, and it happened to release
v1.0.0: 6 of 70 engines on VirusTotal returned a detection.

Every one of those detections was generic. `Trojan:Win32/Wacatac.B!ml` (the
`!ml` suffix means "machine learning"), `Static AI - Suspicious PE`,
`BehavesLike.Win64.Dropper`, and two bare `MALICIOUS` verdicts. No engine named
an actual malware family, and no signature-based engine — Kaspersky, ESET,
Bitdefender, Avast, Sophos, Trend Micro, F-Secure — flagged anything.

The technical cause was the packaging. v1.0.0 was built as a PyInstaller
*onefile* executable, which embeds a compressed payload, unpacks it into `%TEMP%`
at launch and executes a second binary from there. That is behaviourally
indistinguishable from a dropper, which is why "dropper" was the reported threat
label.

## What changed

Starting with v1.1.0:

- **No more onefile.** The app ships as a normal folder in a `.zip`. Nothing
  self-extracts and nothing is written to `%TEMP%` at startup.
- **No UPX compression.** Packed sections are a heuristic trigger and bought us
  nothing.
- **Version metadata is embedded** in the executable, so it identifies its
  publisher, product and version to Windows instead of being anonymous.
- **Releases are built by GitHub Actions**, never on a maintainer's machine. See
  [.github/workflows/release.yml](.github/workflows/release.yml).
- **Every release carries a signed build provenance attestation** and a
  SHA-256 checksum.

## Verifying a download

Check the checksum against `SHA256SUMS.txt` in the release:

```powershell
Get-FileHash -Algorithm SHA256 .\PrusaToOrca-v1.1.0-windows.zip
```

Or verify cryptographically that the archive was built by this repository's
release workflow, from this repository's source:

```bash
gh attestation verify PrusaToOrca-v1.1.0-windows.zip --repo La-Dosette/PrusaToOrca
```

The attestation associates the archive with a specific commit and release
workflow. Verify it together with the published checksum before running the
download.

## What the application does on your machine

- **Reads** the PrusaSlicer `.ini` files you explicitly select.
- **Writes** the OrcaSlicer bundle to the output folder you choose, plus its own
  settings and conversion history next to the application.
- **Network access**: one request, and only when you click "Check for updates".
  It reads `api.github.com` to compare the latest release tag with your
  installed version. See `check_for_updates` in `app.py`.

There is no telemetry, no analytics, no automatic update check, no background
network activity, and nothing is uploaded anywhere. The source is AGPL-3.0 and
you can verify all of this yourself.

## Reporting a vulnerability

Open a [security advisory](https://github.com/La-Dosette/PrusaToOrca/security/advisories/new),
or an issue if the problem is not sensitive.

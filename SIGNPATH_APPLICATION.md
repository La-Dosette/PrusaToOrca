# SignPath Foundation application — answer sheet

Form: <https://signpath.org/apply>

The submit button is behind a reCAPTCHA, so this has to be pasted in and sent by
a human. Every field on the form is listed below in order. Fields marked
**[YOU]** need information only you have.

---

## Project

**Project Name*** — `Google search for this name should clearly identify your project`

```text
PrusaToOrca
```

**Repository URL***

```text
https://github.com/La-Dosette/PrusaToOrca
```

**Homepage URL***

```text
https://la-dosette.github.io/PrusaToOrca/
```

**Download URL**

```text
https://github.com/La-Dosette/PrusaToOrca/releases/latest
```

**Privacy Policy URL**

```text
https://github.com/La-Dosette/PrusaToOrca/blob/main/PRIVACY.md
```

**Wikipedia URL (optional)** — leave empty.

---

**Tagline***

```text
Converts PrusaSlicer printer, filament and print profiles into ready-to-import OrcaSlicer bundles, on the desktop or directly in the browser.
```

**Description***

```text
PrusaToOrca migrates 3D printing profiles between two slicers. PrusaSlicer stores printer, filament and print settings as .ini config bundles; OrcaSlicer expects a .orca_printer bundle of JSON presets with different key names, units and enum values. Doing that by hand across a full profile library is hours of error-prone work, and it is the main thing that keeps people from switching or from using both slicers side by side.

The converter maps several hundred settings across the three profile types, reports exactly which settings were converted, which were approximated because OrcaSlicer has no exact equivalent, and which had no equivalent at all, so nothing is silently lost. It is deliberately non-destructive: it never edits existing OrcaSlicer presets, it generates a new bundle you review before importing, and it prefixes generated preset names by default so an import cannot overwrite profiles you already have.

It ships two ways from one codebase. The Windows desktop application (Python, tkinter, packaged with PyInstaller) adds batch conversion, custom key mappings for settings the default map skips, a guided import assistant, automatic backups, conversion history and an eight-language interface. The browser version runs the same convert.py compiled to WebAssembly via Pyodide, entirely client-side, so the conversion output is byte-identical and no file is ever uploaded.

The project collects no data of any kind. It makes exactly one network request, only when the user clicks "Check for updates", to read the latest release tag from the GitHub API.
```

**Reputation*** — **[YOU]**, see the note below

```text
PrusaToOrca is published on Printables, Prusa Research's model and tool
community, where it has <FILL IN: downloads / likes / views> and an active
comment thread:
https://www.printables.com/model/1650340-prusatoorca-prusaslicer-to-orcaslicer-profile-conv

The GitHub repository has been public under AGPL-3.0 since March 2026, with
tagged releases, a published build recipe, CI on every push, and releases built
by GitHub Actions carrying signed build provenance attestations and SHA-256
checksums.

Why we are applying: release v1.0.0 was flagged by 6 of 70 engines on
VirusTotal. Every detection was a generic machine-learning verdict
(Trojan:Win32/Wacatac.B!ml, "Static AI - Suspicious PE",
"BehavesLike.Win64.Dropper") with no named malware family, and no
signature-based engine detected anything. The cause was packaging: the build
used PyInstaller's one-file mode, which unpacks itself into %TEMP% at launch and
executes a second binary, which is behaviourally identical to a dropper.

v1.1.0 fixed the packaging (no one-file, no UPX, embedded PE version resource)
and moved release builds onto GitHub Actions with provenance attestation. The
remaining gap is code signing. For a tool aimed at hobbyist 3D printing users,
an unsigned executable plus a SmartScreen warning is where trust breaks down,
and a public "is this a virus?" thread does real damage to a small open source
project regardless of the technical truth. A certificate would close that gap
permanently.
```

---

**Maintainer Type** — choose:

```text
Individual maintainer(s)
```

**Build System** — choose (the only two options are GitHub Actions and GitLab CI/CD):

```text
GitHub Actions
```

---

## Contact

**First Name*** — **[YOU]**
**Last Name*** — **[YOU]**
**Email*** — **[YOU]**
**Company Name** — leave empty.

---

**Primary Discovery Channel*** — options are: Organic search, AI / LLM tools,
Developer platforms (e.g. GitHub), Community platforms, Social media, Events,
Referral, Direct contact, Other.

The accurate answer is:

```text
AI / LLM tools
```

**Please specify the exact source (optional)**

```text
Recommended by Claude while working through the antivirus false positives on our v1.0.0 release.
```

---

## Consent checkboxes

- [x] **Required** — read and agree to the SignPath Foundation Code of Conduct,
      and understand certificates are issued in SignPath Foundation's name and
      may be revoked if terms are violated.
      Read it first: <https://signpath.org/terms>
- [ ] Optional — receive other communications from SignPath. Your call.
- [x] **Required** — allow SignPath to store and process your personal data.

---

## Before you submit

The **Reputation** field is what decides this application, and it is the one
place where the GitHub numbers are weak: 1 star, 1 fork, and 19 downloads across
the v1.0.0 assets. Your real audience is on Printables, and those numbers are
not visible from here — open your model page, take the actual download, like and
view counts, and put them in. That single edit is worth more than everything
else on this form.

Do not inflate anything. SignPath Foundation reviews applications by hand and
the whole point of the certificate is trust.

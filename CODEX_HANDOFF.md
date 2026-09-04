# Handoff: publish the v1.1.0 update on Printables

Task brief for another agent. Everything needed is in this file — no prior
context required. Delete this file once the task is done.

## What you need to be able to do

Post on Printables **as the account owner** (La-Dosette). That means a browser
session already logged in to printables.com. If you cannot reach a logged-in
Printables session, stop and say so rather than improvising — the maintainer
will paste the text manually. Do not create an account, and do not enter
credentials.

## Background, in one paragraph

PrusaToOrca is an open source PrusaSlicer→OrcaSlicer profile converter published
on Printables. A user posted a VirusTotal screenshot showing 6 of 70 engines
flagging the Windows executable, and asked why there was no link to the source.
The detections were real but were false positives caused by packaging, and the
project has now shipped v1.1.0 which fixes the cause and makes releases
cryptographically verifiable. The Printables listing has not been updated yet.
That is the entire remaining task.

## Facts you may rely on — all verified, do not soften or embellish

- The flagged file hashed to `77f1592c3b8ca99018b8dc0abd438b2625929671bd7c0cc669284fe9ac5aed9a`,
  byte-identical to the official v1.0.0 release asset. Nothing was tampered with.
- All 6 detections were generic ML/heuristic verdicts — `Trojan:Win32/Wacatac.B!ml`,
  `Static AI - Suspicious PE`, `BehavesLike.Win64.Dropper`, and two bare
  `MALICIOUS` results. No engine named a malware family. No signature-based
  engine (Kaspersky, ESET, Bitdefender, Avast, Sophos, Trend Micro, F-Secure)
  flagged anything.
- Cause: PyInstaller one-file packaging. It embeds a compressed payload, unpacks
  it to `%TEMP%` at launch and executes a second binary — behaviourally
  identical to a dropper.
- v1.1.0 fixes: onedir instead of onefile (launcher 15.6 MB → 2.3 MB), UPX
  disabled, PE version resource embedded, releases built by GitHub Actions with
  a signed provenance attestation and SHA-256 checksums.
- Verified on the published v1.1.0 artifact: checksum matches, and
  `gh attestation verify` confirms it was built by `release.yml@refs/tags/v1.1.0`
  from commit `87fb60bac55b9d9a7d6c406daef54c61a09dd849`.

Live links (all confirmed working):
- Repo: <https://github.com/La-Dosette/PrusaToOrca>
- Web version: <https://la-dosette.github.io/PrusaToOrca/>
- Release: <https://github.com/La-Dosette/PrusaToOrca/releases/tag/v1.1.0>
- Security write-up: <https://github.com/La-Dosette/PrusaToOrca/blob/main/SECURITY.md>

Model page: <https://www.printables.com/model/1650340-prusatoorca-prusaslicer-to-orcaslicer-profile-conv>

## Do this

### 1. Add this to the very top of the model description

Keep it above everything else. Its absence is the actual complaint.

```text
Source code: https://github.com/La-Dosette/PrusaToOrca
Try it in your browser, no download: https://la-dosette.github.io/PrusaToOrca/

Open source (AGPL-3.0). Windows builds are produced by GitHub Actions, not on my
machine, and every release ships with a SHA-256 checksum and a signed build
provenance attestation — you can cryptographically verify that the file you
downloaded was built from the published source.
```

### 2. Reply to the comment from user "Knightofthe9"

The comment posted the VirusTotal screenshot and said "You should insert the
direct link to the github." Reply with exactly this:

```text
Good call, and thanks for checking rather than just downloading. You were right
that the link should have been there — it is now, at the top of the description.

The detections were real but they were false positives: all 6 were generic ML
verdicts with no named family, and zero signature-based engines flagged it. The
cause was PyInstaller's one-file packaging, which self-extracts to %TEMP% and
looks exactly like a dropper. I've rebuilt it without that, without UPX, with
proper version metadata, and releases are now built by GitHub Actions with a
signed provenance attestation and SHA-256 checksums, so any download can be
verified against the published source.

There's also a browser version now if you'd rather not download anything at all:
https://la-dosette.github.io/PrusaToOrca/

Appreciate the push.
```

### 3. Post the release update

Title:

```text
v1.1.0 — Browser version, verifiable builds, and a fix for the antivirus false positives
```

Body: use the block under "3. Suggested update body" in
[PRINTABLES_UPDATE_POST.md](PRINTABLES_UPDATE_POST.md) in this repository,
verbatim.

### 4. Update the download instructions

The listing points at a bare `.exe`. v1.1.0 ships as
`PrusaToOrca-v1.1.0-windows.zip` — unzip anywhere, run `PrusaToOrca.exe`.

## Rules

- **Do not rewrite the technical claims.** They are load-bearing and verified.
  Softening "false positive" into "possible false positive", or inflating
  "6 of 70 generic ML detections" into "cleared by antivirus", both make it
  worse. Post them as written.
- **Do not delete or hide the original comment.** Answering it in the open is
  the point.
- **Do not claim VirusTotal now reports 0/70.** Nobody has rescanned v1.1.0. If
  you want a number in the post, rescan first and use the real one.
- Show the maintainer what you are about to post before submitting anything.

## Optional follow-ups, lower priority

- Submit the v1.1.0 zip as a false positive to Microsoft:
  <https://www.microsoft.com/en-us/wdsi/filesubmission> (needs a Microsoft
  account sign-in — hand this back to the maintainer rather than signing in).
- SignPath Foundation free code-signing application: answers are prepared in
  [SIGNPATH_APPLICATION.md](SIGNPATH_APPLICATION.md). The form is behind a
  reCAPTCHA, so a human has to submit it.

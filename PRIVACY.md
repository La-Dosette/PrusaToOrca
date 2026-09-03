# Privacy

PrusaToOrca collects nothing. There is no telemetry, no analytics, no account,
no crash reporting and no usage tracking. Nothing you convert is uploaded
anywhere.

This document describes what the application actually touches. All of it is
verifiable in the source, which is public under the AGPL-3.0.

## The desktop application

**Reads** the PrusaSlicer `.ini` files you explicitly select or drop onto the
window. Nothing else on your disk is read.

**Writes**
- the OrcaSlicer bundle, to the output folder you choose
- `settings.json` and `conversion_history.json`, next to the application, so
  your preferences and past conversions survive a restart
- report and bug-report exports, only when you ask for one

Deleting the application folder removes all of it. Nothing is written to the
registry or to system directories.

**Network access** happens exactly once, and only when you click "Check for
updates": a single request to `api.github.com` to read the tag name of the
latest release, so it can be compared with your installed version. See
`check_for_updates` in `app.py`. No request is made at startup, in the
background, or during a conversion. The application works fully offline.

**Bug reports** are generated locally as a `.zip` on your disk, with file paths
anonymised. Nothing is transmitted; you decide whether to attach it to a GitHub
issue.

## The web version

<https://la-dosette.github.io/PrusaToOrca/>

The conversion runs entirely in your browser. Your `.ini` file is never
uploaded — it is read by the page, converted locally, and the result is handed
back to you as a download. There is no backend and no server-side processing.

The page is served by GitHub Pages, which logs requests as part of serving the
site; that is GitHub's infrastructure, not ours, and is covered by
[GitHub's Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
Loading the page also fetches the Pyodide runtime from the jsDelivr CDN and web
fonts from Google Fonts. No analytics or tracking scripts are loaded.

## Contact

Open an issue at <https://github.com/La-Dosette/PrusaToOrca/issues>.

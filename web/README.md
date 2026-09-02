# PrusaToOrca Web

The browser version. It runs the project's own [`convert.py`](../convert.py)
through [Pyodide](https://pyodide.org/) instead of reimplementing the conversion
in JavaScript.

That choice is deliberate. A second implementation would be free to drift from
the desktop app, and a converter that quietly produces different profiles
depending on where you ran it is worse than having no web version at all. This
way there is one converter, and the web page is a front end for it.

The conversion runs entirely on the visitor's machine. There is no backend, and
no file is ever uploaded.

## What it deliberately leaves out

Full bundle conversion and the conversion report are here. Custom key mappings,
the guided import assistant, automatic profile backups, conversion history,
anonymised bug reports and the multilingual interface are desktop-only.

## Running it locally

`convert.py` is copied into this folder at deploy time, so copy it in by hand
first:

```bash
cp convert.py web/convert.py
python -m http.server 8765 --directory web
```

Then open <http://localhost:8765>.

## Verifying that both versions agree

`tests/test_web_parity.py` converts a fixture with the Python API and checks the
result against the hashes the browser produces, so a divergence fails CI rather
than reaching users.

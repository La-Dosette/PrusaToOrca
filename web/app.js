// PrusaToOrca Web.
//
// This runs the project's own convert.py in the browser via Pyodide rather than
// reimplementing the conversion in JavaScript. A second implementation would be
// free to drift from the desktop app, and a converter that silently produces
// different profiles depending on where you ran it is worse than no web version
// at all.

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

const els = {
  dropzone: document.getElementById("dropzone"),
  file: document.getElementById("file"),
  convert: document.getElementById("convert"),
  status: document.getElementById("status"),
  result: document.getElementById("result"),
  strict: document.getElementById("strict"),
  prefix: document.getElementById("prefix"),
};

let pyodide = null;
let selectedFile = null;

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle("err", isError);
}

// --- Python side -----------------------------------------------------------

// Wraps convert_ini_to_orca and flattens the ConversionLog into something the
// page can render. Returns JSON; the archive itself is read back from the
// emscripten filesystem, which avoids copying it through the JS bridge twice.
const GLUE = `
import json, pathlib
from convert import ConversionLog, convert_ini_to_orca

def prusatoorca_run(strict, prefix):
    log = ConversionLog()
    out = convert_ini_to_orca(
        "/work/input.ini",
        "/work/out",
        log=log,
        compatibility="strict" if strict else "loose",
        prefix_profiles=prefix,
    )
    out = pathlib.Path(out)
    return json.dumps({
        "path": str(out),
        "filename": out.name,
        "totals": {
            "mapped": log.total_mapped,
            "skipped": log.total_skipped,
            "approx": log.total_approx,
        },
        "warnings": list(log.warnings),
        "sections": [
            {
                "name": s.name,
                "type": s.type,
                "mapped": s.n_mapped,
                "skipped": s.n_skipped,
                "approx": s.n_approx,
            }
            for s in log.sections
        ],
    })
`;

async function boot() {
  try {
    const { loadPyodide } = await import(`${PYODIDE_URL}pyodide.mjs`);
    pyodide = await loadPyodide({ indexURL: PYODIDE_URL });

    // Ship the converter itself, straight from the repository.
    const source = await fetch("convert.py").then((r) => {
      if (!r.ok) throw new Error(`convert.py: HTTP ${r.status}`);
      return r.text();
    });
    pyodide.FS.writeFile("/home/pyodide/convert.py", source);
    pyodide.FS.mkdirTree("/work/out");
    await pyodide.runPythonAsync(GLUE);

    setStatus("Converter ready.");
    els.convert.disabled = !selectedFile;
  } catch (err) {
    setStatus(`Could not load the converter: ${err.message}`, true);
  }
}

// --- File selection --------------------------------------------------------

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function selectFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".ini")) {
    setStatus("That is not a .ini file. Export a config bundle from PrusaSlicer first.", true);
    return;
  }
  selectedFile = file;
  els.dropzone.classList.add("has-file");
  els.dropzone.querySelector(".dz-main").textContent = file.name;
  els.dropzone.querySelector(".dz-sub").textContent =
    `${humanSize(file.size)} — click to choose a different file`;
  els.result.hidden = true;
  els.convert.disabled = !pyodide;
  setStatus(pyodide ? "Ready to convert." : "Loading converter…");
}

els.dropzone.addEventListener("click", () => els.file.click());
els.dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    els.file.click();
  }
});
els.file.addEventListener("change", () => selectFile(els.file.files[0]));

for (const evt of ["dragenter", "dragover"]) {
  els.dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    els.dropzone.classList.add("drag");
  });
}
for (const evt of ["dragleave", "drop"]) {
  els.dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    els.dropzone.classList.remove("drag");
  });
}
els.dropzone.addEventListener("drop", (e) => selectFile(e.dataTransfer.files[0]));

// --- Conversion ------------------------------------------------------------

els.convert.addEventListener("click", async () => {
  if (!pyodide || !selectedFile) return;
  els.convert.disabled = true;
  setStatus("Converting…");

  try {
    const bytes = new Uint8Array(await selectedFile.arrayBuffer());
    pyodide.FS.writeFile("/work/input.ini", bytes);

    const run = pyodide.globals.get("prusatoorca_run");
    const report = JSON.parse(run(els.strict.checked, els.prefix.checked));
    run.destroy();

    const archive = pyodide.FS.readFile(report.path);
    render(report, archive);
    setStatus("Done.");
  } catch (err) {
    setStatus(`Conversion failed: ${String(err).split("\n").pop()}`, true);
  } finally {
    els.convert.disabled = false;
  }
});

// --- Report ----------------------------------------------------------------

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function render(report, archive) {
  const url = URL.createObjectURL(
    new Blob([archive], { type: "application/octet-stream" })
  );

  const warnings = report.warnings.length
    ? `<ul class="warnings">${report.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>`
    : "";

  const rows = report.sections
    .map(
      (s) =>
        `<tr><td>${esc(s.name)}</td><td>${esc(s.type)}</td>` +
        `<td>${s.mapped}</td><td>${s.approx}</td><td>${s.skipped}</td></tr>`
    )
    .join("");

  els.result.innerHTML = `
    <h2>${esc(report.filename)}</h2>
    <div class="stats">
      <div class="stat"><b>${report.sections.length}</b><span>Profiles</span></div>
      <div class="stat"><b>${report.totals.mapped}</b><span>Settings mapped</span></div>
      <div class="stat"><b>${report.totals.approx}</b><span>Approximated</span></div>
      <div class="stat"><b>${report.totals.skipped}</b><span>No equivalent</span></div>
    </div>
    ${warnings}
    <p><a class="btn primary" id="dl" href="${url}" download="${esc(report.filename)}">Download .orca_printer</a></p>
    <p class="quiet">In OrcaSlicer: <em>File &rarr; Import &rarr; Import Configs…</em> and pick this file. Back up your profiles first.</p>
    <details class="sections">
      <summary>Per-profile detail</summary>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Profile</th><th>Type</th><th>Mapped</th><th>Approx.</th><th>Skipped</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </details>`;
  els.result.hidden = false;

  // The object URL is only needed until the click lands.
  els.result.querySelector("#dl").addEventListener("click", () => {
    setTimeout(() => URL.revokeObjectURL(url), 30_000);
  });
  els.result.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

boot();

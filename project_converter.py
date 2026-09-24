#!/usr/bin/env python3
"""PrusaToOrca - project converter.

A standalone window for .3mf project files. Drop one in and it reads which
slicer wrote it, converts to the other one, and reports what it could and could
not carry over.

This exists next to the main application rather than inside it because the two
answer different questions. The main app migrates a profile library: you point
it at a config bundle you exported on purpose. This one takes the file you
already have - the .3mf you downloaded from Printables or MakerWorld, with the
designer's settings baked in - and tells you what was in it.

Both run the same conversion engine, so neither can drift from the other.
"""

import threading
import tkinter as tk
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import threemf
import to_orca
import to_prusa
from convert import ConversionLog
from version import __version__

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:                                   # drag and drop is a bonus
    DND_AVAILABLE = False

APP_NAME = "PrusaToOrca - Projets"
REPO_URL = "https://github.com/La-Dosette/PrusaToOrca"

BG = "#14120f"
PANEL = "#1e1b17"
PANEL_TINT = "#24201b"
LINE = "#362f27"
INK = "#f2ede6"
MUTED = "#a2988a"
ACCENT = "#ff7a2f"
OK_GREEN = "#6bcf84"
WARN = "#e0b44a"
ERR = "#ff7b6b"

TITLE_FONT = ("Segoe UI Semibold", 15)
FONT = ("Segoe UI", 10)
BOLD = ("Segoe UI Semibold", 10)
SMALL = ("Segoe UI", 9)
MONO = ("Consolas", 9)


class ProjectConverter:
    def __init__(self, root):
        self.root = root
        self.source = None
        self.flavour = None
        self.settings = None
        self.result_path = None
        self.prefix = tk.BooleanVar(value=True)

        root.title(f"{APP_NAME} {__version__}")
        root.configure(bg=BG)
        root.minsize(680, 620)
        self._centre(720, 700)

        self._build()
        if DND_AVAILABLE:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)

    # ---------- layout ----------

    def _centre(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 3
        self.root.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _build(self):
        header = tk.Frame(self.root, bg=PANEL, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Convertisseur de projets", font=TITLE_FONT,
                 bg=PANEL, fg=INK).pack(side="left", padx=18)
        link = tk.Label(header, text="Code source", font=SMALL, bg=PANEL,
                        fg=MUTED, cursor="hand2")
        link.pack(side="right", padx=18)
        link.bind("<Button-1>", lambda _e: webbrowser.open(REPO_URL))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(body,
                 text="Glissez un fichier .3mf. Le sens de conversion est "
                      "déterminé à partir du fichier.",
                 font=FONT, bg=BG, fg=MUTED, justify="left",
                 wraplength=640).pack(anchor="w", pady=(0, 12))

        self.drop = tk.Frame(body, bg=PANEL, highlightbackground=LINE,
                             highlightthickness=2, height=120, cursor="hand2")
        self.drop.pack(fill="x")
        self.drop.pack_propagate(False)
        self.drop_title = tk.Label(self.drop, text="Déposez un projet .3mf ici",
                                   font=BOLD, bg=PANEL, fg=INK)
        self.drop_title.pack(expand=True)
        self.drop_sub = tk.Label(
            self.drop,
            text="ou cliquez pour choisir un fichier"
                 + ("" if DND_AVAILABLE else "   (glisser-déposer indisponible)"),
            font=SMALL, bg=PANEL, fg=MUTED)
        self.drop_sub.pack(expand=True)
        for widget in (self.drop, self.drop_title, self.drop_sub):
            widget.bind("<Button-1>", lambda _e: self._choose())

        self.direction = tk.Label(body, text="", font=BOLD, bg=BG, fg=ACCENT)
        self.direction.pack(anchor="w", pady=(12, 0))

        options = tk.Frame(body, bg=BG)
        options.pack(fill="x", pady=(10, 0))
        tk.Checkbutton(
            options, variable=self.prefix,
            text="Préfixer les profils générés (évite d'écraser les vôtres)",
            font=SMALL, bg=BG, fg=MUTED, selectcolor=PANEL_TINT,
            activebackground=BG, activeforeground=INK,
            highlightthickness=0, bd=0).pack(anchor="w")

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=(14, 0))
        self.convert_btn = tk.Button(
            actions, text="Convertir", font=BOLD, bg=ACCENT, fg=BG,
            activebackground=ACCENT, activeforeground=BG, bd=0,
            padx=22, pady=9, cursor="hand2", state="disabled",
            command=self._convert)
        self.convert_btn.pack(side="left")
        self.open_btn = tk.Button(
            actions, text="Ouvrir le dossier", font=FONT, bg=PANEL, fg=INK,
            activebackground=PANEL_TINT, activeforeground=INK, bd=0,
            padx=16, pady=9, cursor="hand2", state="disabled",
            command=self._open_folder)
        self.open_btn.pack(side="left", padx=(10, 0))
        self.status = tk.Label(actions, text="", font=SMALL, bg=BG, fg=MUTED)
        self.status.pack(side="left", padx=(14, 0))

        report_frame = tk.Frame(body, bg=PANEL, highlightbackground=LINE,
                                highlightthickness=1)
        report_frame.pack(fill="both", expand=True, pady=(16, 0))
        tk.Label(report_frame, text="Rapport de conversion", font=BOLD,
                 bg=PANEL, fg=INK).pack(anchor="w", padx=12, pady=(10, 4))
        self.report = tk.Text(report_frame, font=MONO, bg=PANEL, fg=MUTED,
                              bd=0, wrap="word", height=12,
                              padx=12, pady=4, state="disabled")
        self.report.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 10))
        self.report.tag_configure("ok", foreground=OK_GREEN)
        self.report.tag_configure("warn", foreground=WARN)
        self.report.tag_configure("err", foreground=ERR)
        self.report.tag_configure("head", foreground=INK)

        tk.Label(self.root,
                 text="Sauvegardez vos profils avant d'importer un bundle converti.",
                 font=SMALL, bg=BG, fg=MUTED).pack(pady=(0, 12))

    # ---------- report helpers ----------

    def _say(self, text="", tag=None):
        self.report.configure(state="normal")
        self.report.insert("end", text + "\n", tag or ())
        self.report.see("end")
        self.report.configure(state="disabled")

    def _clear_report(self):
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.configure(state="disabled")

    # ---------- file selection ----------

    def _on_drop(self, event):
        raw = event.data.strip()
        if raw.startswith("{") and raw.endswith("}"):    # paths with spaces
            raw = raw[1:-1]
        self._load(raw.split("} {")[0])

    def _choose(self):
        path = filedialog.askopenfilename(
            title="Choisir un projet .3mf",
            filetypes=[("Projet 3MF", "*.3mf"), ("Tous les fichiers", "*.*")])
        if path:
            self._load(path)

    def _load(self, path):
        path = Path(path)
        self._clear_report()
        self.result_path = None
        self.open_btn.configure(state="disabled")

        try:
            self.flavour, self.settings = threemf.read_settings(path)
        except threemf.NotAProject as exc:
            self._fail(str(exc))
            return
        except FileNotFoundError as exc:
            self._fail(str(exc))
            return
        except Exception as exc:                         # archive corrompue, JSON invalide
            self._fail(f"Lecture impossible : {exc}")
            return

        self.source = path
        self.drop.configure(highlightbackground=OK_GREEN)
        self.drop_title.configure(text=path.name)
        self.drop_sub.configure(
            text=f"{len(self.settings)} réglages — cliquez pour changer de fichier")

        if self.flavour == threemf.PRUSASLICER:
            self.direction.configure(
                text="PrusaSlicer  →  OrcaSlicer     (.orca_printer)")
        else:
            self.direction.configure(
                text="OrcaSlicer  →  PrusaSlicer     (.ini)")

        self.convert_btn.configure(state="normal")
        self.status.configure(text="Prêt.", fg=MUTED)
        self._say(f"{path.name}", "head")
        self._say(f"Écrit par {'PrusaSlicer' if self.flavour == threemf.PRUSASLICER else 'OrcaSlicer'}, "
                  f"{len(self.settings)} réglages trouvés.")

    def _fail(self, message):
        self.source = None
        self.convert_btn.configure(state="disabled")
        self.drop.configure(highlightbackground=ERR)
        self.direction.configure(text="")
        self.status.configure(text="", fg=MUTED)
        self._say(message, "err")

    # ---------- conversion ----------

    def _convert(self):
        if not self.source:
            return
        to_orca_direction = self.flavour == threemf.PRUSASLICER
        suffix = ".orca_printer" if to_orca_direction else ".ini"
        target = filedialog.asksaveasfilename(
            title="Enregistrer sous",
            defaultextension=suffix,
            initialfile=self.source.stem + suffix,
            filetypes=[("Bundle OrcaSlicer", "*.orca_printer")] if to_orca_direction
            else [("Config PrusaSlicer", "*.ini")])
        if not target:
            return

        self.convert_btn.configure(state="disabled")
        self.status.configure(text="Conversion…", fg=MUTED)
        threading.Thread(target=self._run, args=(target, to_orca_direction),
                         daemon=True).start()

    def _run(self, target, to_orca_direction):
        log = ConversionLog()
        try:
            if to_orca_direction:
                result = to_orca.convert_project_to_orca(
                    self.source, target, log=log,
                    prefix_profiles=self.prefix.get())
            else:
                result = to_prusa.convert_orca_to_ini(
                    self.source, target, log=log)
        except Exception as exc:                         # remonté à l'utilisateur
            detail = traceback.format_exc(limit=2)
            self.root.after(0, self._finish_error, exc, detail)
            return
        self.root.after(0, self._finish_ok, result, log)

    def _finish_ok(self, result, log):
        self.result_path = Path(result)
        self.convert_btn.configure(state="normal")
        self.open_btn.configure(state="normal")
        self.status.configure(text="Terminé.", fg=OK_GREEN)

        self._say("")
        self._say(f"Écrit : {self.result_path.name}", "ok")
        self._say(f"{log.total_mapped} réglages convertis, "
                  f"{log.total_approx} approximés, "
                  f"{log.total_skipped} sans équivalent.")
        for warning in log.warnings:
            self._say(f"! {warning}", "warn")
        self._say("")
        if self.flavour == threemf.PRUSASLICER:
            self._say("Dans OrcaSlicer : Fichier > Importer > Importer des "
                      "configurations, puis choisissez ce fichier.")
        else:
            self._say("Dans PrusaSlicer : Fichier > Importer > Importer une "
                      "configuration, puis choisissez ce fichier.")

    def _finish_error(self, exc, detail):
        self.convert_btn.configure(state="normal")
        self.status.configure(text="Échec.", fg=ERR)
        self._say("")
        self._say(f"Conversion impossible : {exc}", "err")
        self._say(detail)
        messagebox.showerror(APP_NAME, f"Conversion impossible :\n\n{exc}")

    def _open_folder(self):
        if not self.result_path:
            return
        folder = self.result_path.parent
        try:
            import os
            os.startfile(folder)                         # Windows
        except AttributeError:
            webbrowser.open(folder.as_uri())


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    ProjectConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()

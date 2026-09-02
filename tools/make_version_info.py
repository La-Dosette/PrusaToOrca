"""Generate the PyInstaller version resource embedded in the Windows exe.

An executable with no version resource looks anonymous to Windows and to
antivirus heuristics. This fills in publisher, product and version so the
file identifies itself in Explorer's Properties dialog and to SmartScreen.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from version import __version__

COMPANY = "La-Dosette"
PRODUCT = "PrusaToOrca"
DESCRIPTION = "PrusaSlicer to OrcaSlicer profile converter"
COPYRIGHT = "Copyright (C) La-Dosette. Licensed under the AGPL-3.0."

TEMPLATE = """\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{company}'),
          StringStruct('FileDescription', '{description}'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', '{product}'),
          StringStruct('LegalCopyright', '{copyright}'),
          StringStruct('OriginalFilename', '{product}.exe'),
          StringStruct('ProductName', '{product}'),
          StringStruct('ProductVersion', '{version}'),
        ],
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])]),
  ],
)
"""


def main():
    parts = __version__.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise SystemExit(f"version.py must hold a MAJOR.MINOR.PATCH version, got {__version__!r}")
    major, minor, patch = (int(p) for p in parts)

    out = pathlib.Path(__file__).resolve().parent.parent / "version_info.txt"
    out.write_text(
        TEMPLATE.format(
            major=major,
            minor=minor,
            patch=patch,
            version=__version__,
            company=COMPANY,
            product=PRODUCT,
            description=DESCRIPTION,
            copyright=COPYRIGHT,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out} for version {__version__}")


if __name__ == "__main__":
    main()

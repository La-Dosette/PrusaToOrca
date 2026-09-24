#!/usr/bin/env python3
"""PrusaSlicer project (.3mf) -> OrcaSlicer bundle.

convert.py already converts a PrusaSlicer config bundle, which is a file with
named [print:], [filament:] and [printer:] sections. A .3mf carries one
resolved profile instead, with no sections and no names, so the settings arrive
as a single flat dictionary.

Nothing needs re-mapping for that. Each converter reads the keys it knows and
ignores the rest, so running all three over the same flat dictionary sorts the
settings out by itself.

Usage: python to_orca.py project.3mf [-o bundle.orca_printer]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import threemf
from convert import (ConversionLog, convert_filament_profile,
                     convert_print_profile, convert_printer_profile,
                     create_bundle_structure, prefixed_name, safe_zip_name,
                     unique_zip_path)


def convert_settings_to_orca(settings, name, log=None, prefix_profiles=True):
    """Convert one flat profile into the three OrcaSlicer profiles.

    Returns (bundle_structure, {zip_path: profile}).
    """
    printer_name = prefixed_name(name, prefix_profiles)
    used_paths = set()
    converted = {}

    printer_file = unique_zip_path("printer", printer_name, used_paths)
    process_file = unique_zip_path("process", f"{printer_name} - process", used_paths)
    filament_file = unique_zip_path("filament", f"{printer_name} - filament", used_paths)

    def section(kind):
        return log.new_section(name, kind) if log else None

    converted[printer_file] = convert_printer_profile(
        printer_name, settings, section("printer"))
    converted[process_file] = convert_print_profile(
        f"{printer_name} - process", settings, section("process"))
    converted[filament_file] = convert_filament_profile(
        f"{printer_name} - filament", settings, section("filament"))

    # A project has exactly one printer, so the generated filament and process
    # profiles are only offered for it. That is the same conservative default
    # the bundle converter uses.
    for path in (process_file, filament_file):
        converted[path]["compatible_printers"] = [printer_name]
        converted[path]["compatible_printers_condition"] = ""

    bundle = create_bundle_structure(
        printer_name, [filament_file], [process_file], [printer_file])
    return bundle, converted


def convert_project_to_orca(source, output_path=None, name=None, log=None,
                            prefix_profiles=True):
    """Convert a PrusaSlicer .3mf project to an .orca_printer bundle."""
    source = Path(source)
    flavour, settings = threemf.read_settings(source)
    if flavour != threemf.PRUSASLICER:
        raise ValueError(
            f"{source.name} a été écrit par OrcaSlicer. "
            "Utilisez la conversion OrcaSlicer vers PrusaSlicer.")

    name = name or source.stem
    bundle, converted = convert_settings_to_orca(
        settings, name, log=log, prefix_profiles=prefix_profiles)

    safe_name = safe_zip_name(prefixed_name(name, prefix_profiles))
    if output_path is None:
        output_path = source.parent / f"{safe_name}.orca_printer"
    else:
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".orca_printer":
            output_path = output_path / f"{safe_name}.orca_printer"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("bundle_structure.json",
                         json.dumps(bundle, indent=2, ensure_ascii=False))
        for path, profile in converted.items():
            archive.writestr(path, json.dumps(profile, indent=2, ensure_ascii=False))
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert a PrusaSlicer project (.3mf) to an OrcaSlicer bundle")
    parser.add_argument("input")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--no-prefix", action="store_true",
                        help="do not prefix generated profile names")
    args = parser.parse_args()

    log = ConversionLog()
    try:
        result = convert_project_to_orca(
            args.input, args.output, args.name, log,
            prefix_profiles=not args.no_prefix)
    except (threemf.NotAProject, FileNotFoundError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    print(f"OK  {result}")
    print(f"    {log.total_mapped} réglages convertis, "
          f"{log.total_approx} approximés")
    for warning in log.warnings:
        print(f"    ! {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

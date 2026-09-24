#!/usr/bin/env python3
"""OrcaSlicer -> PrusaSlicer conversion.

The mapping is not written out again here. It is derived from convert.py at
import time by running the forward converters against a recording dictionary
that answers every lookup and notes which keys were asked for, then reading the
prusa_key -> orca_key pairs back out of the ConversionLog those converters
already fill in.

Maintaining a second hand-written table would mean the two directions could
drift, and a converter that disagrees with itself depending on which way you
run it is worse than having no reverse direction at all. This way, a mapping
added to convert.py appears here on the next run with no extra work.

Usage: python to_prusa.py project.3mf [-o bundle.ini]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import convert
import threemf
from convert import (ConversionLog, convert_filament_profile,
                     convert_print_profile, convert_printer_profile)

SECTIONS = ("process", "filament", "printer")
INI_PREFIX = {"process": "print", "filament": "filament", "printer": "printer"}


# =================== MAPPING DISCOVERY ===================

class _Recorder(dict):
    """Answers every lookup so the forward converters run to completion.

    The converters skip a field when its source key is missing, so a real
    profile only exercises the mappings it happens to use. Answering everything
    exercises all of them.
    """

    def __init__(self, answer="1"):
        super().__init__()
        self._answer = answer

    def get(self, key, default=None):
        return self._answer

    def items(self):
        return []


def build_key_map():
    """Return {orca_key: (prusa_key, section)} harvested from convert.py."""
    log = ConversionLog()
    for section, converter in (("process", convert_print_profile),
                               ("filament", convert_filament_profile),
                               ("printer", convert_printer_profile)):
        converter("discovery", _Recorder(), log.new_section("discovery", section))

    key_map = {}
    for section_log in log.sections:
        for prusa_key, orca_key, _value, _note, _approx in section_log.mapped:
            # First writer wins: where several PrusaSlicer keys feed one Orca
            # key, the reverse can only restore one of them.
            key_map.setdefault(orca_key, (prusa_key, section_log.type))
    return key_map


def build_ambiguous_keys():
    """Orca keys fed by more than one PrusaSlicer key.

    These cannot be reversed faithfully - the information that distinguished
    the sources is gone - so they are reported rather than guessed at.
    """
    log = ConversionLog()
    for section, converter in (("process", convert_print_profile),
                               ("filament", convert_filament_profile),
                               ("printer", convert_printer_profile)):
        converter("discovery", _Recorder(), log.new_section("discovery", section))

    sources = {}
    for section_log in log.sections:
        for prusa_key, orca_key, _v, _n, _a in section_log.mapped:
            sources.setdefault(orca_key, set()).add(prusa_key)
    return {k: sorted(v) for k, v in sources.items() if len(v) > 1}


def _invert(mapping):
    """Invert a value table, dropping the approximate entries.

    Entries flagged approximate are many-to-one: several PrusaSlicer values
    collapse onto the same Orca value. Keeping the first non-approximate one
    means the reverse picks the value that round-trips.
    """
    exact, approximate = {}, {}
    for prusa_value, result in mapping.items():
        orca_value, is_approx = result if isinstance(result, tuple) else (result, False)
        target = approximate if is_approx else exact
        target.setdefault(orca_value, prusa_value)
    for orca_value, prusa_value in approximate.items():
        exact.setdefault(orca_value, prusa_value)
    return exact


VALUE_MAPS = {
    "sparse_infill_pattern": _invert(convert.FILL_PATTERN_MAP),
    "top_surface_pattern": _invert(convert.SURFACE_PATTERN_MAP),
    "bottom_surface_pattern": _invert(convert.SURFACE_PATTERN_MAP),
    "internal_solid_infill_pattern": _invert(convert.SURFACE_PATTERN_MAP),
    "seam_position": _invert(convert.SEAM_POSITION_MAP),
    "brim_type": _invert(convert.BRIM_TYPE_MAP),
    "gcode_flavor": _invert(convert.GCODE_FLAVOR_MAP),
    "support_style": _invert(convert.SUPPORT_STYLE_MAP),
    "wall_generator": _invert(convert.PERIMETER_GENERATOR_MAP),
    "fuzzy_skin": _invert(convert.FUZZY_SKIN_MAP),
}

# Orca keys whose forward transform is not a plain copy or a value table.
# Each entry returns {prusa_key: value}, because some of them restore more
# than one PrusaSlicer setting.
def _enabled_disabled(prusa_key):
    def restore(value):
        return {prusa_key: "enabled" if str(value) == "1" else "disabled"}
    return restore


def _restore_ironing(value):
    # convert.py folds two PrusaSlicer keys into one Orca key: 'ironing' says
    # whether it runs, 'ironing_type' says how. Both come back out.
    if str(value) == "no ironing":
        return {"ironing": "0"}
    reverse = _invert(convert.IRONING_TYPE_MAP)
    return {"ironing": "1", "ironing_type": reverse.get(str(value), str(value))}


def _restore_vertical_shells(value):
    text = str(value)
    if text == "ensure_all_walls":
        return {"ensure_vertical_shell_thickness": "enabled"}
    if text == "none":
        return {"ensure_vertical_shell_thickness": "disabled"}
    return {"ensure_vertical_shell_thickness": text}


def _restore_print_sequence(value):
    return {"complete_objects": "1" if str(value) == "by object" else "0"}


def _restore_interface_loops(value):
    return {"support_material_interface_contact_loops":
            "0" if str(value) == "default" else "1"}


def _quoted_gcode(prusa_key):
    """Restore a G-code field that PrusaSlicer stores quoted.

    The per-extruder G-code settings are vector-typed on the PrusaSlicer side,
    so it wraps them in double quotes and escapes the newlines. convert.py's
    clean_gcode undoes both; this puts them back.
    """
    def restore(value):
        text = str(value).replace(NEWLINE, ESCAPED_NEWLINE)
        return {prusa_key: '"' + text + '"'}
    return restore


SPECIAL = {
    "enable_arc_fitting": _enabled_disabled("arc_fitting"),
    "label_objects": _enabled_disabled("gcode_label_objects"),
    "ironing_type": _restore_ironing,
    "ensure_vertical_shell_thickness": _restore_vertical_shells,
    "print_sequence": _restore_print_sequence,
    "support_interface_loop_pattern": _restore_interface_loops,
    "filament_start_gcode": _quoted_gcode("start_filament_gcode"),
    "filament_end_gcode": _quoted_gcode("end_filament_gcode"),
}

NEWLINE = chr(10)
ESCAPED_NEWLINE = chr(92) + "n"


def _flatten(value):
    """Turn an Orca value back into the string PrusaSlicer stores.

    Orca uses lists for two unrelated reasons: one entry per extruder, and
    comma-separated values that convert.py split apart. Joining on commas
    restores both, because a single-element list joins to itself.
    """
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


# =================== CONVERSION ===================

def orca_to_prusa(settings, log=None, key_map=None):
    """Convert OrcaSlicer settings into PrusaSlicer sections.

    Returns {section: {prusa_key: value}} for the print, filament and printer
    sections of a config bundle.
    """
    key_map = key_map or build_key_map()
    sections = {name: {} for name in SECTIONS}
    unknown = []

    section_logs = {}
    if log is not None:
        for name in SECTIONS:
            section_logs[name] = log.new_section(name, name)

    for orca_key, raw_value in settings.items():
        entry = key_map.get(orca_key)
        if entry is None:
            unknown.append(orca_key)
            continue
        prusa_key, section = entry
        value = _flatten(raw_value)

        restore = SPECIAL.get(orca_key)
        if restore is not None:
            restored = restore(value)
        else:
            table = VALUE_MAPS.get(orca_key)
            restored = {prusa_key: table.get(value, value) if table else value}

        for key, val in restored.items():
            if NEWLINE in val:
                val = val.replace(NEWLINE, ESCAPED_NEWLINE)
            sections[section][key] = val
            if section in section_logs:
                section_logs[section].log(orca_key, key, val)

    if log is not None:
        ambiguous = build_ambiguous_keys()
        for orca_key in sorted(set(settings) & set(ambiguous)):
            log.warn(
                f"{orca_key} : plusieurs réglages PrusaSlicer "
                f"({', '.join(ambiguous[orca_key])}) donnent ce réglage OrcaSlicer. "
                f"Seul {key_map[orca_key][0]} a pu être restauré."
            )
        if unknown:
            log.warn(
                f"{len(unknown)} réglages OrcaSlicer sans équivalent PrusaSlicer "
                "connu ont été ignorés."
            )
    return sections, unknown


def write_ini_bundle(sections, name, output_path):
    """Write a PrusaSlicer config bundle."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# generated by PrusaToOrca from an OrcaSlicer project", ""]
    for section in SECTIONS:
        lines.append(f"[{INI_PREFIX[section]}:{name}]")
        for key in sorted(sections[section]):
            lines.append(f"{key} = {sections[section][key]}")
        lines.append("")
    lines.append("[presets]")
    for prefix in ("print", "filament", "printer"):
        lines.append(f"{prefix} = {name}")
    output_path.write_text(NEWLINE.join(lines) + NEWLINE, encoding="utf-8")
    return output_path


def convert_orca_to_ini(source, output_path=None, name=None, log=None):
    """Convert an OrcaSlicer project or preset file to a PrusaSlicer bundle."""
    source = Path(source)
    if source.suffix.lower() == ".3mf":
        flavour, settings = threemf.read_settings(source)
        if flavour != threemf.ORCASLICER:
            raise ValueError(
                f"{source.name} a été écrit par PrusaSlicer. "
                "Utilisez la conversion PrusaSlicer vers OrcaSlicer."
            )
    else:
        settings = json.loads(source.read_text(encoding="utf-8"))

    name = name or source.stem
    sections, unknown = orca_to_prusa(settings, log=log)

    if output_path is None:
        output_path = source.parent / f"{convert.safe_zip_name(name)}.ini"
    else:
        output_path = Path(output_path)
        if output_path.suffix.lower() != ".ini":
            output_path = output_path / f"{convert.safe_zip_name(name)}.ini"

    return write_ini_bundle(sections, name, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert an OrcaSlicer project (.3mf) or preset (.json) "
                    "to a PrusaSlicer config bundle (.ini)")
    parser.add_argument("input")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--name", default=None, help="name for the generated presets")
    args = parser.parse_args()

    log = ConversionLog()
    try:
        result = convert_orca_to_ini(args.input, args.output, args.name, log)
    except (threemf.NotAProject, FileNotFoundError, ValueError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1

    print(f"OK  {result}")
    print(f"    {log.total_mapped} réglages convertis")
    for warning in log.warnings:
        print(f"    ! {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

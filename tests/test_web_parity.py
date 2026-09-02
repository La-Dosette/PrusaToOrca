"""Pin the converter's output so the web and desktop versions cannot diverge.

web/ runs this same convert.py through Pyodide, so in principle the two cannot
disagree. What can still happen is that a change to convert.py alters the
generated profiles without anyone noticing, and the deployed web version and an
already-installed desktop build then produce different bundles for the same
input.

The hashes below were verified byte-for-byte against the output of the browser
build. Treat a failure here as "the conversion output changed" - if that was
intentional, update the hashes and say so in the changelog.
"""

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from convert import ConversionLog, convert_ini_to_orca

FIXTURE = Path(__file__).parent / "fixtures" / "sample_safe.ini"

EXPECTED = {
    "filament/PrusaToOrca - Original Prusa_MK4_Input Shaper 0.4 nozzle - Forshape ecoPLA.json":
        "7a43741f968b0b2639ca7d1f3747abf9717407b3bebcc46254566f22fbae411c",
    "printer/PrusaToOrca - Original Prusa_MK4_Input Shaper 0.4 nozzle.json":
        "486cdaeaee51553afec7c4db1609fa6ffb48d9c33319f95f22223384b7f42f6b",
    "process/PrusaToOrca - Original Prusa_MK4_Input Shaper 0.4 nozzle - 0.20mm SPEED @MK4_0.4_test.json":
        "c3f7dadff15d3b3e3426565a1a8f919013f7cd74c5e7ad108c9ad50a4a7c9db1",
}

EXPECTED_TOTALS = {"mapped": 17, "approx": 0, "skipped": 0, "sections": 3}


class WebParityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = ConversionLog()
        self.bundle = convert_ini_to_orca(
            FIXTURE,
            self.tmp.name,
            log=self.log,
            compatibility="strict",
            prefix_profiles=True,
        )

    def test_profile_contents_are_unchanged(self):
        with zipfile.ZipFile(self.bundle) as zf:
            # bundle_structure.json carries a timestamp and a digest over it, so
            # it is not reproducible by construction and is checked separately.
            names = {n for n in zf.namelist() if n != "bundle_structure.json"}
            self.assertEqual(names, set(EXPECTED))
            for name, expected in EXPECTED.items():
                actual = hashlib.sha256(zf.read(name)).hexdigest()
                self.assertEqual(actual, expected, f"conversion output changed for {name}")

    def test_bundle_structure_lists_every_profile(self):
        import json

        with zipfile.ZipFile(self.bundle) as zf:
            bundle = json.loads(zf.read("bundle_structure.json"))
            listed = set(
                bundle["filament_config"] + bundle["printer_config"] + bundle["process_config"]
            )
        self.assertEqual(listed, set(EXPECTED))
        self.assertEqual(bundle["bundle_type"], "printer config bundle")

    def test_report_totals_are_unchanged(self):
        self.assertEqual(
            {
                "mapped": self.log.total_mapped,
                "approx": self.log.total_approx,
                "skipped": self.log.total_skipped,
                "sections": len(self.log.sections),
            },
            EXPECTED_TOTALS,
        )


if __name__ == "__main__":
    unittest.main()

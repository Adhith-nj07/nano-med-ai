"""Guard the referenced simulation demo against unreviewed UI changes."""

import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "tests" / "simulation_ui_baseline.json"


class TestSimulationUiBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8-sig"))

    def test_protected_files_match_versioned_baseline(self):
        for relative_path, expected_digest in self.baseline["protected_files"].items():
            with self.subTest(path=relative_path):
                path = ROOT / relative_path
                actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual_digest, expected_digest)

    def test_locked_html_ids_and_classes_match_baseline(self):
        markup = (ROOT / self.baseline["reference"]).read_text(encoding="utf-8")
        ids = sorted(set(re.findall(r'id="([^"]+)"', markup)))
        classes = sorted({
            name
            for value in re.findall(r'class="([^"]+)"', markup)
            for name in value.split()
        })
        self.assertEqual(ids, self.baseline["protected_ids"])
        self.assertEqual(classes, self.baseline["protected_classes"])


if __name__ == "__main__":
    unittest.main()

import unittest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.predict import (
    predict_stability, 
    predict_cytotoxicity, 
    ValidationError, 
    ModelLoadError,
    _extract_charge,
    _estimate_mw
)

class TestStabilityPredictor(unittest.TestCase):
    def setUp(self):
        self.valid_input = {
            'Shape': 'Spherical',
            'Core': 'Ag',
            'Size_nm': 20.0,
            'Medium': 'PBS pH 7.4',
            'Ligand_SMILES': 'C(C(C(=O)O)O)(C(=O)O)O'
        }
        
    def test_valid_prediction(self):
        result = predict_stability(self.valid_input)
        self.assertIn("prediction", result)
        self.assertEqual(result["unit"], "mV")
        self.assertEqual(result["target"], "zeta_potential")
        self.assertIsInstance(result["prediction"], float)
        
    def test_determinism(self):
        res1 = predict_stability(self.valid_input)["prediction"]
        res2 = predict_stability(self.valid_input)["prediction"]
        self.assertEqual(res1, res2)

    def test_missing_feature(self):
        invalid_input = self.valid_input.copy()
        del invalid_input["Size_nm"]
        with self.assertRaises(ValidationError) as ctx:
            predict_stability(invalid_input)
        self.assertIn("Missing required feature", str(ctx.exception))

    def test_invalid_datatype(self):
        invalid_input = self.valid_input.copy()
        invalid_input["Size_nm"] = "twenty"
        with self.assertRaises(ValidationError) as ctx:
            predict_stability(invalid_input)
        self.assertIn("must be a valid float", str(ctx.exception))
        
    def test_invalid_size(self):
        invalid_input = self.valid_input.copy()
        invalid_input["Size_nm"] = -5.0
        with self.assertRaises(ValidationError) as ctx:
            predict_stability(invalid_input)
        self.assertIn("strictly positive", str(ctx.exception))

    def test_feature_engineering_consistency(self):
        # Charge
        self.assertEqual(_extract_charge("C[N+](C)(C)C"), "Cationic")
        self.assertEqual(_extract_charge("CC(=O)[O-]"), "Anionic")
        self.assertEqual(_extract_charge("[N+]CC[O-]"), "Zwitterionic")
        self.assertEqual(_extract_charge("CCO"), "Neutral")
        
        # MW
        # "CCO" -> 2 Carbon, 1 Oxygen -> 2*12.01 + 16.00 = 40.02
        self.assertAlmostEqual(_estimate_mw("CCO"), 40.02, places=2)

class TestCytotoxicityPredictor(unittest.TestCase):
    def setUp(self):
        self.valid_input = {
            'Material type': 'CuO',
            'Core size (nm)': 20.0,
            'Hydro size (nm)': 30.0,
            'Surface charge (mV)': -15.0,
            'Surface area (m2/g)': 50.0,
            'Assay': 'MTT',
            'Cell name': 'A549',
            'Exposure time': 24.0,
            'Mass dose (ug/mL)': 10.0
        }
        
    def test_valid_prediction(self):
        result = predict_cytotoxicity(self.valid_input)
        self.assertIn("prediction", result)
        self.assertEqual(result["target"], "cytotoxicity")
        self.assertIn(result["prediction"], ["Toxic", "Nontoxic"])
        
    def test_determinism(self):
        res1 = predict_cytotoxicity(self.valid_input)["prediction"]
        res2 = predict_cytotoxicity(self.valid_input)["prediction"]
        self.assertEqual(res1, res2)

    def test_missing_feature(self):
        invalid_input = self.valid_input.copy()
        del invalid_input["Exposure time"]
        with self.assertRaises(ValidationError) as ctx:
            predict_cytotoxicity(invalid_input)
        self.assertIn("Missing required feature", str(ctx.exception))

    def test_invalid_datatype(self):
        invalid_input = self.valid_input.copy()
        invalid_input["Core size (nm)"] = "large"
        with self.assertRaises(ValidationError) as ctx:
            predict_cytotoxicity(invalid_input)
        self.assertIn("must be numeric", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()

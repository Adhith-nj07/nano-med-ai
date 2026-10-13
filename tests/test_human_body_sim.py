import unittest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.server import app
from src.api.human_body_sim import (
    BIOLOGICAL_REGIONS,
    SIMULATION_STAGES,
    HumanBodySimRequest,
    evaluate_human_body_simulation,
    compute_korsmeyer_peppas_trajectory,
    compute_colloidal_stability_index,
)

class TestHumanBodySim(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_regions(self):
        resp = self.client.get("/api/human_body_sim/regions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("regions", data)
        regions = data["regions"]
        expected_regions = [
            "bloodstream", "liver", "kidneys", "lungs", "skin", "target_tissue", "cellular_environment"
        ]
        for r in expected_regions:
            self.assertIn(r, regions)
            self.assertIn("name", regions[r])
            self.assertIn("nanoparticle_interactions", regions[r])
            self.assertIn("barrier_description", regions[r])
            self.assertIn("scientific_classification", regions[r])

    def test_get_stages(self):
        resp = self.client.get("/api/human_body_sim/stages")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("stages", data)
        stages = data["stages"]
        self.assertEqual(len(stages), 8)
        keys = [s["key"] for s in stages]
        self.assertEqual(keys, [
            "administration",
            "circulation",
            "protein_corona",
            "tissue_interaction",
            "cellular_uptake",
            "drug_release",
            "toxicity_response",
            "clearance"
        ])
        for s in stages:
            self.assertIn("badge_text", s)
            self.assertIn("scientific_nature", s)
            self.assertIn("limitations", s)

    def test_evaluate_endpoint_standard_formulation(self):
        payload = {
            "material": "PLGA",
            "core_size_nm": 80.0,
            "hydrodynamic_size_nm": 95.0,
            "surface_charge_mv": -24.0,
            "surface_coating": "PEG",
            "ligand_smiles": "OCCO",
            "drug_name": "Paclitaxel",
            "drug_loading_pct": 12.0,
            "k_release": 0.18,
            "n_release": 0.55,
            "target_tissue": "target_tissue",
            "administration_route": "Intravenous",
            "initial_concentration_ug_ml": 50.0,
            "temperature_c": 37.0,
            "ph": 7.4,
            "ionic_strength_m": 0.154,
            "exposure_time_hours": 48.0,
            "cell_name": "A549",
            "assay": "MTT"
        }
        resp = self.client.post("/api/human_body_sim/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("formulation_summary", res)
        self.assertIn("model_results", res)
        self.assertIn("stages", res)
        self.assertIn("disclaimer", res)

        model_res = res["model_results"]
        self.assertIn("stability", model_res)
        self.assertIn("cytotoxicity", model_res)
        self.assertIn("drug_release_kinetics", model_res)
        self.assertIn("colloidal_index", model_res)
        self.assertIn("illustrative_biodistribution", model_res)

        # Verify drug release trajectory
        kinetics = model_res["drug_release_kinetics"]
        self.assertEqual(kinetics["mechanism"], "Anomalous / Non-Fickian Transport")
        self.assertTrue(len(kinetics["time_series"]) > 0)
        self.assertTrue(kinetics["final_release_pct"] > 0)

        # Verify colloidal index
        colloidal = model_res["colloidal_index"]
        self.assertTrue(colloidal["is_sterically_stabilized"])
        self.assertEqual(colloidal["aggregation_risk"], "Very Low")

    def test_korsmeyer_peppas_kinetics_mechanisms(self):
        # Fickian
        fick = compute_korsmeyer_peppas_trajectory(k=0.15, n=0.40, total_hours=24.0)
        self.assertIn("Fickian", fick["mechanism"])

        # Anomalous
        anom = compute_korsmeyer_peppas_trajectory(k=0.15, n=0.65, total_hours=24.0)
        self.assertIn("Anomalous", anom["mechanism"])

        # Case II
        case2 = compute_korsmeyer_peppas_trajectory(k=0.15, n=0.90, total_hours=24.0)
        self.assertIn("Case II", case2["mechanism"])

    def test_temperature_ph_warning_triggered(self):
        # Altered pH and temp should flag causality warning
        payload = {
            "material": "PLGA",
            "core_size_nm": 60.0,
            "drug_name": "Doxorubicin",
            "temperature_c": 42.0,  # Hyperthermia
            "ph": 5.5,             # Acidic
            "k_release": 0.20,
            "n_release": 0.50,
            "exposure_time_hours": 24.0
        }
        resp = self.client.post("/api/human_body_sim/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        res = resp.json()
        warning_types = [w["type"] for w in res["warnings"]]
        self.assertIn("ENVIRONMENTAL_CAUSALITY_LIMIT", warning_types)

if __name__ == "__main__":
    unittest.main()

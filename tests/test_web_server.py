import unittest
import os
import sys
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.server import app

class TestWebServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("models", data)

    def test_metadata(self):
        resp = self.client.get("/api/metadata")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("stability", data)
        self.assertIn("cytotoxicity", data)
        self.assertIn("simulation", data)
        self.assertEqual(data["stability"]["default_ranges"]["size_nm"][1], 31.464265445104548)
        self.assertIn("Annexiv V/PI staining", data["cytotoxicity"]["assays"])
        self.assertTrue(data["stability"]["presets"])
        self.assertTrue(data["cytotoxicity"]["presets"])

    def test_model_registry(self):
        response = self.client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        models = response.json()["models"]
        self.assertEqual(len(models), 3)
        self.assertEqual(models[0]["supported_ranges"]["Size_nm"][1], 31.464265445104548)
        self.assertEqual(models[2]["validation_method"], "GroupKFold by trajectory_id")

    def test_versioned_feature_registry_is_truthful_and_complete(self):
        response = self.client.get("/api/v1/features")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["registry_version"], "1.0.0")
        features = {feature["id"]: feature for feature in payload["features"]}
        self.assertTrue({
            "nanoparticle-design", "stability-prediction", "drug-loading",
            "drug-release", "particle-transformation", "biological-interaction",
            "cytotoxicity", "molecular-intelligence", "research-assistant",
            "candidate-screening",
        }.issubset(features))
        for feature in features.values():
            with self.subTest(feature=feature["id"]):
                self.assertIn(feature["state"], payload["feature_states"])
                self.assertTrue(feature["input_schema"]["fields"])
                self.assertTrue(feature["output_schema"]["fields"])
                self.assertIn("validation_status", feature)
                self.assertTrue(feature["limitations"])
        self.assertEqual(features["stability-prediction"]["state"], "EXPERIMENTAL")
        self.assertEqual(features["cytotoxicity"]["state"], "EXPERIMENTAL")
        self.assertNotEqual(features["nanoparticle-design"]["state"], "VALIDATED")
        self.assertEqual(features["stability-prediction"]["availability"], "available")

    def test_simulation_capabilities_do_not_claim_unverified_validation(self):
        from src.simulation.capabilities import CapabilityManager

        capabilities = CapabilityManager().to_dict()
        self.assertEqual(capabilities["zeta_prediction"]["validation_state"], "EXPERIMENTAL")
        self.assertEqual(capabilities["cytotoxicity_prediction"]["validation_state"], "EXPERIMENTAL")
        self.assertEqual(capabilities["drug_release"]["validation_state"], "RESEARCH MODULE")

    def test_versioned_dataset_catalog_reports_provenance_and_live_quality(self):
        response = self.client.get("/api/v1/datasets")
        self.assertEqual(response.status_code, 200)
        catalog = response.json()
        self.assertEqual(catalog["catalog_version"], "1.0.0")
        datasets = {dataset["id"]: dataset for dataset in catalog["datasets"]}
        self.assertEqual(set(datasets), {"stability", "cytotoxicity", "drug-release"})
        self.assertEqual(datasets["stability"]["statistics"]["rows"], 288)
        self.assertEqual(datasets["cytotoxicity"]["statistics"]["rows"], 666)
        self.assertEqual(datasets["drug-release"]["statistics"]["rows"], 115)
        for dataset in datasets.values():
            with self.subTest(dataset=dataset["id"]):
                self.assertTrue(dataset["available"])
                self.assertEqual(len(dataset["sha256"]), 64)
                self.assertTrue(dataset["upstream_datasets"])
                self.assertTrue(dataset["limitations"])
                self.assertNotIn("preview", dataset)
        self.assertGreater(datasets["drug-release"]["statistics"]["unknown_measurement_provenance_rows"], 0)

        detail = self.client.get("/api/v1/datasets/drug-release?preview_rows=2")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()["preview"]), 2)
        self.assertEqual(detail.json()["source_identifiers"][0]["type"], "source_doi")
        stability_detail = self.client.get("/api/v1/datasets/stability")
        self.assertEqual(stability_detail.status_code, 200)
        self.assertGreater(len(stability_detail.json()["source_identifiers"]), 1)
        self.assertEqual(self.client.get("/api/v1/datasets/not-a-dataset").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/datasets/stability?preview_rows=11").status_code, 422)

    def test_versioned_model_cards_include_artifact_identity_and_status(self):
        response = self.client.get("/api/v1/models")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["registry_version"], "1.0.0")
        models = {model["target"]: model for model in payload["models"]}
        self.assertEqual(set(models), {"zeta_potential", "toxicity_class", "cumulative_release_pct"})
        self.assertEqual(models["zeta_potential"]["scientific_state"], "EXPERIMENTAL")
        self.assertEqual(models["toxicity_class"]["scientific_state"], "EXPERIMENTAL")
        self.assertEqual(models["cumulative_release_pct"]["scientific_state"], "RESEARCH MODULE")
        self.assertTrue(models["zeta_potential"]["artifact"]["available"])
        self.assertEqual(len(models["zeta_potential"]["artifact"]["sha256"]), 64)

    def test_versioned_health_reports_dependency_status(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["version"], "1.0.0")
        self.assertEqual(
            {key for key, value in payload["checks"].items() if value["status"] == "available"},
            {"stability-prediction", "cytotoxicity", "drug-release"},
        )

    def test_root_serves_combined_workspace(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Environment Explorer", resp.text)
        self.assertIn("Dataset Preview", resp.text)
        self.assertIn("three-viewer", resp.text)

    def test_dataset_previews(self):
        for task in ("stability", "cytotoxicity"):
            with self.subTest(task=task):
                resp = self.client.get(f"/api/dataset/{task}")
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertGreater(data["rows"], 0)
                self.assertTrue(data["head"])
                self.assertTrue(data["numeric_ranges"])

    def test_prompt_runs_models_and_learned_release(self):
        response = self.client.post("/api/prompt", json={
            "prompt": "PLGA nanoparticle, 300 nm core size, 320 nm hydrodynamic size, paclitaxel, 0.08% drug loading, drug MW 853.918, polymer MW 57700, LA:GA ratio 1.85, surface area 50 m2/g, CuO, 50 ug/mL, 24 hours exposure, A549 cell, MTT assay, zeta -20 mV, simulate 30 days"
        })
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["stability"]["status"], "outside_domain")
        self.assertIsNone(result["stability"]["result"])
        self.assertEqual(result["toxicity"]["status"], "ready")
        self.assertIn("prediction", result["toxicity"]["result"])
        self.assertIn(result["toxicity"]["result"]["risk_level"], {"High Risk", "Moderate Risk", "Low Risk"})
        self.assertEqual(result["parsed"]["exposure_hours"], 24.0)
        self.assertEqual(result["parsed"]["duration_hours"], 720.0)
        self.assertEqual(result["parsed"]["hydrodynamic_size_nm"], 320.0)
        self.assertEqual(result["toxicity"]["inputs"]["Core size (nm)"], 300.0)
        self.assertEqual(result["toxicity"]["inputs"]["Hydro size (nm)"], 320.0)
        self.assertEqual(result["toxicity"]["inputs"]["Surface area (m2/g)"], 50.0)
        self.assertEqual(len(result["simulation"]["time_hours"]), 61)
        self.assertEqual(result["simulation"]["status"], "ready")
        self.assertEqual(result["simulation"]["features"]["drug_loading_pct"], 0.08)
        self.assertEqual(result["simulation"]["features"]["drug_mw"], 853.918)
        self.assertEqual(result["simulation"]["features"]["polymer_mw"], 57700.0)
        self.assertEqual(result["simulation"]["features"]["la_ga_ratio"], 1.85)
        self.assertEqual(result["simulation"]["cv"]["validation"], "GroupKFold by trajectory_id")
        self.assertFalse(result["stability"]["drivers"])
        self.assertTrue(result["toxicity"]["cv"]["metrics"])
        self.assertFalse(any("hydrodynamic size defaulted" in item for item in result["assumptions"]))

    def test_prompt_skips_toxicity_when_conditions_are_missing(self):
        response = self.client.post("/api/prompt", json={
            "prompt": "Silver spherical nanoparticle, 20 nm, PEG coating, PBS, pH 7.4"
        })
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["stability"]["status"], "ready")
        self.assertEqual(result["toxicity"]["status"], "not_run")
        self.assertIsNone(result["toxicity"]["result"])
        self.assertIn("dose", result["toxicity"]["missing_inputs"])
        self.assertEqual(result["simulation"]["status"], "not_run")

    def test_prompt_rejects_invalid_physical_values(self):
        for prompt in ("Silver nanoparticle, -5 nm", "Silver nanoparticle, pH 15", "CuO, dose -3 ug/mL"):
            with self.subTest(prompt=prompt):
                response = self.client.post("/api/prompt", json={"prompt": prompt})
                self.assertEqual(response.status_code, 400)

    def test_prompt_rejects_unsupported_medium(self):
        response = self.client.post("/api/prompt", json={
            "prompt": "Silver nanoparticle, 20 nm, biological fluid"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Supported values", response.json()["detail"])

    def test_stability_prediction_rejects_out_of_domain_size(self):
        response = self.client.post("/api/predict/stability", json={
            "Shape": "Sphere",
            "Core": "Silver",
            "Size_nm": 120,
            "Medium": "PBS pH 7.4",
            "Ligand_SMILES": "OCCO",
        })
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["applicability"], "outside_domain")
        self.assertEqual(detail["issues"][0]["field"], "Size_nm")

    def test_cytotoxicity_prediction_rejects_out_of_domain_size(self):
        response = self.client.post("/api/predict/cytotoxicity", json={
            "Material type": "CuO",
            "Core size (nm)": 999,
            "Hydro size (nm)": 140,
            "Surface charge (mV)": -18.5,
            "Surface area (m2/g)": 38,
            "Exposure time": 24,
            "Mass dose (ug/mL)": 80,
            "Assay": "MTT",
            "Cell name": "A549",
        })
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["applicability"], "outside_domain")
        self.assertEqual(detail["issues"][0]["field"], "Core size (nm)")

    def test_stability_prediction(self):
        payload = {
            "Shape": "Sphere",
            "Core": "Silver",
            "Size_nm": 20.0,
            "Medium": "PBS pH 7.4",
            "Ligand_SMILES": "CC(=O)[O-]"
        }
        resp = self.client.post("/api/predict/stability", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("prediction", data)
        self.assertIn("stability_class", data)
        self.assertIn("engineered_features", data)
        self.assertEqual(data["applicability"], "inside_domain")
        self.assertEqual(data["confidence"], "Low")
        self.assertFalse(data["uncertainty"]["calibrated_interval"])
        self.assertEqual(data["engineered_features"]["detected_charge"], "Anionic")

    def test_cytotoxicity_prediction(self):
        payload = {
            "Material type": "CuO",
            "Core size (nm)": 25.0,
            "Hydro size (nm)": 140.0,
            "Surface charge (mV)": -18.5,
            "Surface area (m2/g)": 38.0,
            "Exposure time": 24.0,
            "Mass dose (ug/mL)": 80.0,
            "Assay": "MTT",
            "Cell name": "A549"
        }
        resp = self.client.post("/api/predict/cytotoxicity", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("prediction", data)
        self.assertIn(data["prediction"], ["Toxic", "Nontoxic"])
        self.assertIn("risk_level", data)
        self.assertIsNotNone(data["probability_toxic"])
        self.assertFalse(data["probability_calibrated"])
        self.assertGreater(data["model_vote_confidence"], 0.5)

    def test_simulation_lifecycle(self):
        # 1. Create simulation
        resp = self.client.post("/api/simulation/create", json={
            "nanoparticle": {
                "initial_size_nm": 100.0,
                "zeta_potential_mv": -20.0,
                "drug_loading_percent": 10.0,
                "carrier_material": "PLGA",
                "core_drug": "Paclitaxel"
            },
            "environment": {
                "temperature_c": 37.0,
                "ph": 7.4,
                "ionic_strength_m": 0.15,
                "medium_type": "PBS"
            },
            "models": {
                "korsmeyer_peppas": {"k": 0.20, "n": 0.45}
            }
        })
        self.assertEqual(resp.status_code, 200)
        sim_data = resp.json()
        sim_id = sim_data["simulation_id"]
        self.assertIsNotNone(sim_id)

        # 2. Step simulation
        step_resp = self.client.post(f"/api/simulation/{sim_id}/step")
        self.assertEqual(step_resp.status_code, 200)

        # 3. Get Trajectory
        traj_resp = self.client.get(f"/api/simulation/{sim_id}/trajectory")
        self.assertEqual(traj_resp.status_code, 200)
        traj_data = traj_resp.json()
        self.assertIn("time_hours", traj_data)
        self.assertIn("release_pct", traj_data)
        self.assertIn("remaining_drug_pct", traj_data)

    def test_heatmap_calculation(self):
        resp = self.client.post("/api/formulation/heatmap", json={
            "core": "Gold",
            "size_nm": 30.0,
            "smiles": "OCCO"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("grid", data)
        self.assertIn("ph_values", data)
        self.assertIn("temperature_values", data)

if __name__ == "__main__":
    unittest.main()

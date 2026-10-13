import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from simulation.data_providers import CsvPhysicalStabilityDataProvider
from simulation.models import Trajectory

class TestPhysicalStabilityDataProvider(unittest.TestCase):
    
    def setUp(self):
        self.provider = CsvPhysicalStabilityDataProvider("dummy_path.csv")
        # Inject dummy trajectory for test
        traj = Trajectory(
            trajectory_id="traj_001",
            formulation_id="form_001",
            study_id="study_001",
            observations=[],
            environment=None,
            provenance={"source": "Paper X"}
        )
        self.provider._cache["traj_001"] = traj
        
    def test_get_trajectory(self):
        traj = self.provider.get_trajectory("traj_001")
        self.assertIsNotNone(traj)
        self.assertEqual(traj.trajectory_id, "traj_001")
        
    def test_get_verification_status(self):
        status = self.provider.get_verification_status("traj_001")
        self.assertEqual(status, "DATA_REQUIRED")
        
    def test_get_provenance(self):
        prov = self.provider.get_provenance("traj_001")
        self.assertEqual(prov["source"], "Paper X")

if __name__ == '__main__':
    unittest.main()

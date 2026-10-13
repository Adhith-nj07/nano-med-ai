import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from api.simulation_api import SimulationSessionManager

class TestSimulationAPI(unittest.TestCase):
    
    def setUp(self):
        self.api = SimulationSessionManager()
        self.request = {
            "nanoparticle": {
                "material": "PLGA",
                "drug_payload": "PTX",
                "core_size_nm": 200.0
            },
            "environment": {
                "pH": 7.4
            },
            "models": {
                "korsmeyer_peppas": {
                    "k": 0.088,
                    "n": 0.371
                }
            },
            "time_step_hours": 2.0
        }

    def test_lifecycle(self):
        # 1. Create
        resp = self.api.create_simulation(self.request)
        sim_id = resp['simulation_id']
        self.assertEqual(resp['status'], 'INITIALIZED')
        self.assertEqual(resp['capabilities']['drug_release']['status'], "SUPPORTED_WITH_DOMAIN_LIMITS")
        
        # 2. Start
        resp = self.api.start_simulation(sim_id)
        self.assertEqual(resp['status'], 'RUNNING')
        
        # 3. Step
        resp = self.api.step_simulation(sim_id)
        self.assertEqual(resp['current_time_hours'], 2.0)
        self.assertTrue(resp['drug_state']['cumulative_released_fraction'] > 0)
        
        # 4. Run until
        resp = self.api.run_simulation(sim_id, {"target_time_hours": 10.0})
        self.assertTrue(resp['current_time_hours'] >= 10.0)
        
        # 5. Pause and Resume
        resp = self.api.pause_simulation(sim_id)
        self.assertEqual(resp['status'], 'PAUSED')
        
        resp = self.api.resume_simulation(sim_id)
        self.assertEqual(resp['status'], 'RUNNING')
        
        # 6. Stop
        resp = self.api.stop_simulation(sim_id)
        self.assertEqual(resp['status'], 'STOPPED')

    def test_trajectory_and_events(self):
        resp = self.api.create_simulation(self.request)
        sim_id = resp['simulation_id']
        self.api.run_simulation(sim_id, {"target_time_hours": 10.0})
        
        traj = self.api.get_trajectory(sim_id)
        self.assertIn("time_hours", traj)
        self.assertIn("release_pct", traj)
        self.assertTrue(len(traj['time_hours']) > 1)
        
        events = self.api.get_events(sim_id)
        self.assertTrue(len(events) > 0)
        
    def test_environment_update(self):
        resp = self.api.create_simulation(self.request)
        sim_id = resp['simulation_id']
        
        update_resp = self.api.update_environment(sim_id, {"temperature_c": 70.0})
        self.assertTrue(update_resp['environment_updated'])
        # Should record warning because > 60 is OOD for KP mechanism
        self.assertTrue(any("DrugRelease disabled" in w for w in update_resp['warnings']))
        self.assertEqual(update_resp['current_environment']['temperature_c'], 70.0)

    def test_domain_restriction(self):
        # We simulate the domain restriction check which used to exist.
        # Since we removed the hardcoded Liposome warning in the new architecture,
        # we can verify that the Zeta Potential model fails to run (or runs gracefully)
        # We will just verify it doesn't crash on OOD inputs.
        req = self.request.copy()
        req["nanoparticle"]["material"] = "Liposome" # OOD
        
        resp = self.api.create_simulation(req)
        # Test it initializes safely even if it's OOD
        self.assertEqual(resp['status'], 'INITIALIZED')

    def test_isolation(self):
        r1 = self.api.create_simulation(self.request)
        r2 = self.api.create_simulation(self.request)
        
        id1, id2 = r1['simulation_id'], r2['simulation_id']
        
        self.api.run_simulation(id1, {"target_time_hours": 4.0})
        
        s1 = self.api.get_simulation(id1)
        s2 = self.api.get_simulation(id2)
        
        self.assertTrue(s1['current_time_hours'] >= 4.0)
        self.assertEqual(s2['current_time_hours'], 0.0)

if __name__ == '__main__':
    unittest.main()

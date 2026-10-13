import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from simulation.models import SimulationState, NanoparticleState, EnvironmentState, DrugState, TransformationEvent, EventType
from simulation.mechanisms import KorsmeyerPeppasMechanism

class TestDrugReleaseEngine(unittest.TestCase):
    
    def setUp(self):
        self.state = SimulationState(
            nanoparticle_state=NanoparticleState(),
            environment_state=EnvironmentState(),
            drug_state=DrugState(
                cumulative_released_fraction=0.0,
                remaining_drug_amount=1.0
            )
        )
        self.env_state = self.state.environment_state
        # Set parameters derived from trajectory bannigan_2022_38
        self.kp_model = KorsmeyerPeppasMechanism(k=0.088, n=0.371, max_valid_fraction=0.6)
        
    def test_initial_release_state(self):
        events = self.kp_model.step(0.0, self.state)
        self.assertEqual(len(events), 0)
        self.assertEqual(self.state.drug_state.cumulative_released_fraction, 0.0)
        
    def test_time_advancement(self):
        events = self.kp_model.step(10.0, self.state)
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(self.state.drug_state.cumulative_released_fraction, 0.088 * (10.0 ** 0.371), places=4)
        self.assertEqual(events[0].payload.get("uncertainty"), "within_model_domain")
        
    def test_extrapolation_warning(self):
        # Time 500 should push it past the max_valid_fraction (0.6)
        events = self.kp_model.step(500.0, self.state)
        self.assertEqual(len(events), 1)
        self.assertTrue(self.state.drug_state.cumulative_released_fraction > 0.6)
        self.assertEqual(events[0].payload.get("uncertainty"), "extrapolation")
        
    def test_unsupported_environmental_change(self):
        # Apply once to initialize hash
        self.kp_model.step(1.0, self.state)
        
        # Change pH
        self.state.environment_state.pH = 5.5
        events = self.kp_model.step(2.0, self.state)
        
        # Should record an environment change warning event + the normal release event
        env_events = [e for e in events if e.event_type == EventType.ENVIRONMENT_CHANGED]
        self.assertEqual(len(env_events), 1)
        self.assertEqual(env_events[0].payload.get("trigger"), "unsupported_for_release_model")
        
if __name__ == '__main__':
    unittest.main()

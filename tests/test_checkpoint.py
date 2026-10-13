import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from simulation.models import NanoparticleState, EnvironmentState
from simulation.engine import SimulationEngine
from simulation.checkpoint import CheckpointManager

class TestCheckpointing(unittest.TestCase):
    
    def test_save_and_load(self):
        engine = SimulationEngine(
            np_state=NanoparticleState(core_size_nm=100.0),
            env_state=EnvironmentState(temperature_c=37.0)
        )
        engine.run(5)
        
        # Save
        ckpt = CheckpointManager.save_checkpoint(engine)
        
        # Verify structure
        self.assertEqual(ckpt['current_time'], 5.0)
        self.assertEqual(ckpt['nanoparticle_state']['core_size_nm'], 100.0)
        self.assertEqual(ckpt['environment_state']['temperature_c'], 37.0)
        self.assertTrue(len(ckpt['events']) >= 1)
        
        # Create new blank engine and restore
        new_engine = SimulationEngine()
        CheckpointManager.load_checkpoint(new_engine, ckpt)
        
        # Verify state
        self.assertEqual(new_engine.state.current_time, 5.0)
        self.assertEqual(new_engine.env_manager.env_state.temperature_c, 37.0)
        self.assertEqual(new_engine.state.nanoparticle_state.core_size_nm, 100.0)
        self.assertEqual(len(new_engine.state.events), len(ckpt['events']))

if __name__ == '__main__':
    unittest.main()

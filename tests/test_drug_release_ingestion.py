import unittest
import pandas as pd
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

class TestDrugReleaseIngestion(unittest.TestCase):
    
    def test_schema_and_normalization(self):
        # We will test using the actual generated processed file
        processed_path = 'data/processed/drug_release_longitudinal.csv'
        self.assertTrue(os.path.exists(processed_path), "Processed file must exist")
        
        df = pd.read_csv(processed_path)
        
        # Check canonical columns
        expected_cols = [
            'trajectory_id', 'study_id', 'formulation_id', 'nanoparticle_classification',
            'drug_name', 'polymer', 'particle_size_nm', 'time_hours', 'cumulative_release_pct'
        ]
        for col in expected_cols:
            self.assertIn(col, df.columns)
            
        # Check classification filtering
        # All records should be 'NANOPARTICLE'
        if len(df) > 0:
            self.assertTrue(all(df['nanoparticle_classification'] == 'NANOPARTICLE'))
            
        # Check bounds
        self.assertTrue(all(df['cumulative_release_pct'] >= 0))
        self.assertTrue(all(df['cumulative_release_pct'] <= 110)) # allow slight over 100
        
        self.assertTrue(all(df['time_hours'] >= 0))
        
        # Check duplicate measurements (trajectory + time)
        dup_count = df.duplicated(subset=['trajectory_id', 'time_hours']).sum()
        self.assertEqual(dup_count, 0, "There should be no duplicated time points per trajectory")

if __name__ == '__main__':
    unittest.main()

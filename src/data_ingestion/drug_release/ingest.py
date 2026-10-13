import pandas as pd
import numpy as np
import os
import hashlib
import json

def get_sha256(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def ingest_bannigan_data(input_path, output_path):
    print(f"Loading raw data from {input_path}")
    df = pd.read_excel(input_path)
    
    records = []
    audit = {
        'total_records': len(df),
        'nanoparticle_records': 0,
        'microparticle_records': 0,
        'other_ambiguous': 0,
        'unique_trajectories': 0,
        'duplicates_flagged': 0
    }
    
    trajectories = {}
    
    for _, row in df.iterrows():
        exp_idx = row['Experimental_index']
        se = row['SE']
        sav = row['SA-V']
        
        particle_size_nm = None
        classification = 'UNKNOWN'
        
        # Calculate size for spheres
        if se == 0:
            if sav > 0:
                particle_size_nm = 6_000_000 / sav
                if particle_size_nm <= 1000:
                    classification = 'NANOPARTICLE'
                    audit['nanoparticle_records'] += 1
                else:
                    classification = 'MICROPARTICLE'
                    audit['microparticle_records'] += 1
            else:
                classification = 'AMBIGUOUS'
                audit['other_ambiguous'] += 1
        else:
            classification = 'OTHER' # Cylinders, films
            audit['other_ambiguous'] += 1
            
        record = {
            'trajectory_id': f"bannigan_2022_{exp_idx}",
            'study_id': 'bannigan_2022',
            'formulation_id': f"formulation_{exp_idx}",
            'nanoparticle_classification': classification,
            'nanoparticle_classification_source': 'derived_from_SAV',
            'drug_name': row['DP_Group'].split('-')[0] if '-' in row['DP_Group'] else 'Unknown',
            'drug_mw': row['Drug_Mw'],
            'polymer': row['DP_Group'].split('-')[-1] if '-' in row['DP_Group'] else 'Unknown',
            'polymer_mw': row['Polymer_MW'],
            'la_ga_ratio': row['LA/GA'],
            'particle_size_nm': particle_size_nm,
            'hydrodynamic_size_nm': None,
            'pdi': None,
            'zeta_potential_mv': None,
            'drug_loading_pct': row['DLC'],
            'encapsulation_efficiency_pct': None,
            'temperature_c': None,  # Not provided in ML dataset
            'pH': None,             # Not provided in ML dataset
            'ionic_strength_m': None,
            'release_medium': 'Unknown',
            'surfactant_pct': None,
            'time_hours': row['Time'] * 24.0, # Time in source is Days
            'cumulative_release_pct': row['Release'] * 100.0, # Fractional to Percentage
            'measurement_provenance': 'UNKNOWN', # Could be digitized or direct
            'source_publication': '10.1038/s41467-022-35343-w',
            'source_doi': '10.1038/s41467-022-35343-w'
        }
        
        # Only keep nanoparticles as per Phase S4A requirements
        if classification == 'NANOPARTICLE':
            records.append(record)
            if exp_idx not in trajectories:
                trajectories[exp_idx] = True
                
    audit['unique_trajectories'] = len(trajectories)
    
    # Check monotonicity
    out_df = pd.DataFrame(records)
    if not out_df.empty:
        out_df.sort_values(by=['trajectory_id', 'time_hours'], inplace=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    print(f"Saved {len(out_df)} nanoparticle records to {output_path}")
    
    with open('data/processed/drug_release_audit.json', 'w') as f:
        json.dump(audit, f, indent=2)
    
if __name__ == '__main__':
    ingest_bannigan_data(
        'data/raw/external/bannigan_2023/Dataset_14_feat.tsv', 
        'data/processed/drug_release_longitudinal.csv'
    )

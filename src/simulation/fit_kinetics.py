import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import json

def kp_model(t, k, n):
    return k * (t ** n)

def fit_trajectories(csv_path):
    df = pd.read_csv(csv_path)
    results = {}
    
    for traj_id, group in df.groupby('trajectory_id'):
        # Filter valid points: t > 0 and cumulative release <= 60% (fraction <= 0.6)
        valid_points = group[(group['time_hours'] > 0) & (group['cumulative_release_pct'] <= 60.0)].copy()
        
        if len(valid_points) < 3:
            results[traj_id] = {
                'status': 'insufficient_data',
                'reason': 'too_few_points_in_validity_window'
            }
            continue
            
        t_data = valid_points['time_hours'].values
        y_data = valid_points['cumulative_release_pct'].values / 100.0 # fractional
        
        # Non-linear fit
        try:
            # Initial guess: k=0.1, n=0.5
            popt, pcov = curve_fit(kp_model, t_data, y_data, p0=[0.1, 0.5], bounds=(0, [10.0, 2.0]))
            k_nl, n_nl = popt
            err_nl = np.sqrt(np.diag(pcov))
            
            y_pred = kp_model(t_data, k_nl, n_nl)
            rmse = np.sqrt(np.mean((y_data - y_pred)**2))
            mae = np.mean(np.abs(y_data - y_pred))
            ss_res = np.sum((y_data - y_pred)**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            results[traj_id] = {
                'status': 'fitted',
                'k': k_nl,
                'n': n_nl,
                'k_std': err_nl[0] if np.isfinite(err_nl[0]) else None,
                'n_std': err_nl[1] if np.isfinite(err_nl[1]) else None,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'points_used': len(t_data),
                'max_release_used': np.max(y_data)
            }
        except Exception as e:
            results[traj_id] = {
                'status': 'insufficient_data',
                'reason': f'fitting_failed: {str(e)}'
            }

    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    fit_trajectories('data/processed/drug_release_longitudinal.csv')

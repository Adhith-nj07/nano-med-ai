import pandas as pd
df = pd.read_excel('data/raw/external/bannigan_2023/Dataset_14_feat.tsv')
nano = df[(df['SE'] == 0) & (df['SA-V'] >= 6000)]
for exp_idx, group in nano.groupby('Experimental_index'):
    print(f"Trajectory {exp_idx} ({group.iloc[0]['DP_Group']}) : {len(group)} points, max time: {group['Time'].max()}")

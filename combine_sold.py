# IDX Exchange Data Analyst Internship
# Script: combine_sold.py
# Purpose: Load and concatenate all monthly CRMLSSold CSV files,
#          filter to Residential only, and save as sold_combined_residential.csv
#
# Row counts:
# Before concat: 32 files
# After concat: 613,842
# After Residential filter:412,131

import pandas as pd
import os

folder = '/Users/eeshasaraswat/Downloads/IDX Exchange Internship'

def get_best_sold_files(folder):
    all_files = [f for f in os.listdir(folder) if f.startswith('CRMLSSold') and f.endswith('.csv')]
    months = set()
    for f in all_files:
        name = f.replace('CRMLSSold', '').replace('_filled.csv', '').replace('.csv', '')
        if name.isdigit():
            months.add(name)
    best = []
    for month in sorted(months):
        filled = f"CRMLSSold{month}_filled.csv"
        original = f"CRMLSSold{month}.csv"
        if filled in all_files:
            best.append(filled)
        elif original in all_files:
            best.append(original)
    return best

sold_files = get_best_sold_files(folder)
print(f"Found {len(sold_files)} Sold files")

sold_dfs = []
for f in sold_files:
    df = pd.read_csv(os.path.join(folder, f), low_memory=False)
    sold_dfs.append(df)
sold = pd.concat(sold_dfs, ignore_index=True)
print(f"After concat: {sold.shape[0]:,} rows")

sold_residential = sold[sold['PropertyType'] == 'Residential']
print(f"After Residential filter: {sold_residential.shape[0]:,} rows")

sold_residential.to_csv(os.path.join(folder, 'sold_combined_residential.csv'), index=False)
print("Done! sold_combined_residential.csv saved.")
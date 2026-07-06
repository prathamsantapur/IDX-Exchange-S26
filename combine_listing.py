# IDX Exchange Data Analyst Internship
# Script: combine_listing.py
# Purpose: Load and concatenate all monthly CRMLSListing CSV files,
#          filter to Residential only, and save as listings_combined_residential.csv
#
# Row counts:
# Before concat: 28 files
# After concat: 902,854 rows
# After Residential filter: 574,969 rows

import pandas as pd
import os

folder = '/Users/eeshasaraswat/Downloads/IDX Exchange Internship'

def get_listing_files(folder):
    all_files = [f for f in os.listdir(folder) if f.startswith('CRMLSListing') and f.endswith('.csv')]
    return sorted(all_files)

listing_files = get_listing_files(folder)
print(f"Found {len(listing_files)} Listing files")

listing_dfs = []
for f in listing_files:
    df = pd.read_csv(os.path.join(folder, f), low_memory=False)
    listing_dfs.append(df)
listings = pd.concat(listing_dfs, ignore_index=True)
print(f"After concat: {listings.shape[0]:,} rows")

listings_residential = listings[listings['PropertyType'] == 'Residential']
print(f"After Residential filter: {listings_residential.shape[0]:,} rows")

listings_residential.to_csv(os.path.join(folder, 'listings_combined_residential.csv'), index=False)
print("Done! listings_combined_residential.csv saved.")
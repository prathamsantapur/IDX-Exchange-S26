# Data quality note:
# CRMLSSold202405.csv contains only 470 rows.
# This is materially lower than surrounding sold files, but the source file was manually checked.
# CRMLSSold202405_filled.csv also contains 470 rows, so this appears to be a source data anomaly,
# not a script or concatenation error. The provided regular file is used as-is.

import os
import pandas as pd

csv_folder = "csv"
output_folder = "outputs"

files = os.listdir(csv_folder)

listing_files = sorted(
    file
    for file in files
    if file.startswith("CRMLSListing")
    and file.endswith(".csv")
)

sold_files = sorted(
    file
    for file in files
    if file.startswith("CRMLSSold")
    and file.endswith(".csv")
    and "_filled" not in file
)

print("Loading listing files...")
listing_dataframes = []

for file in listing_files:
    file_path = os.path.join(csv_folder, file)
    monthly_data = pd.read_csv(file_path, low_memory=False)
    listing_dataframes.append(monthly_data)
    print(file, "-", len(monthly_data), "rows")

print("\nLoading sold files...")
sold_dataframes = []

for file in sold_files:
    file_path = os.path.join(csv_folder, file)
    monthly_data = pd.read_csv(file_path, low_memory=False)
    sold_dataframes.append(monthly_data)
    print(file, "-", len(monthly_data), "rows")

print("\nCombining files...")

listings = pd.concat(listing_dataframes, ignore_index=True)
sold = pd.concat(sold_dataframes, ignore_index=True)

print("Combined listings rows:", len(listings))
print("Combined sold rows:", len(sold))

print("\nFiltering to Residential properties...")

listings_before_filter = len(listings)
sold_before_filter = len(sold)

listings = listings[listings["PropertyType"] == "Residential"].copy()
sold = sold[sold["PropertyType"] == "Residential"].copy()

print(
    "Listings:",
    listings_before_filter,
    "before filter,",
    len(listings),
    "after filter"
)

print(
    "Sold:",
    sold_before_filter,
    "before filter,",
    len(sold),
    "after filter"
)

os.makedirs(output_folder, exist_ok=True)

listings_output = os.path.join(
    output_folder,
    "CRMLSListing_Combined_Residential.csv"
)

sold_output = os.path.join(
    output_folder,
    "CRMLSSold_Combined_Residential.csv"
)

listings.to_csv(listings_output, index=False)
sold.to_csv(sold_output, index=False)

print("\nFinished.")
print("Saved:", listings_output)
print("Saved:", sold_output)
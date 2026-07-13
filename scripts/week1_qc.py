import os
import pandas as pd

csv_folder = "csv"
output_folder = "outputs"

listings_output = os.path.join(output_folder, "CRMLSListing_Combined_Residential.csv")
sold_output = os.path.join(output_folder, "CRMLSSold_Combined_Residential.csv")

files = os.listdir(csv_folder)

listing_files = sorted(
    file for file in files
    if file.startswith("CRMLSListing")
    and file.endswith(".csv")
)

sold_files = sorted(
    file for file in files
    if file.startswith("CRMLSSold")
    and file.endswith(".csv")
    and "_filled" not in file
)

print("=== FILE COUNT CHECK ===")
print("Listing monthly files:", len(listing_files))
print("Sold monthly files:", len(sold_files))
print()

print("First listing file:", listing_files[0])
print("Last listing file:", listing_files[-1])
print("First sold file:", sold_files[0])
print("Last sold file:", sold_files[-1])
print()

print("=== OUTPUT FILE EXISTS CHECK ===")
print("Listings output exists:", os.path.exists(listings_output))
print("Sold output exists:", os.path.exists(sold_output))
print()

print("=== MONTHLY INPUT ROW COUNTS ===")

listing_input_rows = 0
for file in listing_files:
    path = os.path.join(csv_folder, file)
    rows = len(pd.read_csv(path, low_memory=False))
    listing_input_rows += rows
    print(file, rows)

print("Total raw listing rows:", listing_input_rows)
print()

sold_input_rows = 0
for file in sold_files:
    path = os.path.join(csv_folder, file)
    rows = len(pd.read_csv(path, low_memory=False))
    sold_input_rows += rows
    print(file, rows)

print("Total raw sold rows:", sold_input_rows)
print()

print("=== LOAD OUTPUT FILES ===")
listings = pd.read_csv(listings_output, low_memory=False)
sold = pd.read_csv(sold_output, low_memory=False)

print("Combined Residential listings rows:", len(listings))
print("Combined Residential sold rows:", len(sold))
print()

print("=== RESIDENTIAL FILTER CHECK ===")
print("Listing PropertyType values:")
print(listings["PropertyType"].value_counts(dropna=False))
print()

print("Sold PropertyType values:")
print(sold["PropertyType"].value_counts(dropna=False))
print()

print("=== COLUMN CHECK ===")
print("Listings columns:", len(listings.columns))
print("Sold columns:", len(sold.columns))
print()

print("Important listing columns present:")
for col in ["PropertyType", "ListingContractDate", "ListPrice", "CountyOrParish", "City", "PostalCode"]:
    print(col, col in listings.columns)

print()

print("Important sold columns present:")
for col in ["PropertyType", "CloseDate", "ClosePrice", "OriginalListPrice", "LivingArea", "DaysOnMarket", "CountyOrParish", "City", "PostalCode"]:
    print(col, col in sold.columns)

print()

print("=== DATE RANGE CHECK ===")
if "ListingContractDate" in listings.columns:
    listing_dates = pd.to_datetime(listings["ListingContractDate"], errors="coerce")
    print("Earliest listing date:", listing_dates.min())
    print("Latest listing date:", listing_dates.max())

if "CloseDate" in sold.columns:
    close_dates = pd.to_datetime(sold["CloseDate"], errors="coerce")
    print("Earliest close date:", close_dates.min())
    print("Latest close date:", close_dates.max())

print()

print("=== BASIC NULL CHECKS ===")
print("Sold key field null counts:")
for col in ["CloseDate", "ClosePrice", "OriginalListPrice", "LivingArea", "DaysOnMarket"]:
    if col in sold.columns:
        print(col, sold[col].isna().sum())

print()

print("Listings key field null counts:")
for col in ["ListingContractDate", "ListPrice"]:
    if col in listings.columns:
        print(col, listings[col].isna().sum())

print()

print("=== BASIC NUMERIC SANITY CHECKS ===")
if "ClosePrice" in sold.columns:
    print("Sold ClosePrice <= 0:", (sold["ClosePrice"] <= 0).sum())

if "LivingArea" in sold.columns:
    print("Sold LivingArea <= 0:", (sold["LivingArea"] <= 0).sum())

if "DaysOnMarket" in sold.columns:
    print("Sold DaysOnMarket < 0:", (sold["DaysOnMarket"] < 0).sum())

if "ListPrice" in listings.columns:
    print("Listings ListPrice <= 0:", (listings["ListPrice"] <= 0).sum())

print()

print("QC complete.")
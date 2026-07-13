import pandas as pd

listings = pd.read_csv(
    "outputs/CRMLSListing_Combined_Residential.csv",
    low_memory=False
)

sold = pd.read_csv(
    "outputs/CRMLSSold_Combined_Residential.csv",
    low_memory=False
)
print("Listings shape:", listings.shape)
print("Sold shape:", sold.shape)

print("\nFirst five listings:")
print(listings.head())

print("\nFirst five sold records:")
print(sold.head())

print("\nMissing values (Listings):")

listing_missing = listings.isnull().sum()

print(listing_missing.sort_values(ascending=False).head(20))

listing_missing_percent = (
    listings.isnull().mean() * 100
).sort_values(ascending=False)

print("\nTop 20 Missing Percentages")
print(listing_missing_percent.head(20))

missing_report = pd.DataFrame({
    "Missing Count": listings.isnull().sum(),
    "Missing Percent": (listings.isnull().mean() * 100)
})

missing_report = missing_report.sort_values(
    by="Missing Percent",
    ascending=False
)

missing_report.to_csv(
    "reports/listing_missing_report.csv",
    index=True
)

dtype_report = pd.DataFrame({
    "Data Type": listings.dtypes.astype(str)
})

dtype_report.index.name = "Column"

dtype_report.to_csv(
    "reports/listing_data_types.csv"
)

print("Saved listing_data_types.csv")

numeric_summary = listings.describe()

numeric_summary.to_csv(
    "reports/listing_numeric_summary.csv"
)

print("Saved listing_numeric_summary.csv")
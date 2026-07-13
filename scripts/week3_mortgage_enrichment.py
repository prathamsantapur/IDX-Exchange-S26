import os
import pandas as pd

outputs_folder = "outputs"
reports_folder = "reports"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

print("Loading combined Residential datasets...")

sold = pd.read_csv(
    "outputs/CRMLSSold_Combined_Residential.csv",
    low_memory=False
)

listings = pd.read_csv(
    "outputs/CRMLSListing_Combined_Residential.csv",
    low_memory=False
)

print("Sold shape before enrichment:", sold.shape)
print("Listings shape before enrichment:", listings.shape)

print("\nFetching mortgage rate data from FRED...")

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

mortgage = pd.read_csv(
    url,
    parse_dates=["observation_date"]
)

mortgage.columns = [
    "date",
    "rate_30yr_fixed"
]

mortgage["rate_30yr_fixed"] = pd.to_numeric(
    mortgage["rate_30yr_fixed"],
    errors="coerce"
)

mortgage = mortgage.dropna(
    subset=["rate_30yr_fixed"]
)

mortgage["year_month"] = mortgage["date"].dt.to_period("M")

mortgage_monthly = (
    mortgage
    .groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .reset_index()
)

mortgage_monthly["year_month"] = mortgage_monthly["year_month"].astype(str)

mortgage_monthly.to_csv(
    "reports/mortgage_rate_monthly.csv",
    index=False
)

print("Saved reports/mortgage_rate_monthly.csv")

print("\nCreating year_month keys...")

sold["CloseDate_dt"] = pd.to_datetime(
    sold["CloseDate"],
    errors="coerce"
)

listings["ListingContractDate_dt"] = pd.to_datetime(
    listings["ListingContractDate"],
    errors="coerce"
)

sold["year_month"] = sold["CloseDate_dt"].dt.to_period("M").astype(str)

listings["year_month"] = (
    listings["ListingContractDate_dt"]
    .dt.to_period("M")
    .astype(str)
)

print("\nMerging mortgage rates...")

sold_with_rates = sold.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)

listings_with_rates = listings.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)

print("Sold shape after enrichment:", sold_with_rates.shape)
print("Listings shape after enrichment:", listings_with_rates.shape)

print("\nValidating mortgage-rate merge...")

sold_missing_rates = sold_with_rates["rate_30yr_fixed"].isna().sum()
listings_missing_rates = listings_with_rates["rate_30yr_fixed"].isna().sum()

validation_report = pd.DataFrame([
    {
        "Dataset": "sold",
        "Rows": len(sold_with_rates),
        "Missing Mortgage Rate Rows": sold_missing_rates,
        "Missing Mortgage Rate Percent": sold_missing_rates / len(sold_with_rates) * 100
    },
    {
        "Dataset": "listings",
        "Rows": len(listings_with_rates),
        "Missing Mortgage Rate Rows": listings_missing_rates,
        "Missing Mortgage Rate Percent": listings_missing_rates / len(listings_with_rates) * 100
    }
])

validation_report.to_csv(
    "reports/mortgage_rate_merge_validation.csv",
    index=False
)

print("Saved reports/mortgage_rate_merge_validation.csv")

sold_with_rates.to_csv(
    "outputs/CRMLSSold_Combined_Residential_Enriched.csv",
    index=False
)

listings_with_rates.to_csv(
    "outputs/CRMLSListing_Combined_Residential_Enriched.csv",
    index=False
)

print("\nSaved enriched datasets:")
print("outputs/CRMLSSold_Combined_Residential_Enriched.csv")
print("outputs/CRMLSListing_Combined_Residential_Enriched.csv")

print("\nMortgage enrichment complete.")
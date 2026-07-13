import os
import pandas as pd

csv_folder = "csv"
reports_folder = "reports"

os.makedirs(reports_folder, exist_ok=True)

sold = pd.read_csv(
    "outputs/CRMLSSold_Combined_Residential.csv",
    low_memory=False
)

listings = pd.read_csv(
    "outputs/CRMLSListing_Combined_Residential.csv",
    low_memory=False
)

# ------------------------------------------------------------
# 1. Residential vs. other property type share
# Use raw monthly files because the combined outputs are already
# filtered to Residential only.
# ------------------------------------------------------------

raw_files = os.listdir(csv_folder)

raw_listing_files = sorted(
    file for file in raw_files
    if file.startswith("CRMLSListing")
    and file.endswith(".csv")
)

raw_sold_files = sorted(
    file for file in raw_files
    if file.startswith("CRMLSSold")
    and file.endswith(".csv")
    and "_filled" not in file
)

property_type_rows = []

for dataset_name, files in [
    ("listings_raw", raw_listing_files),
    ("sold_raw", raw_sold_files)
]:
    for file in files:
        path = os.path.join(csv_folder, file)

        temp = pd.read_csv(
            path,
            usecols=["PropertyType"],
            low_memory=False
        )

        counts = temp["PropertyType"].value_counts(dropna=False)

        for property_type, count in counts.items():
            property_type_rows.append({
                "Dataset": dataset_name,
                "File": file,
                "PropertyType": property_type,
                "Count": count
            })

property_type_report = pd.DataFrame(property_type_rows)

property_type_summary = (
    property_type_report
    .groupby(["Dataset", "PropertyType"], dropna=False)["Count"]
    .sum()
    .reset_index()
)

property_type_summary["Percent"] = (
    property_type_summary["Count"] /
    property_type_summary.groupby("Dataset")["Count"].transform("sum") *
    100
)

property_type_summary.to_csv(
    "reports/property_type_share_raw.csv",
    index=False
)

print("Saved reports/property_type_share_raw.csv")

# ------------------------------------------------------------
# 2. Median and average close prices
# ------------------------------------------------------------

close_price_mean = sold["ClosePrice"].mean()
close_price_median = sold["ClosePrice"].median()

# ------------------------------------------------------------
# 3. Days on Market distribution
# ------------------------------------------------------------

days_on_market_summary = sold["DaysOnMarket"].describe(
    percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
)

days_on_market_summary.to_csv(
    "reports/sold_days_on_market_summary.csv"
)

print("Saved reports/sold_days_on_market_summary.csv")

# ------------------------------------------------------------
# 4. Percent sold above vs. below list price
# Using ListPrice as the current list price.
# ------------------------------------------------------------

sold_price_check = sold[
    sold["ClosePrice"].notna() &
    sold["ListPrice"].notna()
].copy()

above_list_count = (sold_price_check["ClosePrice"] > sold_price_check["ListPrice"]).sum()
at_list_count = (sold_price_check["ClosePrice"] == sold_price_check["ListPrice"]).sum()
below_list_count = (sold_price_check["ClosePrice"] < sold_price_check["ListPrice"]).sum()

total_price_check = len(sold_price_check)

above_list_percent = above_list_count / total_price_check * 100
at_list_percent = at_list_count / total_price_check * 100
below_list_percent = below_list_count / total_price_check * 100

price_position_report = pd.DataFrame([
    {
        "Category": "Sold above list price",
        "Count": above_list_count,
        "Percent": above_list_percent
    },
    {
        "Category": "Sold at list price",
        "Count": at_list_count,
        "Percent": at_list_percent
    },
    {
        "Category": "Sold below list price",
        "Count": below_list_count,
        "Percent": below_list_percent
    }
])

price_position_report.to_csv(
    "reports/sold_above_below_list_price.csv",
    index=False
)

print("Saved reports/sold_above_below_list_price.csv")

# ------------------------------------------------------------
# 5. Date consistency checks
# ListingContractDate should be before PurchaseContractDate,
# and PurchaseContractDate should be before CloseDate.
# ------------------------------------------------------------

date_check = sold.copy()

date_check["ListingContractDate_dt"] = pd.to_datetime(
    date_check["ListingContractDate"],
    errors="coerce"
)

date_check["PurchaseContractDate_dt"] = pd.to_datetime(
    date_check["PurchaseContractDate"],
    errors="coerce"
)

date_check["CloseDate_dt"] = pd.to_datetime(
    date_check["CloseDate"],
    errors="coerce"
)

date_flags = pd.DataFrame([
    {
        "Check": "Missing ListingContractDate",
        "Count": date_check["ListingContractDate_dt"].isna().sum()
    },
    {
        "Check": "Missing PurchaseContractDate",
        "Count": date_check["PurchaseContractDate_dt"].isna().sum()
    },
    {
        "Check": "Missing CloseDate",
        "Count": date_check["CloseDate_dt"].isna().sum()
    },
    {
        "Check": "ListingContractDate after CloseDate",
        "Count": (
            date_check["ListingContractDate_dt"] >
            date_check["CloseDate_dt"]
        ).sum()
    },
    {
        "Check": "PurchaseContractDate after CloseDate",
        "Count": (
            date_check["PurchaseContractDate_dt"] >
            date_check["CloseDate_dt"]
        ).sum()
    },
    {
        "Check": "PurchaseContractDate before ListingContractDate",
        "Count": (
            date_check["PurchaseContractDate_dt"] <
            date_check["ListingContractDate_dt"]
        ).sum()
    }
])

date_flags.to_csv(
    "reports/sold_date_consistency_checks.csv",
    index=False
)

print("Saved reports/sold_date_consistency_checks.csv")

# ------------------------------------------------------------
# 6. Counties with highest median prices
# Use a minimum transaction threshold so tiny counties do not
# dominate the ranking due to very small sample sizes.
# ------------------------------------------------------------

county_price_summary = (
    sold
    .groupby("CountyOrParish")
    .agg(
        MedianClosePrice=("ClosePrice", "median"),
        AverageClosePrice=("ClosePrice", "mean"),
        SalesCount=("ClosePrice", "count")
    )
    .reset_index()
)

county_price_summary_filtered = county_price_summary[
    county_price_summary["SalesCount"] >= 100
].copy()

county_price_summary_filtered = county_price_summary_filtered.sort_values(
    by="MedianClosePrice",
    ascending=False
)

county_price_summary_filtered.to_csv(
    "reports/sold_county_price_summary.csv",
    index=False
)

print("Saved reports/sold_county_price_summary.csv")

# ------------------------------------------------------------
# 7. One-page-ish EDA metrics summary
# ------------------------------------------------------------

eda_summary = pd.DataFrame([
    {
        "Metric": "Average ClosePrice",
        "Value": close_price_mean
    },
    {
        "Metric": "Median ClosePrice",
        "Value": close_price_median
    },
    {
        "Metric": "Homes sold above list price percent",
        "Value": above_list_percent
    },
    {
        "Metric": "Homes sold at list price percent",
        "Value": at_list_percent
    },
    {
        "Metric": "Homes sold below list price percent",
        "Value": below_list_percent
    },
    {
        "Metric": "Median DaysOnMarket",
        "Value": sold["DaysOnMarket"].median()
    },
    {
        "Metric": "Average DaysOnMarket",
        "Value": sold["DaysOnMarket"].mean()
    }
])

eda_summary.to_csv(
    "reports/week2_3_eda_summary_metrics.csv",
    index=False
)

print("Saved reports/week2_3_eda_summary_metrics.csv")

print("\nEDA validation questions complete.")
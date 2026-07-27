import os
import pandas as pd

outputs_folder = "outputs"
reports_folder = "reports"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

# Prefer the most prepared Sold dataset from Weeks 4-5.
sold_input = "outputs/CRMLSSold_Residential_Cleaned_Prepared_SchoolDistrict.csv"

if not os.path.exists(sold_input):
    sold_input = "outputs/CRMLSSold_Residential_Cleaned_Prepared.csv"

if not os.path.exists(sold_input):
    sold_input = "outputs/CRMLSSold_Combined_Residential_Enriched.csv"

print("Loading Sold dataset...")
print("Input file:", sold_input)

sold = pd.read_csv(sold_input, low_memory=False)

print("Starting shape:", sold.shape)

# ------------------------------------------------------------
# 1. Ensure numeric helper columns exist
# ------------------------------------------------------------

numeric_fields = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket"
]

for field in numeric_fields:
    num_col = f"{field}_num"

    if num_col not in sold.columns and field in sold.columns:
        sold[num_col] = pd.to_numeric(
            sold[field],
            errors="coerce"
        )

# ------------------------------------------------------------
# 2. Ensure datetime helper columns exist
# ------------------------------------------------------------

date_fields = [
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate"
]

for field in date_fields:
    dt_col = f"{field}_dt"

    if dt_col not in sold.columns and field in sold.columns:
        sold[dt_col] = pd.to_datetime(
            sold[field],
            errors="coerce"
        )
    elif dt_col in sold.columns:
        sold[dt_col] = pd.to_datetime(
            sold[dt_col],
            errors="coerce"
        )

# ------------------------------------------------------------
# 3. Feature engineering: market metrics
# ------------------------------------------------------------

print("\nCreating engineered market metrics...")

# Price Ratio:
# ClosePrice / OriginalListPrice
sold["price_ratio"] = (
    sold["ClosePrice_num"] /
    sold["OriginalListPrice_num"].where(
        sold["OriginalListPrice_num"] > 0
    )
)

# Close-to-original-list ratio:
# Same formula required by handbook, named explicitly for clarity.
sold["close_to_original_list_ratio"] = (
    sold["ClosePrice_num"] /
    sold["OriginalListPrice_num"].where(
        sold["OriginalListPrice_num"] > 0
    )
)

# Optional useful metric:
# ClosePrice / ListPrice
# This helps compare final close price to current/listed price.
sold["close_to_list_ratio"] = (
    sold["ClosePrice_num"] /
    sold["ListPrice_num"].where(
        sold["ListPrice_num"] > 0
    )
)

# Price per square foot:
# ClosePrice / LivingArea
sold["price_per_sqft"] = (
    sold["ClosePrice_num"] /
    sold["LivingArea_num"].where(
        sold["LivingArea_num"] > 0
    )
)

# Days on market metric:
sold["days_on_market_metric"] = sold["DaysOnMarket_num"]

# Time-series variables from CloseDate
sold["close_year"] = sold["CloseDate_dt"].dt.year
sold["close_month"] = sold["CloseDate_dt"].dt.month
sold["close_quarter"] = sold["CloseDate_dt"].dt.quarter
sold["close_yrmo"] = sold["CloseDate_dt"].dt.to_period("M").astype(str)

# Listing-to-contract days:
# PurchaseContractDate - ListingContractDate
sold["listing_to_contract_days"] = (
    sold["PurchaseContractDate_dt"] -
    sold["ListingContractDate_dt"]
).dt.days

# Contract-to-close days:
# CloseDate - PurchaseContractDate
sold["contract_to_close_days"] = (
    sold["CloseDate_dt"] -
    sold["PurchaseContractDate_dt"]
).dt.days

# ------------------------------------------------------------
# 4. Metric validation report
# ------------------------------------------------------------

metric_cols = [
    "price_ratio",
    "close_to_original_list_ratio",
    "close_to_list_ratio",
    "price_per_sqft",
    "days_on_market_metric",
    "close_year",
    "close_month",
    "close_yrmo",
    "listing_to_contract_days",
    "contract_to_close_days"
]

validation_rows = []

for col in metric_cols:
    validation_rows.append({
        "Metric": col,
        "Populated Rows": sold[col].notna().sum(),
        "Missing Rows": sold[col].isna().sum(),
        "Total Rows": len(sold),
        "Populated Percent": sold[col].notna().sum() / len(sold) * 100
    })

metric_validation = pd.DataFrame(validation_rows)

metric_validation.to_csv(
    "reports/week6_metric_validation_summary.csv",
    index=False
)

print("Saved reports/week6_metric_validation_summary.csv")

# ------------------------------------------------------------
# 5. Sample output table with engineered metrics
# ------------------------------------------------------------

sample_columns = [
    "ListingKey",
    "PropertyType",
    "PropertySubType",
    "CountyOrParish",
    "MLSAreaMajor",
    "CloseDate",
    "ClosePrice_num",
    "OriginalListPrice_num",
    "ListPrice_num",
    "LivingArea_num",
    "price_ratio",
    "close_to_original_list_ratio",
    "close_to_list_ratio",
    "price_per_sqft",
    "days_on_market_metric",
    "close_year",
    "close_month",
    "close_yrmo",
    "listing_to_contract_days",
    "contract_to_close_days",
    "rate_30yr_fixed",
    "UnifiedSchoolDistrictName"
]

sample_columns = [
    col for col in sample_columns
    if col in sold.columns
]

sample_output = sold[sample_columns].head(100)

sample_output.to_csv(
    "reports/week6_sample_engineered_metrics.csv",
    index=False
)

print("Saved reports/week6_sample_engineered_metrics.csv")

# ------------------------------------------------------------
# 6. Segmented summary by CountyOrParish
# ------------------------------------------------------------

county_summary = (
    sold
    .groupby("CountyOrParish", dropna=False)
    .agg(
        RowCount=("ClosePrice_num", "count"),
        MedianClosePrice=("ClosePrice_num", "median"),
        AverageClosePrice=("ClosePrice_num", "mean"),
        MedianOriginalListPrice=("OriginalListPrice_num", "median"),
        MedianPriceRatio=("price_ratio", "median"),
        MedianCloseToListRatio=("close_to_list_ratio", "median"),
        MedianPricePerSqFt=("price_per_sqft", "median"),
        AveragePricePerSqFt=("price_per_sqft", "mean"),
        MedianDaysOnMarket=("days_on_market_metric", "median"),
        AverageDaysOnMarket=("days_on_market_metric", "mean"),
        MedianListingToContractDays=("listing_to_contract_days", "median"),
        MedianContractToCloseDays=("contract_to_close_days", "median"),
        MedianMortgageRate=("rate_30yr_fixed", "median")
    )
    .reset_index()
)

county_summary = county_summary.sort_values(
    by="RowCount",
    ascending=False
)

county_summary.to_csv(
    "reports/week6_county_market_metrics_summary.csv",
    index=False
)

print("Saved reports/week6_county_market_metrics_summary.csv")

# ------------------------------------------------------------
# 7. Optional school district summary, if available
# ------------------------------------------------------------

if "UnifiedSchoolDistrictName" in sold.columns:
    district_summary = (
        sold
        .groupby("UnifiedSchoolDistrictName", dropna=False)
        .agg(
            RowCount=("ClosePrice_num", "count"),
            MedianClosePrice=("ClosePrice_num", "median"),
            AverageClosePrice=("ClosePrice_num", "mean"),
            MedianPriceRatio=("price_ratio", "median"),
            MedianCloseToListRatio=("close_to_list_ratio", "median"),
            MedianPricePerSqFt=("price_per_sqft", "median"),
            MedianDaysOnMarket=("days_on_market_metric", "median"),
            MedianListingToContractDays=("listing_to_contract_days", "median"),
            MedianContractToCloseDays=("contract_to_close_days", "median")
        )
        .reset_index()
    )

    district_summary = district_summary.sort_values(
        by="RowCount",
        ascending=False
    )

    district_summary.to_csv(
        "reports/week6_school_district_market_metrics_summary.csv",
        index=False
    )

    print("Saved reports/week6_school_district_market_metrics_summary.csv")

# ------------------------------------------------------------
# 8. Save feature-engineered dataset
# ------------------------------------------------------------

sold_output = "outputs/CRMLSSold_Residential_Feature_Engineered.csv"

sold.to_csv(
    sold_output,
    index=False
)

print("\nSaved feature-engineered dataset:")
print(sold_output)

print("\nWeek 6 feature engineering complete.")
print("Final shape:", sold.shape)
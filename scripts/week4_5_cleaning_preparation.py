import os
import pandas as pd

outputs_folder = "outputs"
reports_folder = "reports"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

# Prefer enriched datasets from Week 3 if they exist.
sold_input = "outputs/CRMLSSold_Combined_Residential_Enriched.csv"
listings_input = "outputs/CRMLSListing_Combined_Residential_Enriched.csv"

if not os.path.exists(sold_input):
    sold_input = "outputs/CRMLSSold_Combined_Residential.csv"

if not os.path.exists(listings_input):
    listings_input = "outputs/CRMLSListing_Combined_Residential.csv"

print("Loading datasets...")
print("Sold input:", sold_input)
print("Listings input:", listings_input)

sold = pd.read_csv(sold_input, low_memory=False)
listings = pd.read_csv(listings_input, low_memory=False)

print("Sold starting shape:", sold.shape)
print("Listings starting shape:", listings.shape)

current_year = pd.Timestamp.today().year
max_reasonable_year_built = current_year + 1

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def convert_date_column(df, column):
    if column in df.columns:
        df[f"{column}_dt"] = pd.to_datetime(df[column], errors="coerce")
    return df


def add_date_parts(df, date_column, prefix):
    dt_col = f"{date_column}_dt"

    if dt_col in df.columns:
        df[f"{prefix}_year"] = df[dt_col].dt.year
        df[f"{prefix}_month"] = df[dt_col].dt.month
        df[f"{prefix}_quarter"] = df[dt_col].dt.quarter
        df[f"{prefix}_year_month"] = df[dt_col].dt.to_period("M").astype(str)

    return df


def convert_numeric_column(df, column):
    if column in df.columns:
        df[f"{column}_num"] = pd.to_numeric(df[column], errors="coerce")
    return df


def create_invalid_flag(df, numeric_column, rule_name, condition):
    flag_col = f"{rule_name}_flag"
    df[flag_col] = condition.fillna(False).astype(int)
    return df


def create_outlier_flags(df, numeric_column):
    num_col = f"{numeric_column}_num"

    if num_col not in df.columns:
        return df

    series = df[num_col].dropna()

    if series.empty:
        return df

    p01 = series.quantile(0.01)
    p99 = series.quantile(0.99)

    df[f"{numeric_column}_below_p01_flag"] = (
        df[num_col] < p01
    ).fillna(False).astype(int)

    df[f"{numeric_column}_above_p99_flag"] = (
        df[num_col] > p99
    ).fillna(False).astype(int)

    return df


def summarize_flags(df, dataset_name):
    flag_cols = [col for col in df.columns if col.endswith("_flag")]

    rows = []

    for col in flag_cols:
        rows.append({
            "Dataset": dataset_name,
            "Flag": col,
            "Flagged Rows": int(df[col].sum()),
            "Total Rows": len(df),
            "Flagged Percent": df[col].sum() / len(df) * 100
        })

    return rows


# ------------------------------------------------------------
# 1. Date conversion and date-part creation
# ------------------------------------------------------------

print("\nConverting date columns...")

sold_date_columns = [
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate",
    "ContractStatusChangeDate"
]

listing_date_columns = [
    "ListingContractDate",
    "ContractStatusChangeDate",
    "CloseDate"
]

for col in sold_date_columns:
    sold = convert_date_column(sold, col)

for col in listing_date_columns:
    listings = convert_date_column(listings, col)

sold = add_date_parts(sold, "CloseDate", "close")
sold = add_date_parts(sold, "ListingContractDate", "listing_contract")
sold = add_date_parts(sold, "PurchaseContractDate", "purchase_contract")

listings = add_date_parts(listings, "ListingContractDate", "listing_contract")
listings = add_date_parts(listings, "ContractStatusChangeDate", "contract_status_change")

# ------------------------------------------------------------
# 2. Date consistency flags
# ------------------------------------------------------------

print("Creating date consistency flags...")

if "CloseDate_dt" in sold.columns:
    sold["missing_close_date_flag"] = sold["CloseDate_dt"].isna().astype(int)

if "ListingContractDate_dt" in sold.columns and "CloseDate_dt" in sold.columns:
    sold["listing_after_close_flag"] = (
        sold["ListingContractDate_dt"] > sold["CloseDate_dt"]
    ).fillna(False).astype(int)

if "PurchaseContractDate_dt" in sold.columns and "CloseDate_dt" in sold.columns:
    sold["purchase_after_close_flag"] = (
        sold["PurchaseContractDate_dt"] > sold["CloseDate_dt"]
    ).fillna(False).astype(int)

if "PurchaseContractDate_dt" in sold.columns and "ListingContractDate_dt" in sold.columns:
    sold["purchase_before_listing_flag"] = (
        sold["PurchaseContractDate_dt"] < sold["ListingContractDate_dt"]
    ).fillna(False).astype(int)

if "ListingContractDate_dt" in listings.columns:
    listings["missing_listing_contract_date_flag"] = (
        listings["ListingContractDate_dt"].isna()
    ).astype(int)

# ------------------------------------------------------------
# 3. Numeric conversion and invalid-value flags
# ------------------------------------------------------------

print("Creating numeric quality flags...")

numeric_fields = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]

for field in numeric_fields:
    sold = convert_numeric_column(sold, field)
    listings = convert_numeric_column(listings, field)

# Sold invalid numeric flags
if "ClosePrice_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "ClosePrice",
        "invalid_close_price",
        sold["ClosePrice_num"] <= 0
    )

if "ListPrice_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "ListPrice",
        "invalid_list_price",
        sold["ListPrice_num"] <= 0
    )

if "OriginalListPrice_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "OriginalListPrice",
        "invalid_original_list_price",
        sold["OriginalListPrice_num"] <= 0
    )

if "LivingArea_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "LivingArea",
        "invalid_living_area",
        sold["LivingArea_num"] <= 0
    )

if "LotSizeAcres_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "LotSizeAcres",
        "invalid_lot_size_acres",
        sold["LotSizeAcres_num"] < 0
    )

if "BedroomsTotal_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "BedroomsTotal",
        "invalid_bedrooms_total",
        sold["BedroomsTotal_num"] < 0
    )

if "BathroomsTotalInteger_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "BathroomsTotalInteger",
        "invalid_bathrooms_total_integer",
        sold["BathroomsTotalInteger_num"] < 0
    )

if "DaysOnMarket_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "DaysOnMarket",
        "invalid_days_on_market",
        sold["DaysOnMarket_num"] < 0
    )

if "YearBuilt_num" in sold.columns:
    sold = create_invalid_flag(
        sold,
        "YearBuilt",
        "invalid_year_built",
        (
            (sold["YearBuilt_num"] < 1800) |
            (sold["YearBuilt_num"] > max_reasonable_year_built)
        )
    )

# Listings invalid numeric flags
if "ListPrice_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "ListPrice",
        "invalid_list_price",
        listings["ListPrice_num"] <= 0
    )

if "OriginalListPrice_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "OriginalListPrice",
        "invalid_original_list_price",
        listings["OriginalListPrice_num"] <= 0
    )

if "LivingArea_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "LivingArea",
        "invalid_living_area",
        listings["LivingArea_num"] <= 0
    )

if "LotSizeAcres_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "LotSizeAcres",
        "invalid_lot_size_acres",
        listings["LotSizeAcres_num"] < 0
    )

if "BedroomsTotal_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "BedroomsTotal",
        "invalid_bedrooms_total",
        listings["BedroomsTotal_num"] < 0
    )

if "BathroomsTotalInteger_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "BathroomsTotalInteger",
        "invalid_bathrooms_total_integer",
        listings["BathroomsTotalInteger_num"] < 0
    )

if "DaysOnMarket_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "DaysOnMarket",
        "invalid_days_on_market",
        listings["DaysOnMarket_num"] < 0
    )

if "YearBuilt_num" in listings.columns:
    listings = create_invalid_flag(
        listings,
        "YearBuilt",
        "invalid_year_built",
        (
            (listings["YearBuilt_num"] < 1800) |
            (listings["YearBuilt_num"] > max_reasonable_year_built)
        )
    )

# ------------------------------------------------------------
# 4. Outlier flags using 1st and 99th percentiles
# ------------------------------------------------------------

print("Creating outlier flags...")

for field in numeric_fields:
    sold = create_outlier_flags(sold, field)
    listings = create_outlier_flags(listings, field)

# ------------------------------------------------------------
# 5. Geographic validation
# ------------------------------------------------------------

print("Creating geographic quality flags...")

geo_columns = ["Latitude", "Longitude"]

for col in geo_columns:
    sold = convert_numeric_column(sold, col)
    listings = convert_numeric_column(listings, col)

if "Latitude_num" in sold.columns and "Longitude_num" in sold.columns:
    sold["missing_coordinates_flag"] = (
        sold["Latitude_num"].isna() |
        sold["Longitude_num"].isna()
    ).astype(int)

    sold["outside_california_coordinate_range_flag"] = (
        (sold["Latitude_num"] < 32) |
        (sold["Latitude_num"] > 42.5) |
        (sold["Longitude_num"] < -125) |
        (sold["Longitude_num"] > -113.5)
    ).fillna(False).astype(int)

if "Latitude_num" in listings.columns and "Longitude_num" in listings.columns:
    listings["missing_coordinates_flag"] = (
        listings["Latitude_num"].isna() |
        listings["Longitude_num"].isna()
    ).astype(int)

    listings["outside_california_coordinate_range_flag"] = (
        (listings["Latitude_num"] < 32) |
        (listings["Latitude_num"] > 42.5) |
        (listings["Longitude_num"] < -125) |
        (listings["Longitude_num"] > -113.5)
    ).fillna(False).astype(int)

# ------------------------------------------------------------
# 6. Summary reports
# ------------------------------------------------------------

print("Creating cleaning summary reports...")

flag_summary_rows = []
flag_summary_rows.extend(summarize_flags(sold, "sold"))
flag_summary_rows.extend(summarize_flags(listings, "listings"))

flag_summary = pd.DataFrame(flag_summary_rows)

flag_summary.to_csv(
    "reports/week4_5_cleaning_flag_summary.csv",
    index=False
)

dataset_summary = pd.DataFrame([
    {
        "Dataset": "sold",
        "Input File": sold_input,
        "Rows": sold.shape[0],
        "Columns After Preparation": sold.shape[1]
    },
    {
        "Dataset": "listings",
        "Input File": listings_input,
        "Rows": listings.shape[0],
        "Columns After Preparation": listings.shape[1]
    }
])

dataset_summary.to_csv(
    "reports/week4_5_dataset_preparation_summary.csv",
    index=False
)

# ------------------------------------------------------------
# 7. Save cleaned/prepared datasets
# ------------------------------------------------------------

sold_output = "outputs/CRMLSSold_Residential_Cleaned_Prepared.csv"
listings_output = "outputs/CRMLSListing_Residential_Cleaned_Prepared.csv"

sold.to_csv(sold_output, index=False)
listings.to_csv(listings_output, index=False)

print("\nSaved cleaned/prepared datasets:")
print(sold_output)
print(listings_output)

print("\nSaved reports:")
print("reports/week4_5_cleaning_flag_summary.csv")
print("reports/week4_5_dataset_preparation_summary.csv")

print("\nWeek 4-5 cleaning/preparation complete.")
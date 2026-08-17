import os
import pandas as pd

outputs_folder = "outputs"
reports_folder = "reports"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

# ------------------------------------------------------------
# 1. Input files
# ------------------------------------------------------------

sold_input = "outputs/CRMLSSold_Residential_Week7_Clean_Filtered.csv"

if not os.path.exists(sold_input):
    sold_input = "outputs/CRMLSSold_Residential_Feature_Engineered.csv"

listings_input = "outputs/CRMLSListing_Residential_Cleaned_Prepared_SchoolDistrict.csv"

if not os.path.exists(listings_input):
    listings_input = "outputs/CRMLSListing_Residential_Cleaned_Prepared.csv"

print("Loading datasets...")
print("Sold input:", sold_input)
print("Listings input:", listings_input)

sold = pd.read_csv(sold_input, low_memory=False)
listings = pd.read_csv(listings_input, low_memory=False)

print("Sold shape:", sold.shape)
print("Listings shape:", listings.shape)

# ------------------------------------------------------------
# 2. Helper functions
# ------------------------------------------------------------

def first_existing_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def ensure_numeric(df, source_col, output_col):
    if source_col in df.columns:
        df[output_col] = pd.to_numeric(df[source_col], errors="coerce")
    elif output_col not in df.columns:
        df[output_col] = pd.NA
    return df


def clean_text_column(df, source_col, output_col, default="Unknown"):
    if source_col and source_col in df.columns:
        df[output_col] = (
            df[source_col]
            .astype(str)
            .str.strip()
            .replace({"nan": default, "None": default, "": default})
        )
    else:
        df[output_col] = default
    return df


def clean_zip(df, source_col, output_col="ZipCode_clean"):
    if source_col and source_col in df.columns:
        df[output_col] = (
            df[source_col]
            .astype(str)
            .str.extract(r"(\d{5})")[0]
            .fillna("Unknown")
        )
    else:
        df[output_col] = "Unknown"
    return df


def build_agent_name(df):
    full_name_col = first_existing_column(
        df,
        ["ListAgentFullName", "ListAgentName"]
    )

    if full_name_col:
        df["ListAgentName_clean"] = (
            df[full_name_col]
            .astype(str)
            .str.strip()
            .replace({"nan": "Unknown", "None": "Unknown", "": "Unknown"})
        )
    else:
        first_col = first_existing_column(df, ["ListAgentFirstName"])
        last_col = first_existing_column(df, ["ListAgentLastName"])

        if first_col and last_col:
            df["ListAgentName_clean"] = (
                df[first_col].fillna("").astype(str).str.strip()
                + " "
                + df[last_col].fillna("").astype(str).str.strip()
            ).str.strip()

            df["ListAgentName_clean"] = df["ListAgentName_clean"].replace(
                {"": "Unknown"}
            )
        else:
            df["ListAgentName_clean"] = "Unknown"

    return df


# ------------------------------------------------------------
# 3. Prepare Sold dataset for Tableau
# ------------------------------------------------------------

print("\nPreparing Sold Tableau extract...")

# Date fields
if "CloseDate_dt" not in sold.columns and "CloseDate" in sold.columns:
    sold["CloseDate_dt"] = pd.to_datetime(sold["CloseDate"], errors="coerce")
else:
    sold["CloseDate_dt"] = pd.to_datetime(sold["CloseDate_dt"], errors="coerce")

sold["close_year"] = sold["CloseDate_dt"].dt.year
sold["close_month"] = sold["CloseDate_dt"].dt.month
sold["close_yrmo"] = sold["CloseDate_dt"].dt.to_period("M").astype(str)

# Numeric fields
numeric_map = {
    "ClosePrice": "ClosePrice_num",
    "OriginalListPrice": "OriginalListPrice_num",
    "ListPrice": "ListPrice_num",
    "LivingArea": "LivingArea_num",
    "DaysOnMarket": "DaysOnMarket_num"
}

for source_col, output_col in numeric_map.items():
    if output_col not in sold.columns:
        sold = ensure_numeric(sold, source_col, output_col)

# Recreate important metrics if needed
if "close_to_original_list_ratio" not in sold.columns:
    sold["close_to_original_list_ratio"] = (
        sold["ClosePrice_num"] /
        sold["OriginalListPrice_num"].where(sold["OriginalListPrice_num"] > 0)
    )

if "close_to_list_ratio" not in sold.columns:
    sold["close_to_list_ratio"] = (
        sold["ClosePrice_num"] /
        sold["ListPrice_num"].where(sold["ListPrice_num"] > 0)
    )

if "price_per_sqft" not in sold.columns:
    sold["price_per_sqft"] = (
        sold["ClosePrice_num"] /
        sold["LivingArea_num"].where(sold["LivingArea_num"] > 0)
    )

if "days_on_market_metric" not in sold.columns:
    sold["days_on_market_metric"] = sold["DaysOnMarket_num"]

# Clean dimensions
city_col = first_existing_column(sold, ["City"])
county_col = first_existing_column(sold, ["CountyOrParish"])
zip_col = first_existing_column(sold, ["PostalCode", "PostalCodePlus4", "ZipCode"])
subtype_col = first_existing_column(sold, ["PropertySubType"])
mls_area_col = first_existing_column(sold, ["MLSAreaMajor"])
list_office_col = first_existing_column(sold, ["ListOfficeName"])
buyer_office_col = first_existing_column(sold, ["BuyerOfficeName"])

sold = clean_text_column(sold, city_col, "City_clean")
sold = clean_text_column(sold, county_col, "County_clean")
sold = clean_zip(sold, zip_col)
sold = clean_text_column(sold, subtype_col, "PropertySubType_clean")
sold = clean_text_column(sold, mls_area_col, "MLSAreaMajor_clean")
sold = clean_text_column(sold, list_office_col, "ListOfficeName_clean")
sold = clean_text_column(sold, buyer_office_col, "BuyerOfficeName_clean")
sold = build_agent_name(sold)

if "UnifiedSchoolDistrictName" not in sold.columns:
    sold["UnifiedSchoolDistrictName"] = "Unknown"

# ------------------------------------------------------------
# 4. Prepare Listings dataset for Tableau
# ------------------------------------------------------------

print("Preparing Listings Tableau extract...")

if "ListingContractDate_dt" not in listings.columns and "ListingContractDate" in listings.columns:
    listings["ListingContractDate_dt"] = pd.to_datetime(
        listings["ListingContractDate"],
        errors="coerce"
    )
else:
    listings["ListingContractDate_dt"] = pd.to_datetime(
        listings["ListingContractDate_dt"],
        errors="coerce"
    )

listings["listing_year"] = listings["ListingContractDate_dt"].dt.year
listings["listing_month"] = listings["ListingContractDate_dt"].dt.month
listings["listing_yrmo"] = listings["ListingContractDate_dt"].dt.to_period("M").astype(str)

if "ListPrice_num" not in listings.columns:
    listings = ensure_numeric(listings, "ListPrice", "ListPrice_num")

if "OriginalListPrice_num" not in listings.columns:
    listings = ensure_numeric(listings, "OriginalListPrice", "OriginalListPrice_num")

if "LivingArea_num" not in listings.columns:
    listings = ensure_numeric(listings, "LivingArea", "LivingArea_num")

listing_city_col = first_existing_column(listings, ["City"])
listing_county_col = first_existing_column(listings, ["CountyOrParish"])
listing_zip_col = first_existing_column(listings, ["PostalCode", "PostalCodePlus4", "ZipCode"])
listing_subtype_col = first_existing_column(listings, ["PropertySubType"])
listing_mls_area_col = first_existing_column(listings, ["MLSAreaMajor"])
listing_office_col = first_existing_column(listings, ["ListOfficeName"])

listings = clean_text_column(listings, listing_city_col, "City_clean")
listings = clean_text_column(listings, listing_county_col, "County_clean")
listings = clean_zip(listings, listing_zip_col)
listings = clean_text_column(listings, listing_subtype_col, "PropertySubType_clean")
listings = clean_text_column(listings, listing_mls_area_col, "MLSAreaMajor_clean")
listings = clean_text_column(listings, listing_office_col, "ListOfficeName_clean")
listings = build_agent_name(listings)

if "UnifiedSchoolDistrictName" not in listings.columns:
    listings["UnifiedSchoolDistrictName"] = "Unknown"

# ------------------------------------------------------------
# 5. Save Tableau row-level extracts
# ------------------------------------------------------------

sold_extract_cols = [
    "ListingKey",
    "CloseDate",
    "close_year",
    "close_month",
    "close_yrmo",
    "City_clean",
    "County_clean",
    "ZipCode_clean",
    "PropertySubType_clean",
    "MLSAreaMajor_clean",
    "ClosePrice_num",
    "OriginalListPrice_num",
    "ListPrice_num",
    "LivingArea_num",
    "DaysOnMarket_num",
    "close_to_original_list_ratio",
    "close_to_list_ratio",
    "price_per_sqft",
    "days_on_market_metric",
    "rate_30yr_fixed",
    "UnifiedSchoolDistrictName",
    "ListAgentName_clean",
    "ListOfficeName_clean",
    "BuyerOfficeName_clean"
]

sold_extract_cols = [col for col in sold_extract_cols if col in sold.columns]

sold_extract = sold[sold_extract_cols].copy()

sold_extract.to_csv(
    "outputs/tableau_sold_clean_filtered_extract.csv",
    index=False
)

print("Saved outputs/tableau_sold_clean_filtered_extract.csv")

listings_extract_cols = [
    "ListingKey",
    "ListingContractDate",
    "listing_year",
    "listing_month",
    "listing_yrmo",
    "City_clean",
    "County_clean",
    "ZipCode_clean",
    "PropertySubType_clean",
    "MLSAreaMajor_clean",
    "ListPrice_num",
    "OriginalListPrice_num",
    "LivingArea_num",
    "rate_30yr_fixed",
    "UnifiedSchoolDistrictName",
    "ListAgentName_clean",
    "ListOfficeName_clean"
]

listings_extract_cols = [col for col in listings_extract_cols if col in listings.columns]

listings_extract = listings[listings_extract_cols].copy()

listings_extract.to_csv(
    "outputs/tableau_listings_prepared_extract.csv",
    index=False
)

print("Saved outputs/tableau_listings_prepared_extract.csv")

# ------------------------------------------------------------
# 6. Market analysis summaries
# ------------------------------------------------------------

print("Creating market analysis summaries...")

market_dims = [
    "close_yrmo",
    "close_year",
    "close_month",
    "County_clean",
    "City_clean",
    "ZipCode_clean",
    "PropertySubType_clean"
]

closed_sales_summary = (
    sold
    .groupby(market_dims, dropna=False)
    .agg(
        ClosedSales=("ClosePrice_num", "count"),
        MedianClosePrice=("ClosePrice_num", "median"),
        AverageClosePrice=("ClosePrice_num", "mean"),
        AverageDaysOnMarket=("days_on_market_metric", "mean"),
        MedianDaysOnMarket=("days_on_market_metric", "median"),
        AverageCloseToOriginalListRatio=("close_to_original_list_ratio", "mean"),
        MedianCloseToOriginalListRatio=("close_to_original_list_ratio", "median"),
        AveragePricePerSqFt=("price_per_sqft", "mean"),
        MedianPricePerSqFt=("price_per_sqft", "median"),
        MedianMortgageRate=("rate_30yr_fixed", "median")
    )
    .reset_index()
)

closed_sales_summary.to_csv(
    "outputs/tableau_market_closed_sales_summary.csv",
    index=False
)

print("Saved outputs/tableau_market_closed_sales_summary.csv")

listing_dims = [
    "listing_yrmo",
    "listing_year",
    "listing_month",
    "County_clean",
    "City_clean",
    "ZipCode_clean",
    "PropertySubType_clean"
]

new_listings_summary = (
    listings
    .groupby(listing_dims, dropna=False)
    .agg(
        NewListings=("ListingKey", "count"),
        MedianListPrice=("ListPrice_num", "median"),
        AverageListPrice=("ListPrice_num", "mean"),
        MedianOriginalListPrice=("OriginalListPrice_num", "median")
    )
    .reset_index()
)

new_listings_summary.to_csv(
    "outputs/tableau_market_new_listings_summary.csv",
    index=False
)

print("Saved outputs/tableau_market_new_listings_summary.csv")

# ------------------------------------------------------------
# 7. Competitive analysis summaries
# ------------------------------------------------------------

print("Creating competitive analysis summaries...")

agent_summary = (
    sold[sold["ListAgentName_clean"] != "Unknown"]
    .groupby("ListAgentName_clean", dropna=False)
    .agg(
        Units=("ClosePrice_num", "count"),
        SalesVolume=("ClosePrice_num", "sum"),
        MedianClosePrice=("ClosePrice_num", "median"),
        AverageClosePrice=("ClosePrice_num", "mean")
    )
    .reset_index()
    .sort_values(
        by=["SalesVolume", "Units"],
        ascending=False
    )
    .head(100)
)

agent_summary.to_csv(
    "outputs/tableau_top_100_listing_agents.csv",
    index=False
)

print("Saved outputs/tableau_top_100_listing_agents.csv")

office_summary = (
    sold[sold["ListOfficeName_clean"] != "Unknown"]
    .groupby("ListOfficeName_clean", dropna=False)
    .agg(
        Units=("ClosePrice_num", "count"),
        SalesVolume=("ClosePrice_num", "sum"),
        MedianClosePrice=("ClosePrice_num", "median"),
        AverageClosePrice=("ClosePrice_num", "mean")
    )
    .reset_index()
    .sort_values(
        by=["SalesVolume", "Units"],
        ascending=False
    )
    .head(100)
)

office_summary.to_csv(
    "outputs/tableau_top_100_listing_offices.csv",
    index=False
)

print("Saved outputs/tableau_top_100_listing_offices.csv")

zip_heatmap_summary = (
    sold
    .groupby(
        [
            "close_yrmo",
            "County_clean",
            "City_clean",
            "ZipCode_clean",
            "PropertySubType_clean"
        ],
        dropna=False
    )
    .agg(
        HomesSold=("ClosePrice_num", "count"),
        MedianClosePrice=("ClosePrice_num", "median"),
        AverageClosePrice=("ClosePrice_num", "mean")
    )
    .reset_index()
)

zip_heatmap_summary.to_csv(
    "outputs/tableau_zip_code_heatmap_summary.csv",
    index=False
)

print("Saved outputs/tableau_zip_code_heatmap_summary.csv")

# ------------------------------------------------------------
# 8. Summary report
# ------------------------------------------------------------

prep_summary = pd.DataFrame([
    {
        "Output File": "outputs/tableau_sold_clean_filtered_extract.csv",
        "Rows": len(sold_extract),
        "Purpose": "Row-level clean Sold extract for Tableau market and competitive dashboards"
    },
    {
        "Output File": "outputs/tableau_listings_prepared_extract.csv",
        "Rows": len(listings_extract),
        "Purpose": "Row-level Listings extract for new listings dashboard"
    },
    {
        "Output File": "outputs/tableau_market_closed_sales_summary.csv",
        "Rows": len(closed_sales_summary),
        "Purpose": "Monthly closed-sales market summary"
    },
    {
        "Output File": "outputs/tableau_market_new_listings_summary.csv",
        "Rows": len(new_listings_summary),
        "Purpose": "Monthly new-listings market summary"
    },
    {
        "Output File": "outputs/tableau_top_100_listing_agents.csv",
        "Rows": len(agent_summary),
        "Purpose": "Top 100 listing agents by sales volume and units"
    },
    {
        "Output File": "outputs/tableau_top_100_listing_offices.csv",
        "Rows": len(office_summary),
        "Purpose": "Top 100 listing offices by sales volume and units"
    },
    {
        "Output File": "outputs/tableau_zip_code_heatmap_summary.csv",
        "Rows": len(zip_heatmap_summary),
        "Purpose": "Zip-code-level heat map source for median close price and homes sold"
    }
])

prep_summary.to_csv(
    "reports/week8_10_tableau_preparation_summary.csv",
    index=False
)

print("\nSaved reports/week8_10_tableau_preparation_summary.csv")

print("\nWeek 8-10 preliminary Tableau preparation complete.")
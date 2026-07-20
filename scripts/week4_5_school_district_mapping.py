import os
import pandas as pd
import geopandas as gpd

outputs_folder = "outputs"
reports_folder = "reports"
external_data_folder = "external_data"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

district_path = (
    "external_data/ca_school_district_areas_2025_26.geojson"
)

sold_input = "outputs/CRMLSSold_Residential_Cleaned_Prepared.csv"
listings_input = "outputs/CRMLSListing_Residential_Cleaned_Prepared.csv"

sold_output = "outputs/CRMLSSold_Residential_Cleaned_Prepared_SchoolDistrict.csv"
listings_output = "outputs/CRMLSListing_Residential_Cleaned_Prepared_SchoolDistrict.csv"

print("Loading school district boundaries...")

districts = gpd.read_file(district_path)

print("District boundary shape:", districts.shape)
print("District boundary CRS:", districts.crs)

districts["DistrictType_clean"] = (
    districts["DistrictType"]
    .astype(str)
    .str.strip()
)

unified_districts = districts[
    districts["DistrictType_clean"] == "Unified"
].copy()

print("Unified district shape:", unified_districts.shape)

if unified_districts.empty:
    print("\nERROR: No Unified districts found.")
    print("Available DistrictType values:")
    print(districts["DistrictType"].value_counts(dropna=False))
    raise SystemExit

unified_districts = unified_districts[
    [
        "DistrictName",
        "DistrictType",
        "CountyName",
        "CDSCode",
        "geometry"
    ]
].copy()

unified_districts = unified_districts.rename(
    columns={
        "DistrictName": "UnifiedSchoolDistrictName",
        "DistrictType": "UnifiedSchoolDistrictType",
        "CountyName": "UnifiedSchoolDistrictCounty",
        "CDSCode": "UnifiedSchoolDistrictCDSCode"
    }
)

print("\nUnified district sample:")
print(
    unified_districts[
        [
            "UnifiedSchoolDistrictName",
            "UnifiedSchoolDistrictCounty",
            "UnifiedSchoolDistrictCDSCode"
        ]
    ].head()
)


def add_school_districts(input_path, output_path, dataset_name):
    print(f"\nProcessing {dataset_name}...")
    print("Input:", input_path)

    df = pd.read_csv(input_path, low_memory=False)

    print("Starting shape:", df.shape)

    # Make sure coordinate helper columns exist.
    if "Latitude_num" not in df.columns:
        df["Latitude_num"] = pd.to_numeric(
            df["Latitude"],
            errors="coerce"
        )

    if "Longitude_num" not in df.columns:
        df["Longitude_num"] = pd.to_numeric(
            df["Longitude"],
            errors="coerce"
        )

    valid_coordinate_mask = (
        df["Latitude_num"].notna() &
        df["Longitude_num"].notna() &
        (df["Latitude_num"] >= 32) &
        (df["Latitude_num"] <= 42.5) &
        (df["Longitude_num"] >= -125) &
        (df["Longitude_num"] <= -113.5)
    )

    valid_df = df[valid_coordinate_mask].copy()

    print("Rows with valid coordinates:", len(valid_df))
    print("Rows without valid coordinates:", len(df) - len(valid_df))

    properties_gdf = gpd.GeoDataFrame(
        valid_df,
        geometry=gpd.points_from_xy(
            valid_df["Longitude_num"],
            valid_df["Latitude_num"]
        ),
        crs="EPSG:4326"
    )

    # Match CRS if the district file uses a different one.
    if unified_districts.crs != properties_gdf.crs:
        districts_for_join = unified_districts.to_crs(
            properties_gdf.crs
        )
    else:
        districts_for_join = unified_districts

    print("Running spatial join...")

    joined = gpd.sjoin(
        properties_gdf,
        districts_for_join,
        how="left",
        predicate="within"
    )

    district_cols = [
        "UnifiedSchoolDistrictName",
        "UnifiedSchoolDistrictType",
        "UnifiedSchoolDistrictCounty",
        "UnifiedSchoolDistrictCDSCode"
    ]

    # Initialize district columns on the full dataframe.
    for col in district_cols:
        df[col] = pd.NA

    # Write joined district values back to original rows.
    for col in district_cols:
        df.loc[joined.index, col] = joined[col]

    df["school_district_matched_flag"] = (
        df["UnifiedSchoolDistrictName"].notna()
    ).astype(int)

    df["school_district_unmatched_valid_coord_flag"] = (
        valid_coordinate_mask &
        df["UnifiedSchoolDistrictName"].isna()
    ).astype(int)

    df["school_district_missing_coord_flag"] = (
        ~valid_coordinate_mask
    ).astype(int)

    matched_count = int(df["school_district_matched_flag"].sum())
    unmatched_valid_coord_count = int(
        df["school_district_unmatched_valid_coord_flag"].sum()
    )
    missing_coord_count = int(
        df["school_district_missing_coord_flag"].sum()
    )

    summary = pd.DataFrame([
        {
            "Dataset": dataset_name,
            "Total Rows": len(df),
            "Valid Coordinate Rows": int(valid_coordinate_mask.sum()),
            "Matched School District Rows": matched_count,
            "Unmatched Rows With Valid Coordinates": unmatched_valid_coord_count,
            "Rows Without Valid Coordinates": missing_coord_count,
            "Matched Percent": matched_count / len(df) * 100,
            "Matched Percent Among Valid Coordinates": (
                matched_count / valid_coordinate_mask.sum() * 100
                if valid_coordinate_mask.sum() > 0
                else 0
            )
        }
    ])

    summary_path = (
        f"reports/{dataset_name}_school_district_mapping_summary.csv"
    )

    summary.to_csv(summary_path, index=False)

    top_districts = (
        df["UnifiedSchoolDistrictName"]
        .value_counts(dropna=False)
        .head(25)
        .reset_index()
    )

    top_districts.columns = [
        "UnifiedSchoolDistrictName",
        "Row Count"
    ]

    top_districts.to_csv(
        f"reports/{dataset_name}_top_school_districts.csv",
        index=False
    )

    df.to_csv(output_path, index=False)

    print("Saved output:", output_path)
    print("Saved summary:", summary_path)
    print("\nSummary:")
    print(summary.to_string(index=False))


add_school_districts(
    sold_input,
    sold_output,
    "sold"
)

add_school_districts(
    listings_input,
    listings_output,
    "listings"
)

print("\nSchool district mapping complete.")
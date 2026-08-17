import os
import pandas as pd

outputs_folder = "outputs"
reports_folder = "reports"

os.makedirs(outputs_folder, exist_ok=True)
os.makedirs(reports_folder, exist_ok=True)

# Prefer the Week 6 feature-engineered dataset.
input_path = "outputs/CRMLSSold_Residential_Feature_Engineered.csv"

if not os.path.exists(input_path):
    input_path = "outputs/CRMLSSold_Residential_Cleaned_Prepared_SchoolDistrict.csv"

if not os.path.exists(input_path):
    input_path = "outputs/CRMLSSold_Residential_Cleaned_Prepared.csv"

print("Loading dataset...")
print("Input file:", input_path)

df = pd.read_csv(input_path, low_memory=False)

print("Starting shape:", df.shape)

# ------------------------------------------------------------
# 1. Ensure key numeric columns exist
# ------------------------------------------------------------

required_fields = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket"
]

for field in required_fields:
    num_col = f"{field}_num"

    if num_col not in df.columns:
        df[num_col] = pd.to_numeric(
            df[field],
            errors="coerce"
        )

# ------------------------------------------------------------
# 2. Business-rule invalid flags
# ------------------------------------------------------------

print("\nCreating invalid-value flags...")

df["week7_invalid_close_price_flag"] = (
    df["ClosePrice_num"].isna() |
    (df["ClosePrice_num"] <= 0)
).astype(int)

df["week7_invalid_living_area_flag"] = (
    df["LivingArea_num"].isna() |
    (df["LivingArea_num"] <= 0)
).astype(int)

df["week7_invalid_days_on_market_flag"] = (
    df["DaysOnMarket_num"].isna() |
    (df["DaysOnMarket_num"] < 0)
).astype(int)

# ------------------------------------------------------------
# 3. IQR outlier flags
# ------------------------------------------------------------

print("Creating IQR outlier flags...")

iqr_rows = []

iqr_fields = [
    {
        "field": "ClosePrice",
        "num_col": "ClosePrice_num",
        "valid_condition": df["ClosePrice_num"] > 0
    },
    {
        "field": "LivingArea",
        "num_col": "LivingArea_num",
        "valid_condition": df["LivingArea_num"] > 0
    },
    {
        "field": "DaysOnMarket",
        "num_col": "DaysOnMarket_num",
        "valid_condition": df["DaysOnMarket_num"] >= 0
    }
]

for item in iqr_fields:
    field = item["field"]
    num_col = item["num_col"]
    valid_condition = item["valid_condition"]

    valid_series = df.loc[
        valid_condition,
        num_col
    ].dropna()

    q1 = valid_series.quantile(0.25)
    q3 = valid_series.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    low_flag = f"week7_{field}_iqr_low_outlier_flag"
    high_flag = f"week7_{field}_iqr_high_outlier_flag"
    any_flag = f"week7_{field}_iqr_outlier_flag"

    df[low_flag] = (
        valid_condition &
        (df[num_col] < lower_bound)
    ).fillna(False).astype(int)

    df[high_flag] = (
        valid_condition &
        (df[num_col] > upper_bound)
    ).fillna(False).astype(int)

    df[any_flag] = (
        (df[low_flag] == 1) |
        (df[high_flag] == 1)
    ).astype(int)

    iqr_rows.append({
        "Field": field,
        "Numeric Column": num_col,
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Lower Bound": lower_bound,
        "Upper Bound": upper_bound,
        "Low Outlier Rows": int(df[low_flag].sum()),
        "High Outlier Rows": int(df[high_flag].sum()),
        "Total IQR Outlier Rows": int(df[any_flag].sum()),
        "Total Rows": len(df),
        "Outlier Percent": df[any_flag].sum() / len(df) * 100
    })

iqr_summary = pd.DataFrame(iqr_rows)

iqr_summary.to_csv(
    "reports/week7_iqr_threshold_summary.csv",
    index=False
)

print("Saved reports/week7_iqr_threshold_summary.csv")

# ------------------------------------------------------------
# 4. Combined filtering rule
# ------------------------------------------------------------

print("Creating full analysis exclusion flag...")

week7_flag_cols = [
    "week7_invalid_close_price_flag",
    "week7_invalid_living_area_flag",
    "week7_invalid_days_on_market_flag",
    "week7_ClosePrice_iqr_outlier_flag",
    "week7_LivingArea_iqr_outlier_flag",
    "week7_DaysOnMarket_iqr_outlier_flag"
]

df["week7_analysis_exclusion_flag"] = (
    df[week7_flag_cols].sum(axis=1) > 0
).astype(int)

df["week7_analysis_keep_flag"] = (
    df["week7_analysis_exclusion_flag"] == 0
).astype(int)

filtered_df = df[
    df["week7_analysis_keep_flag"] == 1
].copy()

print("Filtered shape:", filtered_df.shape)

# ------------------------------------------------------------
# 5. Before/after dataset comparison
# ------------------------------------------------------------

print("Creating before/after comparison report...")

comparison_rows = []

metrics_to_compare = [
    "ClosePrice_num",
    "LivingArea_num",
    "DaysOnMarket_num",
    "price_per_sqft",
    "price_ratio",
    "close_to_list_ratio",
    "listing_to_contract_days",
    "contract_to_close_days"
]

available_metrics = [
    col for col in metrics_to_compare
    if col in df.columns
]

for col in available_metrics:
    before_median = df[col].median()
    after_median = filtered_df[col].median()

    comparison_rows.append({
        "Metric": col,
        "Before Median": before_median,
        "After Median": after_median,
        "Median Difference": after_median - before_median,
        "Before Non-Null Rows": df[col].notna().sum(),
        "After Non-Null Rows": filtered_df[col].notna().sum()
    })

comparison = pd.DataFrame(comparison_rows)

comparison.to_csv(
    "reports/week7_before_after_median_comparison.csv",
    index=False
)

print("Saved reports/week7_before_after_median_comparison.csv")

# ------------------------------------------------------------
# 6. Dataset size comparison
# ------------------------------------------------------------

size_summary = pd.DataFrame([
    {
        "Dataset": "Full flagged dataset",
        "Rows": len(df),
        "Columns": df.shape[1],
        "Percent of Original Rows": 100.0
    },
    {
        "Dataset": "Clean filtered analysis dataset",
        "Rows": len(filtered_df),
        "Columns": filtered_df.shape[1],
        "Percent of Original Rows": len(filtered_df) / len(df) * 100
    },
    {
        "Dataset": "Excluded rows",
        "Rows": len(df) - len(filtered_df),
        "Columns": "",
        "Percent of Original Rows": (len(df) - len(filtered_df)) / len(df) * 100
    }
])

size_summary.to_csv(
    "reports/week7_dataset_size_comparison.csv",
    index=False
)

print("Saved reports/week7_dataset_size_comparison.csv")

# ------------------------------------------------------------
# 7. Flag count summary
# ------------------------------------------------------------

flag_summary_rows = []

for col in week7_flag_cols + [
    "week7_analysis_exclusion_flag",
    "week7_analysis_keep_flag"
]:
    flag_summary_rows.append({
        "Flag": col,
        "Flagged Rows": int(df[col].sum()),
        "Total Rows": len(df),
        "Flagged Percent": df[col].sum() / len(df) * 100
    })

flag_summary = pd.DataFrame(flag_summary_rows)

flag_summary.to_csv(
    "reports/week7_outlier_flag_summary.csv",
    index=False
)

print("Saved reports/week7_outlier_flag_summary.csv")

# ------------------------------------------------------------
# 8. Written comparison summary
# ------------------------------------------------------------

full_rows = len(df)
filtered_rows = len(filtered_df)
excluded_rows = full_rows - filtered_rows
excluded_percent = excluded_rows / full_rows * 100

close_price_before = df["ClosePrice_num"].median()
close_price_after = filtered_df["ClosePrice_num"].median()

living_area_before = df["LivingArea_num"].median()
living_area_after = filtered_df["LivingArea_num"].median()

dom_before = df["DaysOnMarket_num"].median()
dom_after = filtered_df["DaysOnMarket_num"].median()

written_summary = f"""
Week 7 Outlier Detection and Data Quality Summary

Input dataset:
{input_path}

Method:
IQR filtering was applied to ClosePrice, LivingArea, and DaysOnMarket. Business-rule invalid values were flagged separately before IQR filtering. The full dataset was preserved with outlier and exclusion flags, and a separate clean filtered analysis dataset was created.

Dataset size comparison:
- Full flagged dataset rows: {full_rows:,}
- Clean filtered analysis dataset rows: {filtered_rows:,}
- Excluded rows: {excluded_rows:,}
- Excluded percent: {excluded_percent:.2f}%

Median comparison:
- ClosePrice median before filtering: {close_price_before:,.2f}
- ClosePrice median after filtering: {close_price_after:,.2f}
- LivingArea median before filtering: {living_area_before:,.2f}
- LivingArea median after filtering: {living_area_after:,.2f}
- DaysOnMarket median before filtering: {dom_before:,.2f}
- DaysOnMarket median after filtering: {dom_after:,.2f}

Important note:
Outlier records were not permanently deleted from the full dataset. They were flagged using Week 7 outlier columns. The filtered dataset is intended for analysis where extreme values would distort market averages and trends.
"""

with open(
    "reports/week7_written_before_after_summary.txt",
    "w"
) as f:
    f.write(written_summary)

print("Saved reports/week7_written_before_after_summary.txt")

# ------------------------------------------------------------
# 9. Save outputs
# ------------------------------------------------------------

full_flagged_output = "outputs/CRMLSSold_Residential_Week7_Full_Flagged.csv"
clean_filtered_output = "outputs/CRMLSSold_Residential_Week7_Clean_Filtered.csv"

df.to_csv(
    full_flagged_output,
    index=False
)

filtered_df.to_csv(
    clean_filtered_output,
    index=False
)

print("\nSaved output datasets:")
print(full_flagged_output)
print(clean_filtered_output)

print("\nWeek 7 outlier detection and data quality complete.")
print("Full flagged shape:", df.shape)
print("Clean filtered shape:", filtered_df.shape)
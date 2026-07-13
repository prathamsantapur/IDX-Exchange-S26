import os
import pandas as pd

reports_folder = "reports"

os.makedirs(reports_folder, exist_ok=True)

datasets = {
    "listings": "outputs/CRMLSListing_Combined_Residential.csv",
    "sold": "outputs/CRMLSSold_Combined_Residential.csv"
}

structure_rows = []

for dataset_name, path in datasets.items():
    df = pd.read_csv(path, low_memory=False)

    print(f"\nProcessing {dataset_name}...")
    print("Shape:", df.shape)

    structure_rows.append({
        "Dataset": dataset_name,
        "Rows": df.shape[0],
        "Columns": df.shape[1]
    })

    # Data type report
    dtype_report = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values
    })

    dtype_report.to_csv(
        f"reports/{dataset_name}_data_types.csv",
        index=False
    )

    # Missing value report
    missing_report = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": df.isnull().sum().values,
        "Missing Percent": (df.isnull().mean() * 100).values
    })

    missing_report = missing_report.sort_values(
        by="Missing Percent",
        ascending=False
    )

    missing_report.to_csv(
        f"reports/{dataset_name}_missing_report.csv",
        index=False
    )

    # Columns over 90% missing
    high_missing = missing_report[
        missing_report["Missing Percent"] > 90
    ]

    high_missing.to_csv(
        f"reports/{dataset_name}_high_missing_over_90_percent.csv",
        index=False
    )

    print(f"Saved reports for {dataset_name}")

structure_report = pd.DataFrame(structure_rows)

structure_report.to_csv(
    "reports/dataset_structure_summary.csv",
    index=False
)

print("\nSaved reports/dataset_structure_summary.csv")
print("Structure reports complete.")
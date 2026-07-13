import os
import pandas as pd
import matplotlib.pyplot as plt

reports_folder = "reports"
plots_folder = "plots"

os.makedirs(reports_folder, exist_ok=True)
os.makedirs(os.path.join(plots_folder, "listings"), exist_ok=True)
os.makedirs(os.path.join(plots_folder, "sold"), exist_ok=True)

listings = pd.read_csv(
    "outputs/CRMLSListing_Combined_Residential.csv",
    low_memory=False
)

sold = pd.read_csv(
    "outputs/CRMLSSold_Combined_Residential.csv",
    low_memory=False
)

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

def analyze_numeric_distributions(df, dataset_name):
    print(f"\nAnalyzing {dataset_name} numeric distributions...")

    available_fields = [
        col for col in numeric_fields
        if col in df.columns
    ]

    print("Available fields:")
    print(available_fields)

    summary = df[available_fields].describe(
        percentiles=[0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    ).T

    summary.index.name = "Column"

    summary_output_path = os.path.join(
        reports_folder,
        f"{dataset_name}_numeric_distribution_summary.csv"
    )

    summary.to_csv(summary_output_path)

    print(f"Saved {summary_output_path}")

    for col in available_fields:
        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if series.empty:
            print(f"Skipping {col}: no numeric data")
            continue

        # Raw histogram
        plt.figure()
        plt.hist(series, bins=50)
        plt.title(f"{dataset_name.title()} {col} Histogram - Raw")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                plots_folder,
                dataset_name,
                f"{col}_histogram_raw.png"
            )
        )
        plt.close()

        # Trimmed histogram using 1st to 99th percentile
        lower = series.quantile(0.01)
        upper = series.quantile(0.99)
        trimmed = series[
            (series >= lower) &
            (series <= upper)
        ]

        plt.figure()
        plt.hist(trimmed, bins=50)
        plt.title(f"{dataset_name.title()} {col} Histogram - 1st to 99th Percentile")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                plots_folder,
                dataset_name,
                f"{col}_histogram_trimmed.png"
            )
        )
        plt.close()

        # Raw boxplot
        plt.figure()
        plt.boxplot(series, vert=False)
        plt.title(f"{dataset_name.title()} {col} Boxplot - Raw")
        plt.xlabel(col)
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                plots_folder,
                dataset_name,
                f"{col}_boxplot_raw.png"
            )
        )
        plt.close()

    print(f"Saved plots for {dataset_name}.")

analyze_numeric_distributions(listings, "listings")
analyze_numeric_distributions(sold, "sold")

print("\nNumeric distribution review complete.")
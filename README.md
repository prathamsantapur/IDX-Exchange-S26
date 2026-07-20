# IDX Exchange MLS Analytics Internship

This repository contains Python scripts for the IDX Exchange Data Analyst Internship workflow.

Due to confidentiality requirements, raw MLS CSV files, generated output datasets, ZIP files, and detailed row-count validation outputs are excluded from this public repository.

## Week 1: Monthly Dataset Aggregation

The Week 1 script:
- Loads monthly CRMLS listing and sold CSV files from a local csv folder
- Separates listing files from sold files
- Concatenates monthly files into combined datasets
- Filters records to PropertyType == "Residential"
- Saves combined Residential datasets locally to an outputs folder

The Week 1 QC script:
- Checks monthly file counts
- Verifies output files exist
- Reviews input and output row counts
- Confirms the Residential filter worked
- Checks key columns, date ranges, nulls, and basic numeric sanity issues

Raw data and generated outputs are not included in this repository.

## Weeks 4–5: Data Cleaning and Preparation

The Week 4–5 workflow adds cleaning, validation, and geographic enrichment steps on top of the combined Residential MLS datasets.

### Scripts

- `scripts/week4_5_cleaning_preparation.py`
  - Loads the enriched Residential Sold and Listings datasets.
  - Converts major date fields into datetime format.
  - Creates year, month, quarter, and year-month helper fields.
  - Flags date consistency issues.
  - Converts key numeric fields into numeric helper columns.
  - Flags invalid values such as nonpositive prices, invalid living area, negative days on market, and unreasonable year built values.
  - Creates percentile-based outlier flags.
  - Validates Latitude and Longitude values.
  - Saves cleaned/prepared local datasets.

- `scripts/week4_5_school_district_mapping.py`
  - Loads the California School District Areas 2025–26 GeoJSON.
  - Filters district boundaries to `DistrictType = "Unified"`.
  - Converts property Latitude and Longitude into geographic points.
  - Performs a spatial join against Unified School District boundaries.
  - Adds matched Unified School District fields to the Sold and Listings datasets.
  - Saves local school-district-enriched outputs and mapping summary reports.

### Data Privacy

Raw MLS files, generated outputs, reports, plots, notes, and external GeoJSON files are intentionally excluded from GitHub through `.gitignore`.
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
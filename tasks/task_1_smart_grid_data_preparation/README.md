# Task 1 – Smart Grid Data Preparation & Energy Knowledge Base

## 1. Objective
The purpose of this task is to prepare the smart grid energy dataset for intelligent analytics by cleaning, validating, and structuring the data so it is suitable for analytics, anomaly detection, and forecasting.

The project uses the existing household electric power consumption dataset already available in the repository.

## 2. Dataset Used
The dataset used in this task is:

- `data/processed/household_power_consumption_cleaned.csv`
- copied into this task folder as: `task_1_smart_grid_data_preparation/dataset/household_power_consumption_cleaned.csv`

This dataset contains time-stamped household energy measurements including active power, reactive power, voltage, current intensity, and sub-meter readings.

The dataset-related artifacts for this submission are kept together under the `dataset/` folder in this task section.

## 3. Scope of the Task
The solution was designed to:

- process energy consumption records
- handle missing and inconsistent data
- convert and validate timestamps
- create relevant time-based features
- prepare the dataset for analytics and time-series analysis
- prepare the dataset for anomaly detection and forecasting
- maintain a clean structure for efficient querying and downstream use
- document preprocessing decisions and data-quality checks

## 4. Methodology
The data preparation workflow includes the following steps:

1. Load the existing dataset without modifying the source file.
2. Validate that all required energy columns exist.
3. Convert timestamp values into proper pandas datetime objects.
4. Remove invalid timestamps and sort the data chronologically.
5. Convert numeric columns to a consistent numeric type.
6. Generate time-based features such as hour, day of week, month, day of month, and weekend flag.
7. Create a prepared output CSV for downstream analysis.
8. Produce a data-quality summary for documentation and transparency.

## 5. Preprocessing Decisions
The following decisions were applied:

- The original source dataset was preserved and not overwritten.
- All timestamps were standardized to a valid datetime format.
- Data was sorted by time to ensure correct chronological sequence.
- Required columns were checked before processing.
- Missing values were identified and recorded in the quality report.
- Time-based features were added to support pattern analysis and forecasting.

## 6. Data Quality Summary
The generated quality summary shows the following results:

- Total rows processed: 2,075,259
- Duplicate timestamps: 0
- Invalid timestamps: 0
- Date range: 2006-12-16 17:24:00 to 2010-11-26 21:02:00
- Missing values across required columns: 0 after preparation

The dataset was successfully structured for subsequent analytics tasks.

## 7. Output Files in This Folder
- `prepare_energy_data.py` — dataset preparation script
- `prepared_energy_data.csv` — prepared task-ready dataset
- `data_quality_summary.json` — quality and preprocessing summary
- `dataset/household_power_consumption_cleaned.csv` — dataset copy for this task submission
- `dataset/data_quality_report.json` — processed dataset quality report for this task submission
- `dataset/README.md` — dataset reference note

## 8. Run Instructions
From the project root, run:

```bash
python tasks/task_1_smart_grid_data_preparation/prepare_energy_data.py
```

## 9. Result
This task successfully prepares the smart-grid energy dataset for downstream analysis and satisfies the required Task 1 scope: dataset processing, cleaning, validation, feature creation, and documentation for data quality.

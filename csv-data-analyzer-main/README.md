# CSV Data Analyzer

This is a CLI tool I made for my Python class to analyze student CSV data.

It takes a CSV file containing student marks, cleans up missing or bad rows, calculates basic stats like average and median, and prints out insights and grade distributions. You can also save the summary report to a text file.

## Requirements
You just need Python 3 and numpy:
```bash
pip install -r requirements.txt
```

## How to run
Run the main script from the project folder:
```bash
python src/analyzer.py
```
It loads `data/students_data.csv` by default and brings up a menu where you can pick what you want to check.

### Menu options
1. Show dataset info (columns and row count)
2. Preview first few rows
3. Numerical statistics (mean, median, std dev, min/max for scores, study hours, attendance)
4. Department & Grade breakdown (grades A to F, pass vs fail)
5. Key insights (highest/lowest scores, pass rates, attendance warnings)
6. Data cleaning summary (shows rows dropped because of duplicate IDs or negative marks)
7. Export report to file (saves to `output/analysis_report.txt`)
8. Exit

## Running the tests
I wrote unit tests using Python's built-in `unittest` module to make sure the math and cleaning logic work:
```bash
python -m unittest discover -s tests
```

## Project Structure
- `src/analyzer.py` - main code with data loading, cleaning and cli menu
- `data/students_data.csv` - sample dataset with some messy rows for testing
- `tests/test_analyzer.py` - unit tests for loading, math, and cleaning
- `output/` - folder where the exported text report gets saved

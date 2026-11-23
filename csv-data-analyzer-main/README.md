# CSV Data Analyzer

A command-line Python application to clean, analyze, and generate summary reports from student performance datasets. Built as a first-year programming mini-project using Python and NumPy.

---

## Overview

When dealing with student record exports, CSV files frequently contain missing values, duplicate entries, or out-of-range figures (like negative scores or attendance > 100%). 

This tool loads the raw dataset, filters out bad records with a logged audit trail, computes core statistics (mean, median, standard deviation, min, max), categorizes scores into letter grades, and lets you export a summary report to a text file.

---

## Features

- **Data Cleaning & Validation:** Detects missing fields, invalid ranges (`study_hours` 0–24, `attendance_pct` 0–100, `exam_score` 0–100), and duplicate student IDs.
- **Statistical Analysis:** Fast calculation of mean, median, min, max, sum, and standard deviation using NumPy (with a standard-library fallback).
- **Categorical Breakdowns:** Department-wise student counts and grade distribution (A/B/C/D/F).
- **Automated Insights:** Quick summary highlighting top scorers, students below 75% attendance, and pass/fail rates.
- **Export Reports:** Saves a formatted summary report to `output/analysis_report.txt`.
- **Menu-Driven CLI:** Interactive terminal interface with clear prompts and navigation.

---

## Project Structure

```text
csv-data-analyzer/
├── data/
│   └── students_data.csv          # Sample dataset with valid & invalid rows
├── src/
│   └── analyzer.py                # Main script (CLI, cleaning, stats, export)
├── output/
│   └── analysis_report.txt        # Generated export report
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py           # Unit tests
├── screenshots/
│   └── program_output.png         # Terminal screenshot
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.8 or higher
- NumPy (`pip install -r requirements.txt`)

### Installation

1. Clone or download the repository:
   ```bash
   git clone https://github.com/arhaansethi/csv-data-analyzer.git
   cd csv-data-analyzer
   ```

2. (Optional) Set up a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Run the analyzer from the project directory:

```bash
python src/analyzer.py
```

When prompted, you can press **Enter** to load the default sample dataset (`data/students_data.csv`), or provide the path to any other CSV file with the same schema.

### Main Menu Options:
1. View Dataset Overview & Column Schema
2. View Data Cleaning Audit & Removed Records
3. Numerical Statistics (Overall or by Column)
4. Department & Grade Distributions
5. View Key Insights
6. Export Summary Report to File
7. Reload / Load Another Dataset
8. Exit

---

## Running Tests

The project includes unit tests covering data loading, cleaning edge cases, numerical calculations, and report generation.

To run the test suite:

```bash
python -m unittest discover -s tests -v
```

---

## Dataset Format

If using your own CSV file, ensure the following columns are present in the header:

| Column | Type | Allowed Values |
|---|---|---|
| `student_id` | String | Unique student ID (e.g. S101) |
| `name` | String | Student name |
| `department` | String | Department or major |
| `study_hours` | Float | 0.0 to 24.0 |
| `attendance_pct`| Float | 0.0 to 100.0 |
| `exam_score` | Float | 0.0 to 100.0 |

---

## License

This project is licensed under the [MIT License](LICENSE).

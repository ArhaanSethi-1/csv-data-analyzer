# CSV Data Analyzer – Python Data Processing Mini Project

**Author:** Arhaan Sethi  
**Course/Degree:** B.Tech / B.Sc Computer Science (First Year Mini-Project)  
**Subject:** Programming in Python / Core Data Structures & Algorithms  
**License:** [MIT License](LICENSE)

---

## 1. Project Title
**CSV Data Analyzer** – An interactive, menu-driven Python application designed to inspect, clean, analyze, and summarize academic student performance records from CSV files using NumPy and Python's standard library.

---

## 2. Project Overview
In educational institutions, student academic records often arrive with inconsistencies—such as duplicate enrolment IDs, blank fields from missing test submissions, or erroneous negative scores. 

The **CSV Data Analyzer** serves as a robust data processing utility built specifically for academic environments. It reads raw student datasets, audits data hygiene by identifying and filtering anomalous entries without modifying the source CSV, computes descriptive numerical statistics, computes categorical frequency tables (departments, grades, pass/fail status), generates rule-based academic insights, and exports an audit-ready analysis report to text.

---

## 3. Objectives
- **Data Hygiene:** Implement defensive data ingestion and validation rules to handle missing, invalid, or duplicate records safely.
- **Statistical Computation:** Use NumPy array operations (with pure Python fallback) to compute core descriptive metrics (Mean, Median, Minimum, Maximum, Population Standard Deviation, Sum, and Count).
- **Categorical Exploration:** Group and analyze frequency distributions across academic departments and letter grades.
- **Academic Insight Generation:** Provide educators with actionable insights (e.g., identifying high achievers, flagging low-attendance students) while respecting data science integrity (not claiming causal links from simple correlation).
- **Reproducible Reporting:** Enable users to export clean, formatted analysis summaries directly to `output/analysis_report.txt`.

---

## 4. Key Features
- **Defensive File Ingestion:** Validates file paths, detects empty 0-byte files, confirms mandatory header columns, and handles encoding errors gracefully.
- **Four-Stage Data Cleaning Audit:**
  - Detects and rejects blank/missing values across required columns.
  - Enforces biological and academic ranges (`study_hours` $\in [0, 24]$, `attendance_pct` $\in [0, 100]$, `exam_score` $\in [0, 100]$).
  - Enforces unique primary keys (`student_id`), retaining the first valid occurrence.
  - Logs exact line numbers and exclusion reasons for an audit trail.
- **NumPy Numerical Analysis:** Fast calculation of mean, median, min, max, sum, and population standard deviation ($ddof=0$).
- **Dynamic Column Selection:** Interactive sub-menu allows analyzing individual numerical columns or viewing a consolidated comparative table.
- **Frequency & Academic Grading:** Automated categorization into Grade A (85–100), Grade B (70–84), Grade C (55–69), Grade D (40–54), and Grade F (<40).
- **Pattern-Based Academic Insights:** Identifies top performers, lowest performers, attendance risks (<75%), and performance correlations without false causal claims.
- **One-Click Text Report Export:** Creates an audit report in `output/analysis_report.txt` while keeping the original CSV intact.
- **Automated Unit Testing:** Includes 16 unit tests using Python's built-in `unittest` module.

---

## 5. Technologies Used
- **Programming Language:** Python 3.10+
- **Numerical Processing:** [NumPy](https://numpy.org/) (`numpy>=1.20.0,<3.0.0`) for vectorized statistical calculations.
- **Standard Library Modules:**
  - `csv`: Reading tabular CSV files via `csv.DictReader`.
  - `os`: File path verification, directory creation, and size auditing.
  - `tempfile` & `shutil`: Creating clean mock fixtures for automated testing.
  - `unittest`: Executing comprehensive unit test cases.

---

## 6. Project Directory Structure
```text
csv data analyzer/
│
├── data/
│   └── students_data.csv          # Sample dataset with valid, missing, duplicate, and invalid rows
│
├── src/
│   └── analyzer.py                # Main application code (loading, cleaning, stats, CLI, export)
│
├── output/
│   └── analysis_report.txt        # Generated analysis summary report (created upon export)
│
├── tests/
│   ├── __init__.py                # Package initialization for test discovery
│   └── test_analyzer.py           # 16 unit tests covering loading, cleaning, stats, and export
│
├── screenshots/
│   ├── README.md                  # Instructions for capturing program terminal screenshots
│   └── program_output.png         # Terminal execution screenshot
│
├── README.md                      # Comprehensive project documentation
├── requirements.txt               # External Python package specifications
├── .gitignore                     # Git exclusion rules (virtual environments, cache, OS files)
└── LICENSE                        # MIT License
```

---

## 7. Dataset Description
The sample dataset is stored in `data/students_data.csv`. It represents an undergraduate batch across multiple engineering branches.

### Schema:
| Column Name | Data Type | Description | Permitted Range |
| :--- | :--- | :--- | :--- |
| `student_id` | String | Unique identifier for each student (e.g., `S101`) | Non-empty, unique |
| `name` | String | Full name of the student | Non-empty string |
| `department` | String | Academic engineering department | Non-empty string |
| `study_hours`| Float | Self-reported daily study hours | $0.0 \le \text{hours} \le 24.0$ |
| `attendance_pct` | Float | Attendance percentage throughout semester | $0.0 \le \text{attendance} \le 100.0$ |
| `exam_score` | Float | Score obtained in the final assessment | $0.0 \le \text{score} \le 100.0$ |

### Dataset Composition:
- **Total raw rows:** 24 data rows (+ 1 header row)
- **Valid clean records:** 20 records
- **Excluded records:** 4 records:
  - `Line 22 (S104)`: Duplicate student ID (first valid entry kept from Line 5).
  - `Line 23 (S121)`: Missing `study_hours` field.
  - `Line 24 (S122)`: Invalid boundary (`exam_score` = `-15.0`).
  - `Line 25 (S123)`: Missing `attendance_pct` field.

---

## 8. Explanation of Data-Cleaning Methods
Data cleaning runs before any calculation to guarantee that corrupted data does not skew statistical outputs:

1. **Completeness Check:** Each row is inspected across all mandatory columns (`REQUIRED_COLUMNS`). If any field is `None`, empty, or only whitespace, the record is flagged as missing and skipped.
2. **Type Casting & Range Verification:** Values are converted from strings to `float`. A `try-except ValueError` catches non-numeric garbage data. Next, biological/logical bounds are checked:
   - Study hours cannot exceed 24 hours per day or be negative.
   - Attendance and scores cannot be negative or exceed 100%.
3. **Duplicate Identification Policy:** We maintain a set of observed student IDs (`seen_student_ids`). If an ID is already in the set, the duplicate entry is rejected. The earliest valid entry is preserved.
4. **Audit Trail Logging:** All rejected rows are recorded in a `removed_records` list with their exact CSV line number, student ID, and specific rejection reason.

---

## 9. Explanation of Statistical Calculations
Statistical functions operate on the cleaned dataset. When NumPy is installed, computations use optimized C-level vectorized arrays:

- **Count ($N$):** Total number of valid student observations ($N = 20$).
- **Mean ($\mu$):** The arithmetic average:
  $$\mu = \frac{1}{N} \sum_{i=1}^{N} x_i$$
- **Median:** The middle value of the sorted observations (average of two central elements when $N$ is even).
- **Minimum & Maximum:** Boundary values $\min(X)$ and $\max(X)$.
- **Standard Deviation ($\sigma$):**
  Calculated using **Population Standard Deviation** ($ddof = 0$ in NumPy):
  $$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2}$$
  *Convention note:* Because the dataset represents the complete roster of evaluated students rather than an inferred subset, population standard deviation is mathematically appropriate.
- **Sum:** The total aggregated points or hours across the batch.

All outputs are rounded consistently to **2 decimal places**.

---

## 10. Explanation of Program Workflow
```text
[Start Program]
       │
       ▼
[Load CSV File] ──(Missing/Corrupt?)──► [Display Error & Terminate]
       │
       ▼
[Data Cleaning Pipeline]
   ├── Filter missing values
   ├── Validate numerical ranges
   └── Drop duplicate IDs (keeping 1st)
       │
       ▼
[Interactive Menu (CLI)] ◄────────────────────────┐
   ├── 1. Display Dataset Information             │
   ├── 2. Display Cleaned Sample Records          │
   ├── 3. View Numerical Statistics (Dynamic)     │
   ├── 4. View Frequency Distributions            │
   ├── 5. Generate Automatic Insights             │
   ├── 6. Display Cleaning Audit Summary          │
   ├── 7. Export Report (output/analysis_report)  │
   └── 8. Exit Program ──────────────────┐        │
                                         ▼        │
                                     [Shutdown]   │
                                                  │
                       (User selects 1-7) ────────┘
```

---

## 11. Installation Instructions

### Prerequisites
- Python 3.10 or higher installed.
- (Optional but recommended) `pip` package manager.

### Step 1: Clone or Download the Repository
```bash
git clone https://github.com/<your-username>/csv-data-analyzer.git
cd "csv data analyzer"
```

### Step 2: (Recommended) Create and Activate a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 12. Execution Instructions
Run the main script from the root of the project directory:

```bash
python src/analyzer.py
```

Follow the on-screen numbered menu to navigate between statistics, frequency tables, data cleaning audits, and report generation.

---

## 13. Example Terminal Output

### Main Menu
```text
================================================
           CSV DATA ANALYZER - MAIN MENU
================================================
1. Display Dataset Information
2. Display Cleaned Sample Records
3. View Numerical Statistics
4. View Categorical Frequency Distributions
5. Generate Automatic Insights
6. Display Data-Cleaning Summary
7. Export Analysis Report
8. Exit
================================================
Enter your choice (1-8):
```

### Option 3 (Consolidated Numerical Statistics):
```text
======================================================================
              CONSOLIDATED NUMERICAL SUMMARY
======================================================================
Metric             | Exam Score     | Study Hours    | Attendance %  
----------------------------------------------------------------------
Count (N)          | 20             | 20             | 20            
Mean (Average)     | 71.6           | 3.48           | 76.6          
Median             | 74.0           | 3.35           | 78.25         
Minimum            | 40.0           | 1.0            | 50.0          
Maximum            | 94.0           | 6.0            | 95.0          
Std Deviation      | 15.59          | 1.36           | 12.83         
Sum / Total        | 1432.0         | 69.6           | 1532.0        
======================================================================
```

### Option 6 (Data-Cleaning Summary):
```text
=======================================================
               DATA CLEANING SUMMARY
=======================================================
Original Records in CSV    : 24
Clean Records Retained     : 20
Total Records Removed      : 4
-------------------------------------------------------
Breakdown of Removed Records:
  • Duplicate Student IDs  : 1
  • Missing / Blank Values : 2
  • Invalid / Out of Range : 1
-------------------------------------------------------
Detailed Log of Excluded Rows:
  [CSV Line 22] ID: S104   -> Duplicate student ID 'S104' (first valid entry already kept)
  [CSV Line 23] ID: S121   -> Missing value in column(s): study_hours
  [CSV Line 24] ID: S122   -> Boundary violation: exam_score (-15.0) out of range [0, 100]
  [CSV Line 25] ID: S123   -> Missing value in column(s): attendance_pct
=======================================================
```

---

## 14. Example Generated Report
Exported to `output/analysis_report.txt`:

```text
================================================================================
                CSV DATA ANALYZER - ACADEMIC ANALYSIS REPORT
================================================================================
Project Name     : CSV Data Analyzer (Python Mini Project)
Student / Author : Arhaan Sethi
Dataset Analyzed : students_data.csv
Computation Mode : NumPy Vectorized
================================================================================

1. DATA CLEANING AUDIT
--------------------------------------------------------------------------------
Total Raw Records       : 24
Clean Records Retained  : 20
Total Records Excluded  : 4
  - Duplicate Records   : 1
  - Missing Data Rows   : 2
  - Invalid / Out-Range : 1

Excluded Records Detail:
  * [CSV Line 22] ID: S104 -> Duplicate student ID 'S104' (first valid entry already kept)
  * [CSV Line 23] ID: S121 -> Missing value in column(s): study_hours
  * [CSV Line 24] ID: S122 -> Boundary violation: exam_score (-15.0) out of range [0, 100]
  * [CSV Line 25] ID: S123 -> Missing value in column(s): attendance_pct
--------------------------------------------------------------------------------

2. NUMERICAL DESCRIPTIVE STATISTICS
--------------------------------------------------------------------------------
Column: Final Exam Score (0-100)
  Count (N)         : 20
  Mean (Average)    : 71.6
  Median            : 74.0
  Minimum           : 40.0
  Maximum           : 94.0
  Std Deviation     : 15.59 (Population std dev, ddof=0)
  Total / Sum       : 1432.0

Column: Daily Study Hours (0-24)
  Count (N)         : 20
  Mean (Average)    : 3.48
  Median            : 3.35
  Minimum           : 1.0
  Maximum           : 6.0
  Std Deviation     : 1.36 (Population std dev, ddof=0)
  Total / Sum       : 69.6

Column: Attendance Percentage (0-100)
  Count (N)         : 20
  Mean (Average)    : 76.6
  Median            : 78.25
  Minimum           : 50.0
  Maximum           : 95.0
  Std Deviation     : 12.83 (Population std dev, ddof=0)
  Total / Sum       : 1532.0
--------------------------------------------------------------------------------

3. CATEGORICAL FREQUENCY DISTRIBUTIONS
--------------------------------------------------------------------------------
A. Department Enrollment Distribution:
   - Computer Science          :  5 students ( 25.0%)
   - Information Technology    :  4 students ( 20.0%)
   - Mechanical                :  4 students ( 20.0%)
   - Electrical                :  4 students ( 20.0%)
   - Civil                     :  3 students ( 15.0%)

B. Academic Grade Distribution:
   - Grade A (85-100)          :  5 students ( 25.0%)
   - Grade B (70-84)           :  7 students ( 35.0%)
   - Grade C (55-69)           :  4 students ( 20.0%)
   - Grade D (40-54)           :  4 students ( 20.0%)
   - Grade F (<40)             :  0 students (  0.0%)

C. Pass / Fail Status (Threshold >= 40):
   - Passed                    : 20 students (100.0%)
   - Failed                    :  0 students (  0.0%)
--------------------------------------------------------------------------------

4. AUTOMATED ACADEMIC INSIGHTS & OBSERVATIONS
--------------------------------------------------------------------------------
1. Cohort Performance: The batch has an overall pass rate of 100.0% (20 passed, 0 failed out of 20 students).
2. Average Benchmark: Class average exam score is 71.6 (median: 74.0), with an average attendance of 76.6% and 3.48 daily study hours.
3. Highest Scorer: Tanvi Deshmukh (S109) from Computer Science achieved the top score of 94.0.
4. Lowest Scorer: Sneha Roy (S113) from Information Technology scored 40.0.
5. Distinction Achievers: 5 student(s) achieved distinction marks (85% and above).
6. Attendance Vigilance: 8 student(s) are currently below the standard 75% college attendance requirement.
7. Academic Intervention: 3 student(s) require proactive mentorship due to low scores (<50) or critical attendance (<60%).
8. Study Pattern Observation: Students studying 4.0 or more hours/day recorded an average score of 86.62, compared to 61.58 for those studying under 4.0 hours. (Note: Represents observed correlation within this cohort; does not imply single-factor causation).
--------------------------------------------------------------------------------
End of Analysis Report. Generated by CSV Data Analyzer.
================================================================================
```

---

## 15. Testing Instructions
The project includes a comprehensive test suite in `tests/test_analyzer.py` built using Python's standard `unittest` module.

### How to Run the Unit Tests:
```bash
# Run test suite directly
python -m unittest tests/test_analyzer.py

# Or run with test discovery
python -m unittest discover tests
```

### Verified Test Cases:
1. `test_load_dataset_success`: Confirms valid CSV loading.
2. `test_load_dataset_missing_file`: Confirms handling of non-existent paths.
3. `test_load_dataset_empty_file`: Confirms handling of 0-byte files.
4. `test_load_dataset_headers_only`: Confirms behavior with headers but no data.
5. `test_load_dataset_missing_required_headers`: Confirms rejection of invalid schemas.
6. `test_clean_dataset_duplicate_ids`: Validates duplicate student ID rejection.
7. `test_clean_dataset_missing_values`: Validates detection of empty cells.
8. `test_clean_dataset_invalid_and_out_of_range`: Validates boundary and type checks.
9. `test_clean_dataset_empty_input`: Ensures empty datasets do not cause crashes.
10. `test_calculate_numeric_stats_accuracy`: Verifies mean, median, min, max, total, and population standard deviation ($ddof=0$).
11. `test_calculate_numeric_stats_empty_column`: Confirms empty columns return `None` safely.
12. `test_calculate_frequency`: Verifies department count dictionary accuracy.
13. `test_calculate_grade_distribution`: Tests grade categorization bands.
14. `test_calculate_pass_fail_distribution`: Validates passing threshold logic.
15. `test_generate_insights`: Validates automated observation generation.
16. `test_export_analysis_report`: Confirms report creation on disk.

---

## 16. Current Limitations
- **Fixed Schema Expectation:** The application expects the student academic columns (`student_id`, `name`, `department`, `study_hours`, `attendance_pct`, `exam_score`). Arbitrary CSV datasets with completely different schemas are detected and rejected.
- **In-Memory Processing:** Loads all rows into memory; ideal for small-to-medium datasets (thousands of rows) but not meant for multi-gigabyte big data files.
- **Terminal UI Only:** Provides a CLI menu without a graphical user interface (GUI) or web interface.

---

## 17. Future Improvements
- **Graphical Visualization:** Integrate Matplotlib or Seaborn to export attendance vs. score scatter plots and department bar charts.
- **Dynamic Schema Mapping:** Allow users to map arbitrary column names to analytical roles during ingestion.
- **CSV Export:** Add an option to export the cleaned records back into a new cleaned CSV file.
- **Web Dashboard:** Build a lightweight Streamlit or Flask interface for browser-based interaction.

---

## 18. Credits and AI Assistance Disclosure
- **Student Author:** Arhaan Sethi
- **Mentorship & Code Review:** Guidance provided on clean modular architecture, defensive input validation, statistical standard deviation conventions, and unit test structuring.
- **Generative AI Disclosure:** Generative AI was utilized as a pair-programming and mentorship assistant for code structuring, debugging edge cases, and drafting comprehensive unit tests and academic documentation. All logic and mathematical calculations were independently reviewed, executed, and verified.

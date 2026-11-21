"""
=============================================================================
CSV Data Analyzer - Python Data Processing Mini Project
=============================================================================
Author: Arhaan Sethi
Subject: Programming in Python / Data Handling Mini-Project
Description:
    A modular, beginner-friendly command-line Python application that loads
    student academic records from a CSV file, performs rigorous data cleaning,
    calculates descriptive numerical statistics using NumPy, performs categorical
    frequency distributions, generates automated academic insights, and exports
    a structured summary report to text.
=============================================================================
"""

import csv
import os

# Check if NumPy is available in the user environment.
# If NumPy is installed, we leverage its fast array operations for statistics.
# If not yet installed, a standard-library fallback prevents immediate crashes.
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# List of mandatory columns expected in the student CSV dataset
REQUIRED_COLUMNS = [
    'student_id',
    'name',
    'department',
    'study_hours',
    'attendance_pct',
    'exam_score'
]


# =============================================================================
# 1. CSV LOADING MODULE
# =============================================================================

def validate_csv_path(file_path):
    """
    Validates whether the provided path is a non-empty string and points
    to an existing file on disk.
    """
    if not file_path or not isinstance(file_path, str):
        print("[Error] File path must be a valid, non-empty string.")
        return False

    if not os.path.exists(file_path):
        print(f"[Error] The file path '{file_path}' does not exist.")
        return False

    if not os.path.isfile(file_path):
        print(f"[Error] The path '{file_path}' is a directory, not a file.")
        return False

    return True


def load_dataset(file_path):
    """
    Reads a CSV dataset from disk using Python's built-in csv.DictReader.
    
    Performs checks for:
    - Path existence and validity
    - Empty file detection
    - Presence of all required column headers
    - File encoding and formatting errors
    
    Returns:
        tuple: (headers_list, raw_rows_list) on success, or (None, None) on failure.
    """
    if not validate_csv_path(file_path):
        return None, None

    rows = []
    headers = []

    try:
        # Check if the file is completely empty (0 bytes)
        if os.path.getsize(file_path) == 0:
            print(f"[Error] The file '{file_path}' is completely empty (0 bytes).")
            return None, None

        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames

            # Handle case where file has no header row
            if not headers:
                print(f"[Error] Unable to read column headers from '{file_path}'.")
                return None, None

            # Verify that all mandatory columns exist in the header
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
            if missing_cols:
                print(f"[Error] CSV is missing required column(s): {', '.join(missing_cols)}")
                return None, None

            # Read all rows into memory
            for row_idx, row in enumerate(reader, start=2):
                # Ensure the row has content and is not just a blank line
                if any(value.strip() for value in row.values() if value is not None):
                    rows.append(row)

        if not rows:
            print(f"[Warning] CSV file '{file_path}' contains headers but has no data rows.")
            return headers, []

        print(f"-> Successfully loaded {len(rows)} raw rows from '{os.path.basename(file_path)}'.")
        return headers, rows

    except UnicodeDecodeError:
        print(f"[Error] Encoding issue: '{file_path}' could not be decoded as UTF-8.")
        return None, None
    except csv.Error as csv_err:
        print(f"[Error] Malformed CSV structure encountered: {csv_err}")
        return None, None
    except OSError as os_err:
        print(f"[Error] System I/O error reading file: {os_err}")
        return None, None


# =============================================================================
# 2. DATA CLEANING MODULE
# =============================================================================

def clean_dataset(raw_rows):
    """
    Performs systematic data cleaning on raw CSV rows without modifying
    the original data.
    
    Data Cleaning Rules:
    1. Check for missing / empty fields across all required columns.
    2. Validate numeric formats and logical ranges:
       - study_hours: float between 0.0 and 24.0
       - attendance_pct: float between 0.0 and 100.0
       - exam_score: float between 0.0 and 100.0
    3. Duplicate Policy: Keep the first valid record encountered for any student_id.
       Subsequent records with the same student_id are rejected as duplicates.
    4. Track counts and reasons for all rejected records.

    Returns:
        tuple: (cleaned_rows, cleaning_summary_dict)
    """
    if not raw_rows:
        empty_summary = {
            'raw_count': 0,
            'clean_count': 0,
            'duplicate_count': 0,
            'missing_count': 0,
            'invalid_count': 0,
            'removed_records': []
        }
        return [], empty_summary

    cleaned_rows = []
    seen_student_ids = set()
    removed_records = []

    duplicate_count = 0
    missing_count = 0
    invalid_count = 0

    for index, row in enumerate(raw_rows, start=2):
        raw_id = row.get('student_id', '').strip()

        # Step 1: Check for blank or missing values in any required field
        missing_fields = []
        for col in REQUIRED_COLUMNS:
            val = row.get(col)
            if val is None or str(val).strip() == '':
                missing_fields.append(col)

        if missing_fields:
            missing_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id if raw_id else 'UNKNOWN',
                'reason': f"Missing value in column(s): {', '.join(missing_fields)}"
            })
            continue

        # Step 2: Validate numerical types and acceptable boundary ranges
        try:
            study_hours = float(row['study_hours'])
            attendance = float(row['attendance_pct'])
            exam_score = float(row['exam_score'])
        except ValueError:
            invalid_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id,
                'reason': "Non-numeric value in numerical column(s)"
            })
            continue

        # Check biological / academic ranges
        range_errors = []
        if not (0.0 <= study_hours <= 24.0):
            range_errors.append(f"study_hours ({study_hours}) out of range [0, 24]")
        if not (0.0 <= attendance <= 100.0):
            range_errors.append(f"attendance_pct ({attendance}) out of range [0, 100]")
        if not (0.0 <= exam_score <= 100.0):
            range_errors.append(f"exam_score ({exam_score}) out of range [0, 100]")

        if range_errors:
            invalid_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id,
                'reason': f"Boundary violation: {'; '.join(range_errors)}"
            })
            continue

        # Step 3: Check for duplicate student ID (first valid record is retained)
        if raw_id in seen_student_ids:
            duplicate_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id,
                'reason': f"Duplicate student ID '{raw_id}' (first valid entry already kept)"
            })
            continue

        # Record is valid; register its ID and create a clean typed record
        seen_student_ids.add(raw_id)
        cleaned_row = {
            'student_id': raw_id,
            'name': str(row['name']).strip(),
            'department': str(row['department']).strip(),
            'study_hours': round(study_hours, 2),
            'attendance_pct': round(attendance, 2),
            'exam_score': round(exam_score, 2)
        }
        cleaned_rows.append(cleaned_row)

    summary = {
        'raw_count': len(raw_rows),
        'clean_count': len(cleaned_rows),
        'duplicate_count': duplicate_count,
        'missing_count': missing_count,
        'invalid_count': invalid_count,
        'removed_records': removed_records
    }

    return cleaned_rows, summary


# =============================================================================
# 3. NUMERICAL ANALYSIS MODULE (Using NumPy with Fallback)
# =============================================================================

def extract_numeric_column(data, column_name):
    """
    Extracts all numerical values from a specified column into a Python list of floats.
    """
    values = []
    for row in data:
        if column_name in row:
            val = row[column_name]
            if val is not None and isinstance(val, (int, float)):
                values.append(float(val))
    return values


def calculate_numeric_stats(data, column_name):
    """
    Calculates summary statistics for a given numerical column.
    
    Metrics:
    - Count (N)
    - Mean (Average)
    - Median (Middle value)
    - Minimum
    - Maximum
    - Standard Deviation (Population standard deviation, ddof=0)
    - Sum (Total)
    
    Standard Deviation Convention:
        Calculated as population standard deviation (ddof=0 in NumPy),
        which represents the parameter spread across all students in the batch.
    
    Returns:
        dict: Statistical summary with consistently rounded floats (2 decimals),
              or None if data is empty.
    """
    values = extract_numeric_column(data, column_name)
    if not values:
        return None

    if HAS_NUMPY:
        np_arr = np.array(values, dtype=float)
        stats = {
            'column': column_name,
            'count': int(len(np_arr)),
            'mean': round(float(np.mean(np_arr)), 2),
            'median': round(float(np.median(np_arr)), 2),
            'min': round(float(np.min(np_arr)), 2),
            'max': round(float(np.max(np_arr)), 2),
            'std_dev': round(float(np.std(np_arr, ddof=0)), 2),
            'total': round(float(np.sum(np_arr)), 2)
        }
    else:
        # Standard Python calculation fallback
        n = len(values)
        total_val = sum(values)
        mean_val = total_val / n

        sorted_vals = sorted(values)
        if n % 2 == 1:
            median_val = sorted_vals[n // 2]
        else:
            mid = n // 2
            median_val = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0

        min_val = min(values)
        max_val = max(values)

        # Population variance and standard deviation (ddof=0)
        variance = sum((x - mean_val) ** 2 for x in values) / n
        std_dev = variance ** 0.5

        stats = {
            'column': column_name,
            'count': n,
            'mean': round(mean_val, 2),
            'median': round(median_val, 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'std_dev': round(std_dev, 2),
            'total': round(total_val, 2)
        }

    return stats


def get_all_numeric_columns():
    """
    Returns list of numeric column keys available in the student dataset.
    """
    return ['study_hours', 'attendance_pct', 'exam_score']


# =============================================================================
# 4. CATEGORICAL & FREQUENCY ANALYSIS MODULE
# =============================================================================

def calculate_frequency(data, column_name):
    """
    Counts frequency distribution of categorical values using a standard dictionary.
    """
    freq_dict = {}
    for row in data:
        val = row.get(column_name, 'Unknown')
        freq_dict[val] = freq_dict.get(val, 0) + 1
    return freq_dict


def calculate_grade_distribution(data):
    """
    Categorizes student marks into standard academic grade bands:
    - Grade A (85 - 100): Outstanding / Distinction
    - Grade B (70 - 84): First Class
    - Grade C (55 - 69): Second Class
    - Grade D (40 - 54): Pass Class
    - Grade F (< 40): Fail
    """
    grades = {
        'Grade A (85-100)': 0,
        'Grade B (70-84)': 0,
        'Grade C (55-69)': 0,
        'Grade D (40-54)': 0,
        'Grade F (<40)': 0
    }

    for row in data:
        score = row.get('exam_score', 0)
        if score >= 85:
            grades['Grade A (85-100)'] += 1
        elif score >= 70:
            grades['Grade B (70-84)'] += 1
        elif score >= 55:
            grades['Grade C (55-69)'] += 1
        elif score >= 40:
            grades['Grade D (40-54)'] += 1
        else:
            grades['Grade F (<40)'] += 1

    return grades


def calculate_pass_fail_distribution(data, passing_mark=40.0):
    """
    Determines how many students passed versus failed based on the passing threshold.
    """
    distribution = {'Passed': 0, 'Failed': 0}
    for row in data:
        score = row.get('exam_score', 0)
        if score >= passing_mark:
            distribution['Passed'] += 1
        else:
            distribution['Failed'] += 1
    return distribution


# =============================================================================
# 5. AUTOMATIC INSIGHTS MODULE
# =============================================================================

def generate_insights(data):
    """
    Generates meaningful, pattern-based observations from the cleaned dataset.
    
    Academic Safety Principle:
    Does NOT claim direct causation between variables (e.g. study hours causing marks).
    Only describes observed statistical distributions, correlations, and performance benchmarks.
    
    Returns:
        list of str: Clean, readable insight statements.
    """
    if not data:
        return ["No data available to generate insights."]

    total_students = len(data)

    # 1. Top and Lowest Scoring Students (using simple readable loops, no lambdas)
    top_student = data[0]
    lowest_student = data[0]

    for student in data[1:]:
        if student['exam_score'] > top_student['exam_score']:
            top_student = student
        if student['exam_score'] < lowest_student['exam_score']:
            lowest_student = student

    # 2. Performance & Pass Rates
    pass_counts = calculate_pass_fail_distribution(data, passing_mark=40.0)
    passed_count = pass_counts['Passed']
    failed_count = pass_counts['Failed']
    pass_rate = round((passed_count / total_students) * 100, 2)

    # 3. High Achievers (score >= 85)
    high_achievers = [s for s in data if s['exam_score'] >= 85.0]

    # 4. Students Needing Academic Support (marks < 50 or attendance < 60%)
    attention_students = [
        s for s in data if (s['exam_score'] < 50.0 or s['attendance_pct'] < 60.0)
    ]

    # 5. Attendance Benchmark (College 75% requirement)
    low_attendance_students = [s for s in data if s['attendance_pct'] < 75.0]

    # 6. Study Hour & Score Pattern (Associative comparison, not causal claim)
    high_study_group = [s['exam_score'] for s in data if s['study_hours'] >= 4.0]
    regular_study_group = [s['exam_score'] for s in data if s['study_hours'] < 4.0]

    avg_high_study = round(sum(high_study_group) / len(high_study_group), 2) if high_study_group else 0.0
    avg_regular_study = round(sum(regular_study_group) / len(regular_study_group), 2) if regular_study_group else 0.0

    # Summary Statistics
    score_stats = calculate_numeric_stats(data, 'exam_score')
    att_stats = calculate_numeric_stats(data, 'attendance_pct')
    study_stats = calculate_numeric_stats(data, 'study_hours')

    insights = [
        f"1. Cohort Performance: The batch has an overall pass rate of {pass_rate}% ({passed_count} passed, {failed_count} failed out of {total_students} students).",
        f"2. Average Benchmark: Class average exam score is {score_stats['mean']} (median: {score_stats['median']}), with an average attendance of {att_stats['mean']}% and {study_stats['mean']} daily study hours.",
        f"3. Highest Scorer: {top_student['name']} ({top_student['student_id']}) from {top_student['department']} achieved the top score of {top_student['exam_score']}.",
        f"4. Lowest Scorer: {lowest_student['name']} ({lowest_student['student_id']}) from {lowest_student['department']} scored {lowest_student['exam_score']}.",
        f"5. Distinction Achievers: {len(high_achievers)} student(s) achieved distinction marks (85% and above).",
        f"6. Attendance Vigilance: {len(low_attendance_students)} student(s) are currently below the standard 75% college attendance requirement.",
        f"7. Academic Intervention: {len(attention_students)} student(s) require proactive mentorship due to low scores (<50) or critical attendance (<60%).",
        f"8. Study Pattern Observation: Students studying 4.0 or more hours/day recorded an average score of {avg_high_study}, compared to {avg_regular_study} for those studying under 4.0 hours. (Note: Represents observed correlation within this cohort; does not imply single-factor causation)."
    ]

    return insights


# =============================================================================
# 6. DISPLAY & FORMATTING FUNCTIONS
# =============================================================================

def display_dataset_info(file_path, headers, raw_count, clean_count):
    """
    Displays metadata and structure of the loaded dataset.
    """
    print("\n" + "=" * 50)
    print("              DATASET INFORMATION")
    print("=" * 50)
    print(f"File Source      : {file_path}")
    print(f"Engine           : {'NumPy (Accelerated)' if HAS_NUMPY else 'Python Standard Library'}")
    print(f"Raw Records      : {raw_count}")
    print(f"Clean Records    : {clean_count}")
    print(f"Removed Records  : {raw_count - clean_count}")
    print("\nDetected Columns & Schema:")
    print("-" * 50)
    print(f"{'Column Name':<20} | {'Expected Type':<15} | {'Category'}")
    print("-" * 50)
    type_map = {
        'student_id': ('String', 'Identifier'),
        'name': ('String', 'Personal Info'),
        'department': ('String', 'Categorical'),
        'study_hours': ('Float', 'Numerical'),
        'attendance_pct': ('Float', 'Numerical'),
        'exam_score': ('Float', 'Numerical')
    }
    for col in headers:
        t_info = type_map.get(col, ('String', 'General'))
        print(f"{col:<20} | {t_info[0]:<15} | {t_info[1]}")
    print("=" * 50)


def display_sample_data(data, count=5):
    """
    Displays the first N records in an aligned tabular view.
    """
    if not data:
        print("\n[Notice] No cleaned records available to display.")
        return

    display_count = min(count, len(data))
    print(f"\n--- Cleaned Sample Records (Showing {display_count} of {len(data)}) ---")
    print("-" * 75)
    print(f"{'ID':<6} {'Name':<18} {'Department':<22} {'Hours':<7} {'Att %':<7} {'Score':<6}")
    print("-" * 75)
    for row in data[:display_count]:
        print(f"{row['student_id']:<6} {row['name']:<18} {row['department']:<22} {row['study_hours']:<7.1f} {row['attendance_pct']:<7.1f} {row['exam_score']:<6.1f}")
    print("-" * 75)


def display_stats(stats, title):
    """
    Prints the calculated statistics for a single numerical column.
    """
    if not stats:
        print(f"\n[Notice] No numerical data available for {title}.")
        return

    print("\n" + "=" * 45)
    print(f"  STATISTICAL SUMMARY: {title.upper()}")
    print("=" * 45)
    print(f"Count (N)          : {stats['count']}")
    print(f"Mean (Average)     : {stats['mean']}")
    print(f"Median             : {stats['median']}")
    print(f"Minimum            : {stats['min']}")
    print(f"Maximum            : {stats['max']}")
    print(f"Std Deviation      : {stats['std_dev']} (ddof=0, population)")
    print(f"Sum / Total        : {stats['total']}")
    print("=" * 45)


def display_all_numeric_stats(data):
    """
    Displays a consolidated comparative summary for all numerical columns.
    """
    columns = [
        ('exam_score', 'Exam Score'),
        ('study_hours', 'Daily Study Hours'),
        ('attendance_pct', 'Attendance %')
    ]

    print("\n" + "=" * 70)
    print("              CONSOLIDATED NUMERICAL SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<18} | {'Exam Score':<14} | {'Study Hours':<14} | {'Attendance %':<14}")
    print("-" * 70)

    stats_map = {}
    for col_key, _ in columns:
        stats_map[col_key] = calculate_numeric_stats(data, col_key)

    metrics = [
        ('Count (N)', 'count'),
        ('Mean (Average)', 'mean'),
        ('Median', 'median'),
        ('Minimum', 'min'),
        ('Maximum', 'max'),
        ('Std Deviation', 'std_dev'),
        ('Sum / Total', 'total')
    ]

    for label, key in metrics:
        v1 = stats_map['exam_score'][key] if stats_map['exam_score'] else 'N/A'
        v2 = stats_map['study_hours'][key] if stats_map['study_hours'] else 'N/A'
        v3 = stats_map['attendance_pct'][key] if stats_map['attendance_pct'] else 'N/A'
        print(f"{label:<18} | {str(v1):<14} | {str(v2):<14} | {str(v3):<14}")
    print("=" * 70)


def display_frequency_table(freq_dict, category_name):
    """
    Prints a clean two-column table displaying counts and percentages.
    """
    total = sum(freq_dict.values())
    print("\n" + "=" * 45)
    print(f"  FREQUENCY DISTRIBUTION: {category_name.upper()}")
    print("=" * 45)
    print(f"{'Category':<26} | {'Count':<6} | {'Share %'}")
    print("-" * 45)
    for cat, count in freq_dict.items():
        pct = round((count / total) * 100, 1) if total > 0 else 0.0
        print(f"{cat:<26} | {count:<6} | {pct:>5.1f}%")
    print("-" * 45)
    print(f"{'Total':<26} | {total:<6} | 100.0%")
    print("=" * 45)


def display_cleaning_summary(summary):
    """
    Displays the complete audit report of data cleaning.
    """
    print("\n" + "=" * 55)
    print("               DATA CLEANING SUMMARY")
    print("=" * 55)
    print(f"Original Records in CSV    : {summary['raw_count']}")
    print(f"Clean Records Retained     : {summary['clean_count']}")
    total_removed = summary['raw_count'] - summary['clean_count']
    print(f"Total Records Removed      : {total_removed}")
    print("-" * 55)
    print("Breakdown of Removed Records:")
    print(f"  • Duplicate Student IDs  : {summary['duplicate_count']}")
    print(f"  • Missing / Blank Values : {summary['missing_count']}")
    print(f"  • Invalid / Out of Range : {summary['invalid_count']}")
    print("-" * 55)

    if summary['removed_records']:
        print("Detailed Log of Excluded Rows:")
        for item in summary['removed_records']:
            print(f"  [CSV Line {item['csv_line']}] ID: {item['student_id']:<6} -> {item['reason']}")
    else:
        print("  All rows were clean. No records were excluded.")
    print("=" * 55)


# =============================================================================
# 7. REPORT EXPORT MODULE
# =============================================================================

def export_analysis_report(file_path, cleaned_data, raw_data_count, cleaning_summary, output_path):
    """
    Generates a comprehensive text analysis report and writes it to disk.
    
    Ensures:
    - Output directory is automatically created if missing.
    - Original CSV dataset is completely untouched.
    - Full reproducibility with clear sections.
    
    Returns:
        bool: True on success, False on failure.
    """
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        lines = []
        lines.append("================================================================================")
        lines.append("                CSV DATA ANALYZER - ACADEMIC ANALYSIS REPORT")
        lines.append("================================================================================")
        lines.append(f"Project Name     : CSV Data Analyzer (Python Mini Project)")
        lines.append(f"Student / Author : Arhaan Sethi")
        lines.append(f"Dataset Analyzed : {os.path.basename(file_path)}")
        lines.append(f"Computation Mode : {'NumPy Vectorized' if HAS_NUMPY else 'Python Standard Library'}")
        lines.append("================================================================================\n")

        # Section 1: Data Cleaning Audit
        lines.append("1. DATA CLEANING AUDIT")
        lines.append("--------------------------------------------------------------------------------")
        lines.append(f"Total Raw Records       : {raw_data_count}")
        lines.append(f"Clean Records Retained  : {cleaning_summary['clean_count']}")
        lines.append(f"Total Records Excluded  : {raw_data_count - cleaning_summary['clean_count']}")
        lines.append(f"  - Duplicate Records   : {cleaning_summary['duplicate_count']}")
        lines.append(f"  - Missing Data Rows   : {cleaning_summary['missing_count']}")
        lines.append(f"  - Invalid / Out-Range : {cleaning_summary['invalid_count']}")
        lines.append("\nExcluded Records Detail:")
        if cleaning_summary['removed_records']:
            for item in cleaning_summary['removed_records']:
                lines.append(f"  * [CSV Line {item['csv_line']}] ID: {item['student_id']} -> {item['reason']}")
        else:
            lines.append("  * None. Dataset had zero invalid rows.")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 2: Numerical Statistics
        lines.append("2. NUMERICAL DESCRIPTIVE STATISTICS")
        lines.append("--------------------------------------------------------------------------------")
        cols_to_report = [
            ('exam_score', 'Final Exam Score (0-100)'),
            ('study_hours', 'Daily Study Hours (0-24)'),
            ('attendance_pct', 'Attendance Percentage (0-100)')
        ]
        for col_key, col_title in cols_to_report:
            st = calculate_numeric_stats(cleaned_data, col_key)
            if st:
                lines.append(f"Column: {col_title}")
                lines.append(f"  Count (N)         : {st['count']}")
                lines.append(f"  Mean (Average)    : {st['mean']}")
                lines.append(f"  Median            : {st['median']}")
                lines.append(f"  Minimum           : {st['min']}")
                lines.append(f"  Maximum           : {st['max']}")
                lines.append(f"  Std Deviation     : {st['std_dev']} (Population std dev, ddof=0)")
                lines.append(f"  Total / Sum       : {st['total']}")
                lines.append("")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 3: Frequency Distributions
        lines.append("3. CATEGORICAL FREQUENCY DISTRIBUTIONS")
        lines.append("--------------------------------------------------------------------------------")

        dept_freq = calculate_frequency(cleaned_data, 'department')
        lines.append("A. Department Enrollment Distribution:")
        for dept, cnt in dept_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {dept:<25} : {cnt:>2} students ({pct:>5.1f}%)")

        grade_freq = calculate_grade_distribution(cleaned_data)
        lines.append("\nB. Academic Grade Distribution:")
        for grd, cnt in grade_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {grd:<25} : {cnt:>2} students ({pct:>5.1f}%)")

        pass_freq = calculate_pass_fail_distribution(cleaned_data)
        lines.append("\nC. Pass / Fail Status (Threshold >= 40):")
        for st_name, cnt in pass_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {st_name:<25} : {cnt:>2} students ({pct:>5.1f}%)")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 4: Automated Insights
        lines.append("4. AUTOMATED ACADEMIC INSIGHTS & OBSERVATIONS")
        lines.append("--------------------------------------------------------------------------------")
        insights = generate_insights(cleaned_data)
        for ins in insights:
            lines.append(f"{ins}")
        lines.append("--------------------------------------------------------------------------------")
        lines.append("End of Analysis Report. Generated by CSV Data Analyzer.")
        lines.append("================================================================================")

        with open(output_path, mode='w', encoding='utf-8') as out_file:
            out_file.write("\n".join(lines) + "\n")

        print(f"\n[Success] Full report exported successfully to: '{output_path}'")
        return True

    except Exception as e:
        print(f"\n[Error] Failed to export analysis report: {e}")
        return False


# =============================================================================
# 8. INTERACTIVE COMMAND-LINE INTERFACE (CLI)
# =============================================================================

def handle_numeric_stats_menu(cleaned_data):
    """
    Sub-menu allowing the user to dynamically select which numerical column to analyze.
    """
    while True:
        print("\n--- Numerical Statistics Selection ---")
        print("1. Final Exam Score (exam_score)")
        print("2. Daily Study Hours (study_hours)")
        print("3. Attendance Percentage (attendance_pct)")
        print("4. View All Numerical Columns Consolidated")
        print("5. Return to Main Menu")
        print("---------------------------------------")

        sub_choice = input("Select a numerical column option (1-5): ").strip()

        if sub_choice == '1':
            st = calculate_numeric_stats(cleaned_data, 'exam_score')
            display_stats(st, "Final Exam Score")
        elif sub_choice == '2':
            st = calculate_numeric_stats(cleaned_data, 'study_hours')
            display_stats(st, "Daily Study Hours")
        elif sub_choice == '3':
            st = calculate_numeric_stats(cleaned_data, 'attendance_pct')
            display_stats(st, "Attendance Percentage")
        elif sub_choice == '4':
            display_all_numeric_stats(cleaned_data)
        elif sub_choice == '5':
            break
        else:
            print("[Warning] Invalid selection. Please enter a number from 1 to 5.")


def handle_frequency_menu(cleaned_data):
    """
    Sub-menu allowing the user to select specific frequency distributions.
    """
    while True:
        print("\n--- Categorical Frequency Selection ---")
        print("1. Department Distribution")
        print("2. Academic Grade Distribution (A / B / C / D / F)")
        print("3. Pass / Fail Status")
        print("4. Display All Distributions")
        print("5. Return to Main Menu")
        print("---------------------------------------")

        sub_choice = input("Select a frequency option (1-5): ").strip()

        if sub_choice == '1':
            freq = calculate_frequency(cleaned_data, 'department')
            display_frequency_table(freq, "Department Distribution")
        elif sub_choice == '2':
            grades = calculate_grade_distribution(cleaned_data)
            display_frequency_table(grades, "Grade Distribution")
        elif sub_choice == '3':
            pf = calculate_pass_fail_distribution(cleaned_data)
            display_frequency_table(pf, "Pass / Fail Distribution")
        elif sub_choice == '4':
            freq = calculate_frequency(cleaned_data, 'department')
            display_frequency_table(freq, "Department Distribution")
            grades = calculate_grade_distribution(cleaned_data)
            display_frequency_table(grades, "Grade Distribution")
            pf = calculate_pass_fail_distribution(cleaned_data)
            display_frequency_table(pf, "Pass / Fail Distribution")
        elif sub_choice == '5':
            break
        else:
            print("[Warning] Invalid selection. Please enter a number from 1 to 5.")


def run_cli(cleaned_data, raw_data, headers, file_path, cleaning_summary):
    """
    Main interactive menu loop running the 8 specified student project options.
    """
    # Output report default path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_report_path = os.path.join(project_root, 'output', 'analysis_report.txt')

    while True:
        print("\n" + "=" * 48)
        print("           CSV DATA ANALYZER - MAIN MENU")
        print("=" * 48)
        print("1. Display Dataset Information")
        print("2. Display Cleaned Sample Records")
        print("3. View Numerical Statistics")
        print("4. View Categorical Frequency Distributions")
        print("5. Generate Automatic Insights")
        print("6. Display Data-Cleaning Summary")
        print("7. Export Analysis Report")
        print("8. Exit")
        print("=" * 48)

        choice = input("Enter your choice (1-8): ").strip()

        if choice == '1':
            display_dataset_info(file_path, headers, len(raw_data), len(cleaned_data))

        elif choice == '2':
            user_n = input("How many sample rows to display? (Press Enter for 5): ").strip()
            count = 5
            if user_n.isdigit() and int(user_n) > 0:
                count = int(user_n)
            display_sample_data(cleaned_data, count=count)

        elif choice == '3':
            handle_numeric_stats_menu(cleaned_data)

        elif choice == '4':
            handle_frequency_menu(cleaned_data)

        elif choice == '5':
            print("\n" + "=" * 55)
            print("          AUTOMATED ACADEMIC OBSERVATIONS")
            print("=" * 55)
            insights = generate_insights(cleaned_data)
            for item in insights:
                print(f"\n{item}")
            print("\n" + "=" * 55)

        elif choice == '6':
            display_cleaning_summary(cleaning_summary)

        elif choice == '7':
            export_analysis_report(
                file_path=file_path,
                cleaned_data=cleaned_data,
                raw_data_count=len(raw_data),
                cleaning_summary=cleaning_summary,
                output_path=default_report_path
            )

        elif choice == '8':
            print("\nThank you for using CSV Data Analyzer.")
            print("Shutting down... Goodbye!\n")
            break

        else:
            print("[Warning] Invalid selection! Please enter a number between 1 and 8.")


# =============================================================================
# 9. MAIN PROGRAM ENTRY POINT
# =============================================================================

def main():
    """
    Main driver function to locate files, coordinate pipeline steps,
    and launch the interactive CLI.
    """
    print("=" * 50)
    print("    CSV Data Analyzer - Python Mini Project")
    print("=" * 50)

    # Resolve project root and CSV location safely
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_csv = os.path.join(project_root, 'data', 'students_data.csv')

    print(f"\n[Info] Loading default dataset: {default_csv}")
    headers, raw_data = load_dataset(default_csv)

    if raw_data is None:
        print("[Fatal] Could not load dataset. Terminating program.")
        return

    # Clean the dataset and obtain cleaning audit
    cleaned_data, cleaning_summary = clean_dataset(raw_data)

    if not cleaned_data:
        print("[Fatal] No valid records remained after cleaning. Terminating program.")
        return

    print(f"[Info] Ready. {len(cleaned_data)} clean records available for analysis.")

    # Start the CLI
    run_cli(cleaned_data, raw_data, headers, default_csv, cleaning_summary)


if __name__ == '__main__':
    main()

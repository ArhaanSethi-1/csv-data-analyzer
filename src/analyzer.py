"""
CSV Data Analyzer
Author: Arhaan Sethi

A command-line tool to load, clean, and analyze student academic data from CSV files.
"""

import csv
import os

# Use numpy for numerical operations if available, otherwise use pure Python fallback
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

REQUIRED_COLUMNS = [
    'student_id',
    'name',
    'department',
    'study_hours',
    'attendance_pct',
    'exam_score'
]


# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------

def validate_csv_path(file_path):
    """Check if the provided path is a non-empty string pointing to an existing file."""
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
    Reads a CSV dataset from disk using csv.DictReader.
    Validates file existence, empty file status, and required column headers.
    """
    if not validate_csv_path(file_path):
        return None, None

    rows = []
    headers = []

    try:
        if os.path.getsize(file_path) == 0:
            print(f"[Error] The file '{file_path}' is completely empty (0 bytes).")
            return None, None

        with open(file_path, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames

            if not headers:
                print(f"[Error] Unable to read column headers from '{file_path}'.")
                return None, None

            missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
            if missing_cols:
                print(f"[Error] CSV is missing required column(s): {', '.join(missing_cols)}")
                return None, None

            for row in reader:
                # skip empty lines
                if any(val.strip() for val in row.values() if val is not None):
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


# -----------------------------------------------------------------------------
# Data Cleaning & Validation
# -----------------------------------------------------------------------------

def clean_dataset(raw_rows):
    """
    Cleans raw student records:
    - Filters out rows with missing required columns.
    - Validates numeric bounds: study_hours [0, 24], attendance_pct [0, 100], exam_score [0, 100].
    - Filters duplicate student_ids (keeps first occurrence).
    Returns (cleaned_rows, summary_dict).
    """
    if not raw_rows:
        return [], {
            'raw_count': 0,
            'clean_count': 0,
            'duplicate_count': 0,
            'missing_count': 0,
            'invalid_count': 0,
            'removed_records': []
        }

    cleaned_rows = []
    seen_student_ids = set()
    removed_records = []

    duplicate_count = 0
    missing_count = 0
    invalid_count = 0

    for index, row in enumerate(raw_rows, start=2):
        raw_id = row.get('student_id', '').strip()

        # Check for empty/missing values in required columns
        missing_fields = [
            col for col in REQUIRED_COLUMNS
            if row.get(col) is None or str(row.get(col)).strip() == ''
        ]
        if missing_fields:
            missing_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id if raw_id else 'UNKNOWN',
                'reason': f"Missing value in column(s): {', '.join(missing_fields)}"
            })
            continue

        # Parse numerical values
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

        # Range checks
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

        # Check for duplicates (keep first valid)
        if raw_id in seen_student_ids:
            duplicate_count += 1
            removed_records.append({
                'csv_line': index,
                'student_id': raw_id,
                'reason': f"Duplicate student ID '{raw_id}' (first valid entry already kept)"
            })
            continue

        seen_student_ids.add(raw_id)
        cleaned_rows.append({
            'student_id': raw_id,
            'name': str(row['name']).strip(),
            'department': str(row['department']).strip(),
            'study_hours': round(study_hours, 2),
            'attendance_pct': round(attendance, 2),
            'exam_score': round(exam_score, 2)
        })

    summary = {
        'raw_count': len(raw_rows),
        'clean_count': len(cleaned_rows),
        'duplicate_count': duplicate_count,
        'missing_count': missing_count,
        'invalid_count': invalid_count,
        'removed_records': removed_records
    }
    return cleaned_rows, summary


# -----------------------------------------------------------------------------
# Statistical Analysis
# -----------------------------------------------------------------------------

def extract_numeric_column(data, column_name):
    """Extract numeric values from a column into a list of floats."""
    values = []
    for row in data:
        if column_name in row and row[column_name] is not None:
            try:
                values.append(float(row[column_name]))
            except (ValueError, TypeError):
                pass
    return values


def calculate_numeric_stats(data, column_name):
    """
    Calculate summary statistics for a numerical column:
    count, mean, median, min, max, population std dev (ddof=0), and total sum.
    """
    values = extract_numeric_column(data, column_name)
    if not values:
        return None

    if HAS_NUMPY:
        arr = np.array(values, dtype=float)
        return {
            'column': column_name,
            'count': int(len(arr)),
            'mean': round(float(np.mean(arr)), 2),
            'median': round(float(np.median(arr)), 2),
            'min': round(float(np.min(arr)), 2),
            'max': round(float(np.max(arr)), 2),
            'std_dev': round(float(np.std(arr, ddof=0)), 2),
            'total': round(float(np.sum(arr)), 2)
        }

    # Pure Python fallback
    n = len(values)
    total_val = sum(values)
    mean_val = total_val / n

    sorted_vals = sorted(values)
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        mid = n // 2
        median_val = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0

    variance = sum((x - mean_val) ** 2 for x in values) / n
    std_dev = variance ** 0.5

    return {
        'column': column_name,
        'count': n,
        'mean': round(mean_val, 2),
        'median': round(median_val, 2),
        'min': round(min(values), 2),
        'max': round(max(values), 2),
        'std_dev': round(std_dev, 2),
        'total': round(total_val, 2)
    }


def get_all_numeric_columns():
    return ['study_hours', 'attendance_pct', 'exam_score']


# -----------------------------------------------------------------------------
# Categorical Distributions
# -----------------------------------------------------------------------------

def calculate_frequency(data, column_name):
    """Count frequency of categorical values."""
    freq = {}
    for row in data:
        val = row.get(column_name, 'Unknown')
        freq[val] = freq.get(val, 0) + 1
    return freq


def calculate_grade_distribution(data):
    """Assign letter grades according to exam score brackets."""
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
    """Count students passing or failing based on passing_mark."""
    dist = {'Passed': 0, 'Failed': 0}
    for row in data:
        score = row.get('exam_score', 0)
        if score >= passing_mark:
            dist['Passed'] += 1
        else:
            dist['Failed'] += 1
    return dist


# -----------------------------------------------------------------------------
# Automated Insights
# -----------------------------------------------------------------------------

def generate_insights(data):
    """Generate high-level observations and performance benchmarks from the dataset."""
    if not data:
        return ["No data available to generate insights."]

    total_students = len(data)

    top_student = max(data, key=lambda s: s['exam_score'])
    lowest_student = min(data, key=lambda s: s['exam_score'])

    pass_counts = calculate_pass_fail_distribution(data, passing_mark=40.0)
    passed_count = pass_counts['Passed']
    failed_count = pass_counts['Failed']
    pass_rate = round((passed_count / total_students) * 100, 2)

    high_achievers = [s for s in data if s['exam_score'] >= 85.0]
    attention_students = [
        s for s in data if (s['exam_score'] < 50.0 or s['attendance_pct'] < 60.0)
    ]
    low_attendance_students = [s for s in data if s['attendance_pct'] < 75.0]

    high_study_scores = [s['exam_score'] for s in data if s['study_hours'] >= 4.0]
    regular_study_scores = [s['exam_score'] for s in data if s['study_hours'] < 4.0]

    avg_high_study = round(sum(high_study_scores) / len(high_study_scores), 2) if high_study_scores else 0.0
    avg_regular_study = round(sum(regular_study_scores) / len(regular_study_scores), 2) if regular_study_scores else 0.0

    score_stats = calculate_numeric_stats(data, 'exam_score')
    att_stats = calculate_numeric_stats(data, 'attendance_pct')
    study_stats = calculate_numeric_stats(data, 'study_hours')

    return [
        f"1. Overall Pass Rate: {pass_rate}% ({passed_count} passed, {failed_count} failed out of {total_students} students).",
        f"2. Cohort Averages: Mean exam score is {score_stats['mean']} (median: {score_stats['median']}), average attendance is {att_stats['mean']}%, and average daily study hours is {study_stats['mean']}.",
        f"3. Top Scorer: {top_student['name']} ({top_student['student_id']}) from {top_student['department']} achieved the highest score of {top_student['exam_score']}.",
        f"4. Lowest Scorer: {lowest_student['name']} ({lowest_student['student_id']}) from {lowest_student['department']} scored {lowest_student['exam_score']}.",
        f"5. Distinction: {len(high_achievers)} student(s) achieved distinction (score >= 85).",
        f"6. Attendance Flag: {len(low_attendance_students)} student(s) have attendance below the 75% threshold.",
        f"7. Academic Support: {len(attention_students)} student(s) have low exam scores (<50) or critical attendance (<60%).",
        f"8. Study Hours: Students studying 4+ hours/day averaged {avg_high_study} on exams, vs {avg_regular_study} for students studying under 4 hours."
    ]


# -----------------------------------------------------------------------------
# Terminal Display Functions
# -----------------------------------------------------------------------------

def display_dataset_info(file_path, headers, raw_count, clean_count):
    """Displays dataset summary and column schema."""
    print("\n" + "=" * 50)
    print("              DATASET INFORMATION")
    print("=" * 50)
    print(f"File Source      : {file_path}")
    print(f"Engine           : {'NumPy' if HAS_NUMPY else 'Python Standard Library'}")
    print(f"Raw Records      : {raw_count}")
    print(f"Clean Records    : {clean_count}")
    print(f"Removed Records  : {raw_count - clean_count}")
    print("\nColumns:")
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
    """Displays the first N records in a formatted table."""
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
    """Prints statistics for a single numerical column."""
    if not stats:
        print(f"\n[Notice] No numerical data available for {title}.")
        return

    print("\n" + "=" * 45)
    print(f"  STATISTICAL SUMMARY: {title.upper()}")
    print("=" * 45)
    print(f"Count (N)          : {stats['count']}")
    print(f"Mean               : {stats['mean']}")
    print(f"Median             : {stats['median']}")
    print(f"Minimum            : {stats['min']}")
    print(f"Maximum            : {stats['max']}")
    print(f"Std Deviation      : {stats['std_dev']} (ddof=0)")
    print(f"Total Sum          : {stats['total']}")
    print("=" * 45)


def display_all_numeric_stats(data):
    """Displays a side-by-side comparison of all numerical columns."""
    columns = [
        ('exam_score', 'Exam Score'),
        ('study_hours', 'Study Hours'),
        ('attendance_pct', 'Attendance %')
    ]

    print("\n" + "=" * 70)
    print("              CONSOLIDATED NUMERICAL SUMMARY")
    print("=" * 70)
    print(f"{'Metric':<18} | {'Exam Score':<14} | {'Study Hours':<14} | {'Attendance %':<14}")
    print("-" * 70)

    stats_map = {col_key: calculate_numeric_stats(data, col_key) for col_key, _ in columns}

    metrics = [
        ('Count (N)', 'count'),
        ('Mean', 'mean'),
        ('Median', 'median'),
        ('Minimum', 'min'),
        ('Maximum', 'max'),
        ('Std Deviation', 'std_dev'),
        ('Sum', 'total')
    ]

    for label, key in metrics:
        v1 = stats_map['exam_score'][key] if stats_map['exam_score'] else 'N/A'
        v2 = stats_map['study_hours'][key] if stats_map['study_hours'] else 'N/A'
        v3 = stats_map['attendance_pct'][key] if stats_map['attendance_pct'] else 'N/A'
        print(f"{label:<18} | {str(v1):<14} | {str(v2):<14} | {str(v3):<14}")
    print("=" * 70)


def display_frequency_table(freq_dict, category_name):
    """Prints counts and percentage shares for a category."""
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
    """Displays data cleaning metrics and excluded row details."""
    print("\n" + "=" * 55)
    print("               DATA CLEANING SUMMARY")
    print("=" * 55)
    print(f"Original Records in CSV    : {summary['raw_count']}")
    print(f"Clean Records Retained     : {summary['clean_count']}")
    total_removed = summary['raw_count'] - summary['clean_count']
    print(f"Total Records Removed      : {total_removed}")
    print("-" * 55)
    print("Breakdown of Removed Records:")
    print(f"  - Duplicate Student IDs  : {summary['duplicate_count']}")
    print(f"  - Missing / Blank Values : {summary['missing_count']}")
    print(f"  - Invalid / Out of Range : {summary['invalid_count']}")
    print("-" * 55)

    if summary['removed_records']:
        print("Details of Excluded Rows:")
        for item in summary['removed_records']:
            print(f"  [Line {item['csv_line']}] ID: {item['student_id']:<6} -> {item['reason']}")
    else:
        print("  All rows were valid. No records were excluded.")
    print("=" * 55)


# -----------------------------------------------------------------------------
# Report Export
# -----------------------------------------------------------------------------

def export_analysis_report(file_path, cleaned_data, raw_data_count, cleaning_summary, output_path):
    """Writes a formatted text summary report to the output path."""
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        lines = []
        lines.append("================================================================================")
        lines.append("                CSV DATA ANALYZER - ACADEMIC ANALYSIS REPORT")
        lines.append("================================================================================")
        lines.append("Project Name     : CSV Data Analyzer")
        lines.append("Author           : Arhaan Sethi")
        lines.append(f"Source Dataset   : {os.path.basename(file_path)}")
        lines.append(f"Engine           : {'NumPy' if HAS_NUMPY else 'Python Standard Library'}")
        lines.append("================================================================================\n")

        # Section 1
        lines.append("1. DATA CLEANING AUDIT")
        lines.append("--------------------------------------------------------------------------------")
        lines.append(f"Raw Records Read        : {raw_data_count}")
        lines.append(f"Clean Records Retained  : {cleaning_summary['clean_count']}")
        lines.append(f"Total Records Excluded  : {raw_data_count - cleaning_summary['clean_count']}")
        lines.append(f"  - Duplicate IDs       : {cleaning_summary['duplicate_count']}")
        lines.append(f"  - Missing Values      : {cleaning_summary['missing_count']}")
        lines.append(f"  - Invalid / Out-Range : {cleaning_summary['invalid_count']}")
        lines.append("\nExcluded Records Detail:")
        if cleaning_summary['removed_records']:
            for item in cleaning_summary['removed_records']:
                lines.append(f"  * [CSV Line {item['csv_line']}] ID: {item['student_id']} -> {item['reason']}")
        else:
            lines.append("  * None. Dataset had zero invalid rows.")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 2
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
                lines.append(f"  Mean              : {st['mean']}")
                lines.append(f"  Median            : {st['median']}")
                lines.append(f"  Minimum           : {st['min']}")
                lines.append(f"  Maximum           : {st['max']}")
                lines.append(f"  Std Deviation     : {st['std_dev']} (ddof=0)")
                lines.append(f"  Total / Sum       : {st['total']}")
                lines.append("")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 3
        lines.append("3. CATEGORICAL FREQUENCY DISTRIBUTIONS")
        lines.append("--------------------------------------------------------------------------------")

        dept_freq = calculate_frequency(cleaned_data, 'department')
        lines.append("A. Department Distribution:")
        for dept, cnt in dept_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {dept:<25} : {cnt:>2} students ({pct:>5.1f}%)")

        grade_freq = calculate_grade_distribution(cleaned_data)
        lines.append("\nB. Grade Distribution:")
        for grd, cnt in grade_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {grd:<25} : {cnt:>2} students ({pct:>5.1f}%)")

        pass_freq = calculate_pass_fail_distribution(cleaned_data)
        lines.append("\nC. Pass / Fail Status (Threshold >= 40):")
        for st_name, cnt in pass_freq.items():
            pct = round((cnt / len(cleaned_data)) * 100, 1)
            lines.append(f"   - {st_name:<25} : {cnt:>2} students ({pct:>5.1f}%)")
        lines.append("--------------------------------------------------------------------------------\n")

        # Section 4
        lines.append("4. AUTOMATED ACADEMIC INSIGHTS")
        lines.append("--------------------------------------------------------------------------------")
        insights = generate_insights(cleaned_data)
        for ins in insights:
            lines.append(f"{ins}")
        lines.append("--------------------------------------------------------------------------------")
        lines.append("End of Analysis Report.")
        lines.append("================================================================================")

        with open(output_path, mode='w', encoding='utf-8') as out_file:
            out_file.write("\n".join(lines) + "\n")

        print(f"\n[Success] Full report exported successfully to: '{output_path}'")
        return True

    except Exception as e:
        print(f"\n[Error] Failed to export analysis report: {e}")
        return False


# -----------------------------------------------------------------------------
# Menus and CLI Loop
# -----------------------------------------------------------------------------

def handle_numeric_stats_menu(cleaned_data):
    """Sub-menu to select numerical column statistics."""
    while True:
        print("\n--- Numerical Statistics Selection ---")
        print("1. Final Exam Score (exam_score)")
        print("2. Daily Study Hours (study_hours)")
        print("3. Attendance Percentage (attendance_pct)")
        print("4. View All Numerical Columns Consolidated")
        print("5. Return to Main Menu")
        print("---------------------------------------")

        sub_choice = input("Select an option (1-5): ").strip()

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
    """Sub-menu to select frequency distributions."""
    while True:
        print("\n--- Categorical Distributions ---")
        print("1. Department Distribution")
        print("2. Grade Distribution (A / B / C / D / F)")
        print("3. Pass / Fail Status")
        print("4. Display All")
        print("5. Return to Main Menu")
        print("---------------------------------")

        sub_choice = input("Select an option (1-5): ").strip()

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
    """Main interactive menu loop."""
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
        print("5. Generate Key Insights")
        print("6. Display Data-Cleaning Summary")
        print("7. Export Analysis Report")
        print("8. Exit")
        print("=" * 48)

        choice = input("Enter your choice (1-8): ").strip()

        if choice == '1':
            display_dataset_info(file_path, headers, len(raw_data), len(cleaned_data))

        elif choice == '2':
            user_n = input("How many sample rows to display? (Press Enter for 5): ").strip()
            count = int(user_n) if user_n.isdigit() and int(user_n) > 0 else 5
            display_sample_data(cleaned_data, count=count)

        elif choice == '3':
            handle_numeric_stats_menu(cleaned_data)

        elif choice == '4':
            handle_frequency_menu(cleaned_data)

        elif choice == '5':
            print("\n" + "=" * 55)
            print("                 KEY INSIGHTS")
            print("=" * 55)
            for item in generate_insights(cleaned_data):
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
            print("\nExiting CSV Data Analyzer. Goodbye!\n")
            break

        else:
            print("[Warning] Invalid selection! Please enter a number between 1 and 8.")


def main():
    """Program entry point."""
    print("=" * 50)
    print("    CSV Data Analyzer - Python Mini Project")
    print("=" * 50)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_csv = os.path.join(project_root, 'data', 'students_data.csv')

    print(f"\nLoading dataset: {default_csv}")
    headers, raw_data = load_dataset(default_csv)

    if raw_data is None:
        print("[Error] Could not load dataset. Exiting.")
        return

    cleaned_data, cleaning_summary = clean_dataset(raw_data)

    if not cleaned_data:
        print("[Error] No valid records remained after cleaning. Exiting.")
        return

    print(f"[Info] Ready. {len(cleaned_data)} valid records available.")
    run_cli(cleaned_data, raw_data, headers, default_csv, cleaning_summary)


if __name__ == '__main__':
    main()

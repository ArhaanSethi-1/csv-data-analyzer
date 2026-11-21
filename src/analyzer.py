"""
CSV Data Analyzer - Python Mini Project
Author: College Student
Description: A simple command-line tool to load, clean, analyze,
and summarize student performance data from a CSV file.
"""

import csv
import os

# Check if numpy is installed; if not, provide simple fallback calculations
# so the script runs smoothly anywhere.
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False



def load_dataset(file_path):
    """
    Reads a CSV file using python's built-in csv module.
    Returns the column headers and a list of rows as dictionaries.
    """
    if not os.path.exists(file_path):
        print(f"[Error] The file '{file_path}' was not found.")
        return None, None

    rows = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            for row in reader:
                rows.append(row)
        print(f"-> Successfully loaded {len(rows)} raw rows from '{file_path}'.")
        return headers, rows
    except Exception as e:
        print(f"[Error] Failed to read CSV file: {e}")
        return None, None


def clean_dataset(raw_rows):
    """
    Cleans the dataset by:
    1. Skipping duplicate student IDs.
    2. Skipping rows with empty values.
    3. Checking value boundaries (e.g., exam_score must be between 0 and 100).
    4. Converting numerical string columns to floats/integers.
    """
    cleaned_rows = []
    seen_ids = set()
    skipped_duplicates = 0
    skipped_missing = 0
    skipped_invalid = 0

    for row in raw_rows:
        student_id = row.get('student_id', '').strip()

        # Check for duplicates using student_id
        if student_id in seen_ids:
            skipped_duplicates += 1
            continue

        # Check for empty cells in required columns
        has_empty_field = False
        for key in ['student_id', 'name', 'department', 'study_hours', 'attendance_pct', 'exam_score']:
            if not row.get(key) or row.get(key).strip() == '':
                has_empty_field = True
                break

        if has_empty_field:
            skipped_missing += 1
            continue

        # Type conversion and boundary checks
        try:
            study_hours = float(row['study_hours'])
            attendance = float(row['attendance_pct'])
            exam_score = float(row['exam_score'])

            # Logical validation
            if study_hours < 0 or study_hours > 24:
                skipped_invalid += 1
                continue
            if attendance < 0 or attendance > 100:
                skipped_invalid += 1
                continue
            if exam_score < 0 or exam_score > 100:
                skipped_invalid += 1
                continue

            cleaned_row = {
                'student_id': student_id,
                'name': row['name'].strip(),
                'department': row['department'].strip(),
                'study_hours': study_hours,
                'attendance_pct': attendance,
                'exam_score': exam_score
            }

            seen_ids.add(student_id)
            cleaned_rows.append(cleaned_row)

        except ValueError:
            # If conversion to float fails
            skipped_invalid += 1
            continue

    print("\n--- Cleaning Summary ---")
    print(f"Total raw rows: {len(raw_rows)}")
    print(f"Skipped duplicate records: {skipped_duplicates}")
    print(f"Skipped rows with missing values: {skipped_missing}")
    print(f"Skipped invalid/out-of-range rows: {skipped_invalid}")
    print(f"Total clean rows retained: {len(cleaned_rows)}")
    print("------------------------\n")

    return cleaned_rows


def extract_numeric_column(data, column_name):
    """
    Helper function to pull all values of a numeric column into a Python list.
    """
    values = []
    for row in data:
        if column_name in row:
            values.append(row[column_name])
    return values


def calculate_numeric_stats(data, column_name):
    """
    Calculates summary statistics using NumPy (or pure Python if NumPy is not yet installed):
    - Mean
    - Median
    - Minimum & Maximum
    - Standard Deviation
    - Total / Sum
    """
    values = extract_numeric_column(data, column_name)
    if not values:
        print(f"No numeric data available for column '{column_name}'.")
        return None

    if HAS_NUMPY:
        np_values = np.array(values)
        stats = {
            'count': len(np_values),
            'mean': round(float(np.mean(np_values)), 2),
            'median': round(float(np.median(np_values)), 2),
            'min': round(float(np.min(np_values)), 2),
            'max': round(float(np.max(np_values)), 2),
            'std_dev': round(float(np.std(np_values)), 2),
            'total': round(float(np.sum(np_values)), 2)
        }
    else:
        # Fallback using standard Python math
        n = len(values)
        total_val = sum(values)
        mean_val = total_val / n
        sorted_vals = sorted(values)
        if n % 2 == 1:
            median_val = sorted_vals[n // 2]
        else:
            median_val = (sorted_vals[(n // 2) - 1] + sorted_vals[n // 2]) / 2.0
        min_val = min(values)
        max_val = max(values)
        variance = sum((x - mean_val) ** 2 for x in values) / n
        std_val = variance ** 0.5

        stats = {
            'count': n,
            'mean': round(mean_val, 2),
            'median': round(median_val, 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'std_dev': round(std_val, 2),
            'total': round(total_val, 2)
        }

    return stats


def calculate_frequency(data, column_name):
    """
    Counts frequency distribution of categorical values using a standard dictionary and loop.
    """
    freq_dict = {}
    for row in data:
        val = row.get(column_name, 'Unknown')
        if val in freq_dict:
            freq_dict[val] += 1
        else:
            freq_dict[val] = 1
    return freq_dict


def display_stats(stats, title):
    """
    Prints statistical dictionary in a clean, readable format.
    """
    if not stats:
        return
    print(f"\n===== Statistical Summary: {title} =====")
    print(f"Total Records  : {stats['count']}")
    print(f"Mean (Average) : {stats['mean']}")
    print(f"Median         : {stats['median']}")
    print(f"Minimum Value  : {stats['min']}")
    print(f"Maximum Value  : {stats['max']}")
    print(f"Std Deviation  : {stats['std_dev']}")
    print(f"Sum / Total    : {stats['total']}")
    print("=" * 40)


def display_frequency(freq_dict, column_name):
    """
    Prints frequency table of categories.
    """
    print(f"\n===== Frequency Distribution: {column_name} =====")
    print(f"{'Category':<25} | {'Count':<5}")
    print("-" * 35)
    for category, count in freq_dict.items():
        print(f"{category:<25} | {count:<5}")
    print("-" * 35)


def generate_insights(data):
    """
    Generates meaningful insights from the student data using simple rules and conditions.
    """
    if not data:
        print("No data available to generate insights.")
        return

    exam_scores = extract_numeric_column(data, 'exam_score')
    study_hours = extract_numeric_column(data, 'study_hours')
    attendance = extract_numeric_column(data, 'attendance_pct')

    avg_score = np.mean(exam_scores) if HAS_NUMPY else (sum(exam_scores) / len(exam_scores))
    avg_hours = np.mean(study_hours) if HAS_NUMPY else (sum(study_hours) / len(study_hours))
    avg_attendance = np.mean(attendance) if HAS_NUMPY else (sum(attendance) / len(attendance))

    # Count grade categories
    passed_students = 0
    distinction_students = 0
    at_risk_students = 0

    for row in data:
        score = row['exam_score']
        att = row['attendance_pct']
        if score >= 40:
            passed_students += 1
        if score >= 85:
            distinction_students += 1
        if score < 50 or att < 60:
            at_risk_students += 1

    total = len(data)
    pass_pct = round((passed_students / total) * 100, 2)

    # Top performing student
    top_student = max(data, key=lambda x: x['exam_score'])

    print("\n================ Key Insights & Observations ================")
    print(f"1. Overall Pass Rate: {pass_pct}% ({passed_students} out of {total} students passed).")
    print(f"2. High Achievers: {distinction_students} student(s) scored 85% or above.")
    print(f"3. Top Scorer: {top_student['name']} ({top_student['department']}) with a score of {top_student['exam_score']}.")
    print(f"4. Average Benchmark: An average student studies {round(avg_hours, 1)} hrs/day with {round(avg_attendance, 1)}% attendance.")
    print(f"5. Students Needing Attention: {at_risk_students} student(s) have low attendance (<60%) or low marks (<50).")
    print("=============================================================\n")


def display_sample_data(data, count=5):
    """
    Displays the first few records in table format.
    """
    if not data:
        print("Dataset is empty.")
        return

    print(f"\nDisplaying first {min(count, len(data))} records:")
    print("-" * 75)
    print(f"{'ID':<6} {'Name':<18} {'Department':<22} {'Hours':<6} {'Att%':<6} {'Score':<6}")
    print("-" * 75)
    for row in data[:count]:
        print(f"{row['student_id']:<6} {row['name']:<18} {row['department']:<22} {row['study_hours']:<6} {row['attendance_pct']:<6} {row['exam_score']:<6}")
    print("-" * 75)


def run_cli(cleaned_data):
    """
    Interactive menu loop for user interaction in terminal.
    """
    while True:
        print("\n===== CSV DATA ANALYZER MENU =====")
        print("1. View Sample Records")
        print("2. Analyze Exam Scores (Statistics)")
        print("3. Analyze Study Hours (Statistics)")
        print("4. Analyze Attendance (Statistics)")
        print("5. Department Breakdown (Frequency Distribution)")
        print("6. Generate Key Insights & Summary")
        print("7. Exit Program")
        print("==================================")

        choice = input("Enter your choice (1-7): ").strip()

        if choice == '1':
            display_sample_data(cleaned_data, count=5)
        elif choice == '2':
            stats = calculate_numeric_stats(cleaned_data, 'exam_score')
            display_stats(stats, "Final Exam Scores")
        elif choice == '3':
            stats = calculate_numeric_stats(cleaned_data, 'study_hours')
            display_stats(stats, "Daily Study Hours")
        elif choice == '4':
            stats = calculate_numeric_stats(cleaned_data, 'attendance_pct')
            display_stats(stats, "Attendance Percentage")
        elif choice == '5':
            freq = calculate_frequency(cleaned_data, 'department')
            display_frequency(freq, "Department")
        elif choice == '6':
            generate_insights(cleaned_data)
        elif choice == '7':
            print("\nThank you for using CSV Data Analyzer. Exiting program...\n")
            break
        else:
            print("Invalid choice! Please select a valid option between 1 and 7.")


def main():
    """
    Main function to execute the program pipeline.
    """
    print("=" * 45)
    print("     CSV Data Analyzer Mini Project")
    print("=" * 45)

    # Determine data file path relative to current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, 'data', 'students_data.csv')

    headers, raw_data = load_dataset(file_path)

    if not raw_data:
        print("Exiting because dataset could not be loaded.")
        return

    # Clean the dataset
    cleaned_data = clean_dataset(raw_data)

    if not cleaned_data:
        print("No valid records remaining after cleaning. Exiting.")
        return

    # Start the interactive menu
    run_cli(cleaned_data)


if __name__ == '__main__':
    main()

import csv
import os

# using numpy for stats if installed
try:
    import numpy as np
    HAS_NUMPY = True
except:
    HAS_NUMPY = False

REQUIRED_COLUMNS = ['student_id', 'name', 'department', 'study_hours', 'attendance_pct', 'exam_score']


def validate_csv_path(file_path):
    if not file_path or type(file_path) != str:
        print("[Error] Invalid path")
        return False
    if not os.path.exists(file_path):
        print(f"[Error] File '{file_path}' not found")
        return False
    if not os.path.isfile(file_path):
        print(f"[Error] '{file_path}' is a folder not a file")
        return False
    return True


def load_dataset(file_path):
    # check if path is good
    if not validate_csv_path(file_path):
        return None, None

    rows = []
    try:
        if os.path.getsize(file_path) == 0:
            print(f"[Error] The file '{file_path}' is completely empty (0 bytes).")
            return None, None

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                print(f"[Error] No headers found in '{file_path}'")
                return None, None

            missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
            if len(missing_cols) > 0:
                print("[Error] CSV is missing required column(s):", ", ".join(missing_cols))
                return None, None

            for r in reader:
                if any(val.strip() for val in r.values() if val is not None):
                    rows.append(r)

        if len(rows) == 0:
            print(f"[Warning] CSV file '{file_path}' contains headers but has no data rows.")
            return headers, []

        print(f"-> Successfully loaded {len(rows)} raw rows from '{os.path.basename(file_path)}'.")
        return headers, rows

    except Exception as e:
        print("[Error] Could not read file:", e)
        return None, None


def clean_dataset(raw_rows):
    if not raw_rows:
        return [], {
            'raw_count': 0,
            'clean_count': 0,
            'duplicate_count': 0,
            'missing_count': 0,
            'invalid_count': 0,
            'removed_records': []
        }

    clean_list = []
    seen_ids = set()
    removed = []
    dup_cnt = 0
    missing_cnt = 0
    invalid_cnt = 0

    line_num = 2
    for r in raw_rows:
        sid = r.get("student_id", "").strip()

        # check missing
        missing_fields = []
        for col in REQUIRED_COLUMNS:
            v = r.get(col)
            if v is None or str(v).strip() == "":
                missing_fields.append(col)

        if len(missing_fields) > 0:
            missing_cnt += 1
            removed.append({
                'csv_line': line_num,
                'student_id': sid if sid else "UNKNOWN",
                'reason': f"Missing value in column(s): {', '.join(missing_fields)}"
            })
            line_num += 1
            continue

        # check numeric conversion
        try:
            hours = float(r["study_hours"])
            att = float(r["attendance_pct"])
            score = float(r["exam_score"])
        except:
            invalid_cnt += 1
            removed.append({
                'csv_line': line_num,
                'student_id': sid,
                'reason': "Non-numeric value in numerical column(s)"
            })
            line_num += 1
            continue

        # range checking
        errs = []
        if hours < 0.0 or hours > 24.0:
            errs.append(f"study_hours ({hours}) out of range [0, 24]")
        if att < 0.0 or att > 100.0:
            errs.append(f"attendance_pct ({att}) out of range [0, 100]")
        if score < 0.0 or score > 100.0:
            errs.append(f"exam_score ({score}) out of range [0, 100]")

        if len(errs) > 0:
            invalid_cnt += 1
            removed.append({
                'csv_line': line_num,
                'student_id': sid,
                'reason': "Boundary violation: " + "; ".join(errs)
            })
            line_num += 1
            continue

        # duplicate student id check - keep first one
        if sid in seen_ids:
            dup_cnt += 1
            removed.append({
                'csv_line': line_num,
                'student_id': sid,
                'reason': f"Duplicate student ID '{sid}' (first valid entry already kept)"
            })
            line_num += 1
            continue

        seen_ids.add(sid)
        clean_list.append({
            'student_id': sid,
            'name': str(r['name']).strip(),
            'department': str(r['department']).strip(),
            'study_hours': round(hours, 2),
            'attendance_pct': round(att, 2),
            'exam_score': round(score, 2)
        })
        line_num += 1

    summary = {
        'raw_count': len(raw_rows),
        'clean_count': len(clean_list),
        'duplicate_count': dup_cnt,
        'missing_count': missing_cnt,
        'invalid_count': invalid_cnt,
        'removed_records': removed
    }
    return clean_list, summary


def extract_numeric_column(data, column_name):
    vals = []
    for row in data:
        if column_name in row and row[column_name] is not None:
            try:
                vals.append(float(row[column_name]))
            except:
                pass
    return vals


def calculate_numeric_stats(data, column_name):
    vals = extract_numeric_column(data, column_name)
    if not vals:
        return None

    if HAS_NUMPY:
        arr = np.array(vals, dtype=float)
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

    # fallback without numpy
    n = len(vals)
    tot = sum(vals)
    avg = tot / n

    s = sorted(vals)
    if n % 2 != 0:
        med = s[n // 2]
    else:
        med = (s[n // 2 - 1] + s[n // 2]) / 2.0

    var = sum((x - avg) ** 2 for x in vals) / n
    sd = var ** 0.5

    return {
        'column': column_name,
        'count': n,
        'mean': round(avg, 2),
        'median': round(med, 2),
        'min': round(min(vals), 2),
        'max': round(max(vals), 2),
        'std_dev': round(sd, 2),
        'total': round(tot, 2)
    }


def get_all_numeric_columns():
    return ['study_hours', 'attendance_pct', 'exam_score']


def calculate_frequency(data, column_name):
    freq = {}
    for r in data:
        dept = r.get(column_name, 'Unknown')
        freq[dept] = freq.get(dept, 0) + 1
    return freq


def calculate_grade_distribution(data):
    grades = {
        'Grade A (85-100)': 0,
        'Grade B (70-84)': 0,
        'Grade C (55-69)': 0,
        'Grade D (40-54)': 0,
        'Grade F (<40)': 0
    }
    for item in data:
        sc = item.get('exam_score', 0)
        if sc >= 85:
            grades['Grade A (85-100)'] += 1
        elif sc >= 70:
            grades['Grade B (70-84)'] += 1
        elif sc >= 55:
            grades['Grade C (55-69)'] += 1
        elif sc >= 40:
            grades['Grade D (40-54)'] += 1
        else:
            grades['Grade F (<40)'] += 1
    return grades


def calculate_pass_fail_distribution(data, passing_mark=40.0):
    pf = {'Passed': 0, 'Failed': 0}
    for r in data:
        if r.get('exam_score', 0) >= passing_mark:
            pf['Passed'] += 1
        else:
            pf['Failed'] += 1
    return pf


def generate_insights(data):
    if not data:
        return ["No data available to generate insights."]

    total = len(data)
    best = data[0]
    worst = data[0]
    for s in data[1:]:
        if s['exam_score'] > best['exam_score']:
            best = s
        if s['exam_score'] < worst['exam_score']:
            worst = s

    pf = calculate_pass_fail_distribution(data, passing_mark=40.0)
    passed = pf['Passed']
    failed = pf['Failed']
    pct_pass = round((passed / total) * 100, 2)

    top_students = [s for s in data if s['exam_score'] >= 85.0]
    struggling = [s for s in data if (s['exam_score'] < 50.0 or s['attendance_pct'] < 60.0)]
    low_att = [s for s in data if s['attendance_pct'] < 75.0]

    high_study = [s['exam_score'] for s in data if s['study_hours'] >= 4.0]
    low_study = [s['exam_score'] for s in data if s['study_hours'] < 4.0]

    avg_high = round(sum(high_study) / len(high_study), 2) if high_study else 0.0
    avg_low = round(sum(low_study) / len(low_study), 2) if low_study else 0.0

    score_st = calculate_numeric_stats(data, 'exam_score')
    att_st = calculate_numeric_stats(data, 'attendance_pct')
    study_st = calculate_numeric_stats(data, 'study_hours')

    res = [
        f"1. Pass rate: {pct_pass}% ({passed} passed, {failed} failed out of {total} total students).",
        f"2. Averages: Mean score is {score_st['mean']} (median: {score_st['median']}), attendance avg is {att_st['mean']}%, and avg study hours is {study_st['mean']}.",
        f"3. Top Scorer: {best['name']} ({best['student_id']}) from {best['department']} with {best['exam_score']}.",
        f"4. Lowest Scorer: {worst['name']} ({worst['student_id']}) from {worst['department']} with {worst['exam_score']}.",
        f"5. Grade A: {len(top_students)} student(s) got 85 or higher.",
        f"6. Attendance warning: {len(low_att)} student(s) below the 75% college requirement.",
        f"7. Need help: {len(struggling)} student(s) have low scores or attendance under 60%.",
        f"8. Study hours vs scores: students studying 4+ hrs avg {avg_high} vs {avg_low} for under 4 hrs."
    ]
    return res


def display_dataset_info(file_path, headers, raw_count, clean_count):
    print("\n" + "=" * 40)
    print("        DATASET INFO")
    print("=" * 40)
    print("File:", file_path)
    print("Engine:", "NumPy" if HAS_NUMPY else "Standard Python")
    print("Raw rows:", raw_count)
    print("Clean rows:", clean_count)
    print("Removed:", raw_count - clean_count)
    print("\nColumns found:")
    print("-" * 35)
    for col in headers:
        print(" -", col)
    print("=" * 40)


def display_sample_data(data, count=5):
    if not data:
        print("\nNo data to show.")
        return

    n = min(count, len(data))
    print(f"\n--- Showing first {n} rows ---")
    print("ID     Name               Dept                 Hours  Att%   Score")
    print("-" * 65)
    for r in data[:n]:
        print(f"{r['student_id']:<6} {r['name']:<18} {r['department']:<20} {r['study_hours']:<6} {r['attendance_pct']:<6} {r['exam_score']}")
    print("-" * 65)


def display_stats(stats, title):
    if not stats:
        print(f"\nNo stats for {title}")
        return

    print("\n" + "-" * 35)
    print(f"Stats: {title}")
    print("-" * 35)
    print(f"Count:         {stats['count']}")
    print(f"Mean:          {stats['mean']}")
    print(f"Median:        {stats['median']}")
    print(f"Min:           {stats['min']}")
    print(f"Max:           {stats['max']}")
    print(f"Std Dev:       {stats['std_dev']}")
    print(f"Total:         {stats['total']}")
    print("-" * 35)


def display_all_numeric_stats(data):
    print("\n" + "=" * 55)
    print("           NUMERICAL STATS SUMMARY")
    print("=" * 55)
    cols = [('exam_score', 'Score'), ('study_hours', 'Hours'), ('attendance_pct', 'Att %')]
    st_map = {k: calculate_numeric_stats(data, k) for k, _ in cols}

    print(f"{'Metric':<14} | {'Score':<10} | {'Hours':<10} | {'Att %':<10}")
    print("-" * 52)
    keys = ['count', 'mean', 'median', 'min', 'max', 'std_dev', 'total']
    for k in keys:
        s1 = st_map['exam_score'][k] if st_map['exam_score'] else 'N/A'
        s2 = st_map['study_hours'][k] if st_map['study_hours'] else 'N/A'
        s3 = st_map['attendance_pct'][k] if st_map['attendance_pct'] else 'N/A'
        print(f"{k:<14} | {str(s1):<10} | {str(s2):<10} | {str(s3):<10}")
    print("=" * 55)


def display_frequency_table(freq_dict, category_name):
    tot = sum(freq_dict.values())
    print(f"\n--- {category_name} ---")
    for k, v in freq_dict.items():
        pct = round((v / tot) * 100, 1) if tot > 0 else 0
        print(f"  {k}: {v} ({pct}%)")


def display_cleaning_summary(summary):
    print("\n" + "=" * 45)
    print("       CLEANING SUMMARY")
    print("=" * 45)
    print("Total rows read:     ", summary['raw_count'])
    print("Valid rows kept:     ", summary['clean_count'])
    print("Invalid rows dropped:", summary['raw_count'] - summary['clean_count'])
    print(" - Duplicates:       ", summary['duplicate_count'])
    print(" - Missing fields:   ", summary['missing_count'])
    print(" - Out of range:     ", summary['invalid_count'])
    print("-" * 45)

    if summary['removed_records']:
        print("Dropped rows detail:")
        for itm in summary['removed_records']:
            print(f"  Line {itm['csv_line']} (ID: {itm['student_id']}): {itm['reason']}")
    else:
        print("No rows had to be removed!")
    print("=" * 45)


def export_analysis_report(file_path, cleaned_data, raw_data_count, cleaning_summary, output_path):
    try:
        out_folder = os.path.dirname(output_path)
        if out_folder and not os.path.exists(out_folder):
            os.makedirs(out_folder, exist_ok=True)

        lines = [
            "================================================================================",
            "                CSV DATA ANALYZER - ACADEMIC ANALYSIS REPORT",
            "================================================================================",
            f"File: {os.path.basename(file_path)}",
            f"Author: Arhaan Sethi",
            f"Engine: {'NumPy' if HAS_NUMPY else 'Python stdlib'}",
            "",
            "1. DATA CLEANING AUDIT",
            "--------------------------------------------------------------------------------",
            f"Raw Records: {raw_data_count}",
            f"Clean Records: {cleaning_summary['clean_count']}",
            f"Excluded: {raw_data_count - cleaning_summary['clean_count']}",
            f"  - Duplicates: {cleaning_summary['duplicate_count']}",
            f"  - Missing: {cleaning_summary['missing_count']}",
            f"  - Out of range / invalid: {cleaning_summary['invalid_count']}",
            "",
            "Excluded Records Detail:"
        ]

        if cleaning_summary['removed_records']:
            for itm in cleaning_summary['removed_records']:
                lines.append(f"  * [CSV Line {itm['csv_line']}] ID: {itm['student_id']} -> {itm['reason']}")
        else:
            lines.append("  * None.")

        lines.extend([
            "--------------------------------------------------------------------------------",
            "",
            "2. NUMERICAL DESCRIPTIVE STATISTICS",
            "--------------------------------------------------------------------------------"
        ])

        col_tuples = [
            ('exam_score', 'Exam Score'),
            ('study_hours', 'Daily Study Hours'),
            ('attendance_pct', 'Attendance Pct')
        ]
        for col_name, lbl in col_tuples:
            st = calculate_numeric_stats(cleaned_data, col_name)
            if st:
                lines.append(f"Column: {lbl}")
                lines.append(f"  Count:    {st['count']}")
                lines.append(f"  Mean:     {st['mean']}")
                lines.append(f"  Median:   {st['median']}")
                lines.append(f"  Min:      {st['min']}")
                lines.append(f"  Max:      {st['max']}")
                lines.append(f"  Std Dev:  {st['std_dev']}")
                lines.append(f"  Total:    {st['total']}")
                lines.append("")

        lines.extend([
            "3. CATEGORICAL FREQUENCY DISTRIBUTIONS",
            "--------------------------------------------------------------------------------",
            "Departments:"
        ])
        dept_f = calculate_frequency(cleaned_data, 'department')
        for d, c in dept_f.items():
            lines.append(f"  {d}: {c}")

        lines.append("\nGrade Distribution:")
        grd_f = calculate_grade_distribution(cleaned_data)
        for g, c in grd_f.items():
            lines.append(f"  {g}: {c}")

        lines.append("\nPass/Fail:")
        pf_f = calculate_pass_fail_distribution(cleaned_data)
        for p, c in pf_f.items():
            lines.append(f"  {p}: {c}")

        lines.extend([
            "",
            "4. AUTOMATED ACADEMIC INSIGHTS",
            "--------------------------------------------------------------------------------"
        ])
        for ins in generate_insights(cleaned_data):
            lines.append(ins)

        lines.append("================================================================================")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")

        print(f"\n[Success] Full report exported successfully to: '{output_path}'")
        return True

    except Exception as e:
        print("[Error] Export failed:", e)
        return False


def handle_numeric_stats_menu(cleaned_data):
    while True:
        print("\n--- Numerical Stats Menu ---")
        print("1. Exam scores")
        print("2. Study hours")
        print("3. Attendance pct")
        print("4. Compare all columns")
        print("5. Back")

        opt = input("Pick an option (1-5): ").strip()
        if opt == '1':
            st = calculate_numeric_stats(cleaned_data, 'exam_score')
            display_stats(st, "Exam Score")
        elif opt == '2':
            st = calculate_numeric_stats(cleaned_data, 'study_hours')
            display_stats(st, "Study Hours")
        elif opt == '3':
            st = calculate_numeric_stats(cleaned_data, 'attendance_pct')
            display_stats(st, "Attendance %")
        elif opt == '4':
            display_all_numeric_stats(cleaned_data)
        elif opt == '5':
            break
        else:
            print("Invalid input, enter 1 to 5")


def handle_frequency_menu(cleaned_data):
    while True:
        print("\n-- Categorical stats --")
        print("1. Dept breakdown")
        print("2. Grade distribution")
        print("3. Pass vs fail count")
        print("4. Show all")
        print("5. Back to main menu")

        opt = input("Choose (1-5): ").strip()
        if opt == '1':
            display_frequency_table(calculate_frequency(cleaned_data, 'department'), "Department")
        elif opt == '2':
            display_frequency_table(calculate_grade_distribution(cleaned_data), "Grades")
        elif opt == '3':
            display_frequency_table(calculate_pass_fail_distribution(cleaned_data), "Pass/Fail")
        elif opt == '4':
            display_frequency_table(calculate_frequency(cleaned_data, 'department'), "Department")
            display_frequency_table(calculate_grade_distribution(cleaned_data), "Grades")
            display_frequency_table(calculate_pass_fail_distribution(cleaned_data), "Pass/Fail")
        elif opt == '5':
            break
        else:
            print("Wrong option, try again")


def run_cli(cleaned_data, raw_data, headers, file_path, cleaning_summary):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    rep_path = os.path.join(os.path.dirname(cur_dir), 'output', 'analysis_report.txt')

    while True:
        print("\n=== Student CSV Analyzer ===")
        print("1. Show dataset info")
        print("2. Preview first few rows")
        print("3. Numerical statistics")
        print("4. Department & Grade breakdown")
        print("5. Key insights")
        print("6. Data cleaning summary")
        print("7. Export report to file")
        print("8. Exit")

        ch = input("Enter choice (1-8): ").strip()
        if ch == '1':
            display_dataset_info(file_path, headers, len(raw_data), len(cleaned_data))
        elif ch == '2':
            num = input("How many rows to print? (default 5): ").strip()
            cnt = int(num) if num.isdigit() and int(num) > 0 else 5
            display_sample_data(cleaned_data, count=cnt)
        elif ch == '3':
            handle_numeric_stats_menu(cleaned_data)
        elif ch == '4':
            handle_frequency_menu(cleaned_data)
        elif ch == '5':
            print("\n--- Key Insights ---")
            for line in generate_insights(cleaned_data):
                print(line)
        elif ch == '6':
            display_cleaning_summary(cleaning_summary)
        elif ch == '7':
            export_analysis_report(file_path, cleaned_data, len(raw_data), cleaning_summary, rep_path)
        elif ch == '8':
            print("\nBye!")
            break
        else:
            print("Please enter a number between 1 and 8.")


def main():
    print("CSV Data Analyzer - Python Project")
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_csv = os.path.join(base, 'data', 'students_data.csv')

    print("Loading default CSV:", default_csv)
    headers, raw_data = load_dataset(default_csv)
    if not raw_data:
        print("Could not load data.")
        return

    cleaned_data, summary = clean_dataset(raw_data)
    if not cleaned_data:
        print("No valid data left after cleaning.")
        return

    run_cli(cleaned_data, raw_data, headers, default_csv, summary)


if __name__ == '__main__':
    main()

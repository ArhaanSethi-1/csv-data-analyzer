"""
Unit tests for CSV Data Analyzer.
"""

import os
import shutil
import tempfile
import unittest

from src.analyzer import (
    validate_csv_path,
    load_dataset,
    clean_dataset,
    extract_numeric_column,
    calculate_numeric_stats,
    calculate_frequency,
    calculate_grade_distribution,
    calculate_pass_fail_distribution,
    generate_insights,
    export_analysis_report
)


class TestCSVDataAnalyzer(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        # 1. Valid test CSV
        self.valid_csv_path = os.path.join(self.test_dir, "valid_students.csv")
        with open(self.valid_csv_path, mode="w", encoding="utf-8") as f:
            f.write(
                "student_id,name,department,study_hours,attendance_pct,exam_score\n"
                "S1,Alice,Computer Science,4.0,90.0,85.0\n"
                "S2,Bob,Mechanical,2.0,70.0,55.0\n"
                "S3,Charlie,Electrical,3.0,80.0,70.0\n"
            )

        # 2. CSV with duplicates, missing values, and out-of-range values
        self.dirty_csv_path = os.path.join(self.test_dir, "dirty_students.csv")
        with open(self.dirty_csv_path, mode="w", encoding="utf-8") as f:
            f.write(
                "student_id,name,department,study_hours,attendance_pct,exam_score\n"
                "S1,Alice,Computer Science,4.0,90.0,85.0\n"
                "S1,Alice Duplicate,Computer Science,4.0,90.0,85.0\n"  # Duplicate ID
                "S2,Bob,Mechanical,,70.0,55.0\n"                      # Missing study_hours
                "S3,Charlie,Electrical,3.0,,70.0\n"                   # Missing attendance
                "S4,David,Civil,3.0,80.0,-10.0\n"                     # Negative exam_score
                "S5,Eva,Civil,25.0,80.0,60.0\n"                       # Study hours > 24
                "S6,Frank,Civil,2.0,150.0,60.0\n"                     # Attendance > 100
                "S7,Grace,Information Technology,abc,80.0,75.0\n"     # Non-numeric study_hours
                "S8,Heidi,Computer Science,5.0,95.0,92.0\n"           # Valid
            )

        # 3. Empty CSV (0 bytes)
        self.empty_csv_path = os.path.join(self.test_dir, "empty.csv")
        with open(self.empty_csv_path, mode="w", encoding="utf-8") as f:
            pass

        # 4. Headers-only CSV
        self.headers_only_csv_path = os.path.join(self.test_dir, "headers_only.csv")
        with open(self.headers_only_csv_path, mode="w", encoding="utf-8") as f:
            f.write("student_id,name,department,study_hours,attendance_pct,exam_score\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # --- Loading Tests ---

    def test_load_dataset_success(self):
        headers, rows = load_dataset(self.valid_csv_path)
        self.assertIsNotNone(headers)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["name"], "Alice")

    def test_load_dataset_missing_file(self):
        fake_path = os.path.join(self.test_dir, "does_not_exist.csv")
        headers, rows = load_dataset(fake_path)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    def test_load_dataset_empty_file(self):
        headers, rows = load_dataset(self.empty_csv_path)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    def test_load_dataset_headers_only(self):
        headers, rows = load_dataset(self.headers_only_csv_path)
        self.assertIsNotNone(headers)
        self.assertEqual(len(rows), 0)

    def test_load_dataset_missing_required_headers(self):
        bad_csv = os.path.join(self.test_dir, "bad_headers.csv")
        with open(bad_csv, mode="w", encoding="utf-8") as f:
            f.write("col_a,col_b\n1,2\n")

        headers, rows = load_dataset(bad_csv)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    # --- Cleaning Tests ---

    def test_clean_dataset_duplicate_ids(self):
        headers, raw = load_dataset(self.dirty_csv_path)
        cleaned, summary = clean_dataset(raw)
        self.assertEqual(summary["duplicate_count"], 1)

        ids = [row["student_id"] for row in cleaned]
        self.assertEqual(ids.count("S1"), 1)

    def test_clean_dataset_missing_values(self):
        headers, raw = load_dataset(self.dirty_csv_path)
        _, summary = clean_dataset(raw)
        self.assertEqual(summary["missing_count"], 2)

    def test_clean_dataset_invalid_and_out_of_range(self):
        headers, raw = load_dataset(self.dirty_csv_path)
        _, summary = clean_dataset(raw)
        self.assertEqual(summary["invalid_count"], 4)

    def test_clean_dataset_empty_input(self):
        cleaned, summary = clean_dataset([])
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(summary["clean_count"], 0)
        self.assertEqual(summary["raw_count"], 0)

    # --- Numerical Statistics Tests ---

    def test_calculate_numeric_stats_accuracy(self):
        sample_data = [
            {"exam_score": 10.0},
            {"exam_score": 20.0},
            {"exam_score": 30.0},
            {"exam_score": 40.0},
            {"exam_score": 50.0}
        ]
        stats = calculate_numeric_stats(sample_data, "exam_score")
        self.assertIsNotNone(stats)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["mean"], 30.0)
        self.assertEqual(stats["median"], 30.0)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 50.0)
        self.assertEqual(stats["total"], 150.0)
        self.assertEqual(stats["std_dev"], 14.14)

    def test_calculate_numeric_stats_empty_column(self):
        stats_empty = calculate_numeric_stats([], "exam_score")
        self.assertIsNone(stats_empty)

        sample_data = [{"name": "Alice"}]
        stats_missing = calculate_numeric_stats(sample_data, "exam_score")
        self.assertIsNone(stats_missing)

    # --- Frequency & Categorical Tests ---

    def test_calculate_frequency(self):
        sample_data = [
            {"department": "Computer Science"},
            {"department": "Mechanical"},
            {"department": "Computer Science"}
        ]
        freq = calculate_frequency(sample_data, "department")
        self.assertEqual(freq["Computer Science"], 2)
        self.assertEqual(freq["Mechanical"], 1)

    def test_calculate_grade_distribution(self):
        sample_data = [
            {"exam_score": 90.0},
            {"exam_score": 75.0},
            {"exam_score": 60.0},
            {"exam_score": 45.0},
            {"exam_score": 30.0}
        ]
        grades = calculate_grade_distribution(sample_data)
        self.assertEqual(grades["Grade A (85-100)"], 1)
        self.assertEqual(grades["Grade B (70-84)"], 1)
        self.assertEqual(grades["Grade C (55-69)"], 1)
        self.assertEqual(grades["Grade D (40-54)"], 1)
        self.assertEqual(grades["Grade F (<40)"], 1)

    def test_calculate_pass_fail_distribution(self):
        sample_data = [
            {"exam_score": 85.0},
            {"exam_score": 39.5},
            {"exam_score": 40.0}
        ]
        pf = calculate_pass_fail_distribution(sample_data, passing_mark=40.0)
        self.assertEqual(pf["Passed"], 2)
        self.assertEqual(pf["Failed"], 1)

    # --- Insights & Report Export Tests ---

    def test_generate_insights(self):
        sample_data = [
            {
                "student_id": "S1", "name": "Alice", "department": "Computer Science",
                "study_hours": 5.0, "attendance_pct": 95.0, "exam_score": 90.0
            },
            {
                "student_id": "S2", "name": "Bob", "department": "Civil",
                "study_hours": 1.5, "attendance_pct": 50.0, "exam_score": 45.0
            }
        ]
        insights = generate_insights(sample_data)
        self.assertTrue(len(insights) >= 5)
        self.assertTrue(any("Alice" in line for line in insights))
        self.assertTrue(any("Attendance" in line for line in insights))

    def test_export_analysis_report(self):
        headers, raw = load_dataset(self.valid_csv_path)
        cleaned, summary = clean_dataset(raw)

        report_path = os.path.join(self.test_dir, "output", "test_report.txt")
        success = export_analysis_report(
            file_path=self.valid_csv_path,
            cleaned_data=cleaned,
            raw_data_count=len(raw),
            cleaning_summary=summary,
            output_path=report_path
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, mode="r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("CSV DATA ANALYZER - ACADEMIC ANALYSIS REPORT", content)
        self.assertIn("DATA CLEANING AUDIT", content)
        self.assertIn("NUMERICAL DESCRIPTIVE STATISTICS", content)
        self.assertIn("CATEGORICAL FREQUENCY DISTRIBUTIONS", content)
        self.assertIn("AUTOMATED ACADEMIC INSIGHTS", content)


if __name__ == "__main__":
    unittest.main()

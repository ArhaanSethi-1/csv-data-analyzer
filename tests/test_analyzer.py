"""
=============================================================================
Unit Tests for CSV Data Analyzer
=============================================================================
Tests all core functional modules:
- CSV file loading & path validation
- Data cleaning logic (duplicates, missing, invalid values)
- Numerical calculations (mean, median, min, max, std_dev, sum, count)
- Categorical frequency distributions
- Automated insights generation
- Report file generation and persistence
=============================================================================
"""

import os
import unittest
import tempfile
import shutil

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
    """
    Test suite using Python's built-in unittest framework.
    """

    def setUp(self):
        """
        Creates a temporary directory with test CSV fixtures.
        """
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
                "S4,David,Civil,3.0,80.0,-10.0\n"                     # Out of range exam_score
                "S5,Eva,Civil,25.0,80.0,60.0\n"                       # Out of range study_hours (>24)
                "S6,Frank,Civil,2.0,150.0,60.0\n"                     # Out of range attendance (>100)
                "S7,Grace,Information Technology,abc,80.0,75.0\n"     # Non-numeric study_hours
                "S8,Heidi,Computer Science,5.0,95.0,92.0\n"           # Valid
            )

        # 3. Empty CSV (0 bytes)
        self.empty_csv_path = os.path.join(self.test_dir, "empty.csv")
        with open(self.empty_csv_path, mode="w", encoding="utf-8") as f:
            pass

        # 4. CSV with headers only (no rows)
        self.headers_only_csv_path = os.path.join(self.test_dir, "headers_only.csv")
        with open(self.headers_only_csv_path, mode="w", encoding="utf-8") as f:
            f.write("student_id,name,department,study_hours,attendance_pct,exam_score\n")

        # 5. CSV with missing required headers
        self.invalid_headers_csv_path = os.path.join(self.test_dir, "bad_headers.csv")
        with open(self.invalid_headers_csv_path, mode="w", encoding="utf-8") as f:
            f.write("id,student_name,score\n1,Alice,90\n")

    def tearDown(self):
        """
        Cleans up temporary directory after tests complete.
        """
        shutil.rmtree(self.test_dir)

    # -------------------------------------------------------------------------
    # A. CSV LOADING TESTS
    # -------------------------------------------------------------------------

    def test_load_dataset_success(self):
        """Tests that a well-formed CSV file loads successfully."""
        headers, rows = load_dataset(self.valid_csv_path)
        self.assertIsNotNone(headers)
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows), 3)
        self.assertIn("student_id", headers)

    def test_load_dataset_missing_file(self):
        """Tests that attempting to load a non-existent file returns (None, None)."""
        non_existent_path = os.path.join(self.test_dir, "does_not_exist.csv")
        headers, rows = load_dataset(non_existent_path)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    def test_load_dataset_empty_file(self):
        """Tests that a zero-byte empty CSV returns (None, None)."""
        headers, rows = load_dataset(self.empty_csv_path)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    def test_load_dataset_headers_only(self):
        """Tests that a CSV with headers but no data rows returns empty row list."""
        headers, rows = load_dataset(self.headers_only_csv_path)
        self.assertIsNotNone(headers)
        self.assertEqual(len(rows), 0)

    def test_load_dataset_missing_required_headers(self):
        """Tests that a CSV missing mandatory columns is rejected."""
        headers, rows = load_dataset(self.invalid_headers_csv_path)
        self.assertIsNone(headers)
        self.assertIsNone(rows)

    # -------------------------------------------------------------------------
    # B. DATA CLEANING TESTS
    # -------------------------------------------------------------------------

    def test_clean_dataset_duplicate_ids(self):
        """Tests that duplicate student IDs are filtered out and logged."""
        headers, raw = load_dataset(self.dirty_csv_path)
        cleaned, summary = clean_dataset(raw)

        # Expected retained valid records: S1 and S8
        self.assertEqual(summary["raw_count"], 9)
        self.assertEqual(summary["clean_count"], 2)
        self.assertEqual(summary["duplicate_count"], 1)

        # Verify only one instance of S1 is retained
        retained_ids = [r["student_id"] for r in cleaned]
        self.assertEqual(retained_ids.count("S1"), 1)
        self.assertIn("S8", retained_ids)

    def test_clean_dataset_missing_values(self):
        """Tests that rows with blank or missing values are rejected."""
        headers, raw = load_dataset(self.dirty_csv_path)
        _, summary = clean_dataset(raw)
        self.assertEqual(summary["missing_count"], 2)  # S2 (study_hours), S3 (attendance)

    def test_clean_dataset_invalid_and_out_of_range(self):
        """Tests that out-of-range and non-numeric values are rejected."""
        headers, raw = load_dataset(self.dirty_csv_path)
        _, summary = clean_dataset(raw)
        # S4 (negative score), S5 (hours > 24), S6 (att > 100), S7 (non-numeric hours)
        self.assertEqual(summary["invalid_count"], 4)

    def test_clean_dataset_empty_input(self):
        """Tests that passing an empty list to clean_dataset does not crash."""
        cleaned, summary = clean_dataset([])
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(summary["clean_count"], 0)
        self.assertEqual(summary["raw_count"], 0)

    # -------------------------------------------------------------------------
    # C. NUMERICAL STATISTICS TESTS
    # -------------------------------------------------------------------------

    def test_calculate_numeric_stats_accuracy(self):
        """Tests statistical metrics against known mathematical values."""
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
        # Population standard deviation of [10, 20, 30, 40, 50] is sqrt(200) = 14.14
        self.assertEqual(stats["std_dev"], 14.14)

    def test_calculate_numeric_stats_empty_column(self):
        """Tests that passing an empty dataset or non-existent column returns None."""
        stats_empty = calculate_numeric_stats([], "exam_score")
        self.assertIsNone(stats_empty)

        sample_data = [{"name": "Alice"}]
        stats_missing = calculate_numeric_stats(sample_data, "exam_score")
        self.assertIsNone(stats_missing)

    # -------------------------------------------------------------------------
    # D. FREQUENCY & CATEGORICAL TESTS
    # -------------------------------------------------------------------------

    def test_calculate_frequency(self):
        """Tests department frequency counting."""
        sample_data = [
            {"department": "Computer Science"},
            {"department": "Mechanical"},
            {"department": "Computer Science"}
        ]
        freq = calculate_frequency(sample_data, "department")
        self.assertEqual(freq["Computer Science"], 2)
        self.assertEqual(freq["Mechanical"], 1)

    def test_calculate_grade_distribution(self):
        """Tests student grading categorization."""
        sample_data = [
            {"exam_score": 90.0},  # Grade A
            {"exam_score": 75.0},  # Grade B
            {"exam_score": 60.0},  # Grade C
            {"exam_score": 45.0},  # Grade D
            {"exam_score": 30.0}   # Grade F
        ]
        grades = calculate_grade_distribution(sample_data)
        self.assertEqual(grades["Grade A (85-100)"], 1)
        self.assertEqual(grades["Grade B (70-84)"], 1)
        self.assertEqual(grades["Grade C (55-69)"], 1)
        self.assertEqual(grades["Grade D (40-54)"], 1)
        self.assertEqual(grades["Grade F (<40)"], 1)

    def test_calculate_pass_fail_distribution(self):
        """Tests pass/fail counts at standard 40-mark threshold."""
        sample_data = [
            {"exam_score": 85.0},
            {"exam_score": 39.5},
            {"exam_score": 40.0}
        ]
        pf = calculate_pass_fail_distribution(sample_data, passing_mark=40.0)
        self.assertEqual(pf["Passed"], 2)
        self.assertEqual(pf["Failed"], 1)

    # -------------------------------------------------------------------------
    # E. INSIGHTS GENERATION & REPORT EXPORT TESTS
    # -------------------------------------------------------------------------

    def test_generate_insights(self):
        """Tests that insights list is generated with expected content."""
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
        # Check that top scorer is identified
        self.assertTrue(any("Alice" in line for line in insights))
        # Check that attendance observation is present
        self.assertTrue(any("Attendance" in line for line in insights))

    def test_export_analysis_report(self):
        """Tests that the report text file is created and contains vital sections."""
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

import os
import tempfile
import unittest

from src.analyzer import (
    load_dataset,
    clean_dataset,
    calculate_numeric_stats,
    calculate_grade_distribution,
    calculate_pass_fail_distribution,
    generate_insights,
    export_analysis_report
)


class TestLoading(unittest.TestCase):

    def test_load_valid_csv(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, 'w') as f:
            f.write("student_id,name,department,study_hours,attendance_pct,exam_score\n")
            f.write("S1,Alice,CS,3.0,80.0,70.0\n")
            f.write("S2,Bob,Mech,2.0,60.0,55.0\n")
        headers, rows = load_dataset(path)
        os.remove(path)
        self.assertIsNotNone(headers)
        self.assertEqual(len(rows), 2)

    def test_load_missing_file(self):
        h, r = load_dataset("this_file_doesnt_exist.csv")
        self.assertIsNone(h)

    def test_load_missing_columns(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, 'w') as f:
            f.write("id,name\n")
            f.write("S1,Alice\n")
        h, r = load_dataset(path)
        os.remove(path)
        self.assertIsNone(h)


class TestCleaning(unittest.TestCase):

    def test_removes_missing_fields(self):
        rows = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': '3', 'attendance_pct': '80', 'exam_score': '70'},
            {'student_id': 'S2', 'name': 'Bob', 'department': 'CS',
             'study_hours': '', 'attendance_pct': '80', 'exam_score': '70'},
        ]
        cleaned, summary = clean_dataset(rows)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(summary['dropped_count'], 1)

    def test_removes_duplicates(self):
        rows = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': '3', 'attendance_pct': '80', 'exam_score': '70'},
            {'student_id': 'S1', 'name': 'Alice Again', 'department': 'CS',
             'study_hours': '3', 'attendance_pct': '80', 'exam_score': '70'},
        ]
        cleaned, summary = clean_dataset(rows)
        self.assertEqual(len(cleaned), 1)

    def test_removes_negative_score(self):
        rows = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': '3', 'attendance_pct': '80', 'exam_score': '-10'},
        ]
        cleaned, _ = clean_dataset(rows)
        self.assertEqual(len(cleaned), 0)

    def test_removes_non_numeric(self):
        rows = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': 'abc', 'attendance_pct': '80', 'exam_score': '70'},
        ]
        cleaned, _ = clean_dataset(rows)
        self.assertEqual(len(cleaned), 0)

    def test_empty_input(self):
        cleaned, summary = clean_dataset([])
        self.assertEqual(len(cleaned), 0)
        self.assertEqual(summary['raw_count'], 0)


class TestStats(unittest.TestCase):

    def test_basic_stats(self):
        data = [{'exam_score': 10.0}, {'exam_score': 20.0}, {'exam_score': 30.0}]
        stats = calculate_numeric_stats(data, 'exam_score')
        self.assertEqual(stats['count'], 3)
        self.assertEqual(stats['mean'], 20.0)
        self.assertEqual(stats['median'], 20.0)
        self.assertEqual(stats['min'], 10.0)
        self.assertEqual(stats['max'], 30.0)

    def test_empty_data_returns_none(self):
        stats = calculate_numeric_stats([], 'exam_score')
        self.assertIsNone(stats)

    def test_grade_distribution(self):
        data = [
            {'exam_score': 92.0},
            {'exam_score': 73.0},
            {'exam_score': 60.0},
            {'exam_score': 45.0},
            {'exam_score': 30.0},
        ]
        grades = calculate_grade_distribution(data)
        self.assertEqual(grades['Grade A (85-100)'], 1)
        self.assertEqual(grades['Grade F (<40)'], 1)

    def test_pass_fail(self):
        data = [{'exam_score': 85.0}, {'exam_score': 35.0}, {'exam_score': 40.0}]
        pf = calculate_pass_fail_distribution(data)
        self.assertEqual(pf['Passed'], 2)
        self.assertEqual(pf['Failed'], 1)


class TestInsightsAndExport(unittest.TestCase):

    def test_insights_returns_list(self):
        data = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': 5.0, 'attendance_pct': 90.0, 'exam_score': 88.0},
            {'student_id': 'S2', 'name': 'Bob', 'department': 'Mech',
             'study_hours': 1.0, 'attendance_pct': 45.0, 'exam_score': 42.0},
        ]
        insights = generate_insights(data)
        self.assertGreater(len(insights), 3)
        self.assertTrue(any("Alice" in line for line in insights))

    def test_export_creates_file(self):
        data = [
            {'student_id': 'S1', 'name': 'Alice', 'department': 'CS',
             'study_hours': 5.0, 'attendance_pct': 90.0, 'exam_score': 88.0},
        ]
        summary = {'raw_count': 1, 'clean_count': 1, 'dropped_count': 0}
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        result = export_analysis_report("test.csv", data, 1, summary, path)
        self.assertTrue(result)
        self.assertTrue(os.path.getsize(path) > 0)
        os.remove(path)


if __name__ == '__main__':
    unittest.main()

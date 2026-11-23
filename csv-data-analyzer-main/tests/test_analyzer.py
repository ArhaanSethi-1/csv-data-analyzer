import os
import tempfile
import unittest

from src.analyzer import (
    load_dataset,
    clean_dataset,
    calculate_numeric_stats,
    calculate_grade_distribution,
    export_analysis_report
)


class TestAnalyzer(unittest.TestCase):

    def test_load(self):
        # test with a dummy csv
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, 'w') as f:
            f.write("student_id,name,department,study_hours,attendance_pct,exam_score\n")
            f.write("S1,John,CS,2.0,80.0,75.0\n")

        headers, rows = load_dataset(path)
        os.remove(path)
        self.assertIsNotNone(headers)
        self.assertEqual(len(rows), 1)

    def test_bad_file(self):
        # test missing file
        h, r = load_dataset("non_existent_file_xyz.csv")
        self.assertIsNone(h)
        self.assertIsNone(r)

    def test_clean(self):
        sample = [
            {'student_id': 'S1', 'name': 'John', 'department': 'CS', 'study_hours': '2', 'attendance_pct': '80', 'exam_score': '75'},
            {'student_id': 'S1', 'name': 'John Dup', 'department': 'CS', 'study_hours': '2', 'attendance_pct': '80', 'exam_score': '75'},
            {'student_id': 'S2', 'name': 'Bad', 'department': 'CS', 'study_hours': '2', 'attendance_pct': '80', 'exam_score': '-5'}
        ]
        cleaned, summary = clean_dataset(sample)
        self.assertEqual(summary['duplicate_count'], 1)
        self.assertEqual(summary['invalid_count'], 1)
        self.assertEqual(len(cleaned), 1)

    def test_stats_works(self):
        data = [{'exam_score': 10}, {'exam_score': 20}, {'exam_score': 30}]
        stats = calculate_numeric_stats(data, 'exam_score')
        self.assertIsNotNone(stats)
        self.assertEqual(stats['mean'], 20.0)

    def test_grades(self):
        # lazy test just checking it returns something
        data = [{'exam_score': 90}, {'exam_score': 50}]
        g = calculate_grade_distribution(data)
        self.assertIsNotNone(g)
        self.assertEqual(g['Grade A (85-100)'], 1)


if __name__ == '__main__':
    unittest.main()

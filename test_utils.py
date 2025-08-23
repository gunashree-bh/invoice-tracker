import unittest
from datetime import date, timedelta
from app import compute_aging_bucket

class TestAgingBucket(unittest.TestCase):

    def setUp(self):
        self.today = date(2025, 8, 22)  # fixed "today" for consistent testing

    def test_not_due(self):
        due = self.today + timedelta(days=5)
        self.assertEqual(compute_aging_bucket(due, self.today), "Not Due")

    def test_0_30_days(self):
        due = self.today - timedelta(days=15)
        self.assertEqual(compute_aging_bucket(due, self.today), "0-30")

    def test_31_60_days(self):
        due = self.today - timedelta(days=45)
        self.assertEqual(compute_aging_bucket(due, self.today), "31-60")

    def test_61_90_days(self):
        due = self.today - timedelta(days=75)
        self.assertEqual(compute_aging_bucket(due, self.today), "61-90")

    def test_90_plus_days(self):
        due = self.today - timedelta(days=120)
        self.assertEqual(compute_aging_bucket(due, self.today), "90+")

if __name__ == "__main__":
    unittest.main()

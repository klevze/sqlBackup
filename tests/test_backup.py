import unittest
import datetime
from src.backup import format_size, should_upload

class TestBackupHelpers(unittest.TestCase):
    def test_format_size_bytes(self):
        self.assertEqual(format_size(500), "500 B")

    def test_format_size_kb(self):
        self.assertEqual(format_size(2048), "2.0 KB")

    def test_format_size_mb(self):
        self.assertEqual(format_size(1048576), "1.0 MB")

    def test_format_size_gb(self):
        self.assertEqual(format_size(1073741824), "1.0 GB")

    def test_should_upload_daily(self):
        self.assertTrue(should_upload("daily"))

    def test_should_upload_numeric(self):
        now = datetime.datetime.now()
        self.assertTrue(should_upload(str(now.day)))

if __name__ == "__main__":
    unittest.main()

import unittest
from src.config import load_config

class TestConfig(unittest.TestCase):
    def test_config_loaded(self):
        config = load_config()
        # Check that required sections exist.
        self.assertTrue(config.has_section("backup"))
        self.assertTrue(config.has_section("mysql"))
        self.assertTrue(config.has_section("notification"))

if __name__ == "__main__":
    unittest.main()

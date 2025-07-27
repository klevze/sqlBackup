#!/usr/bin/env python3
"""
Comprehensive test runner for sqlBackup project
"""

import unittest
import sys
import os
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all test modules
from tests.test_backup import *
from tests.test_config import *
from tests.test_notifications import *
from tests.test_remote_upload import *
from tests.test_logger import *
from tests.test_config_validator import *


class TestRunner:
    """Custom test runner with enhanced reporting."""
    
    def __init__(self, verbosity=2):
        """Initialize test runner."""
        self.verbosity = verbosity
        self.test_modules = [
            'tests.test_backup',
            'tests.test_config', 
            'tests.test_notifications',
            'tests.test_remote_upload',
            'tests.test_logger',
            'tests.test_config_validator'
        ]
    
    def run_all_tests(self):
        """Run all test suites."""
        print("=" * 80)
        print("SQLBACKUP COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print()
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load tests from all modules
        for module_name in self.test_modules:
            try:
                module_tests = loader.loadTestsFromName(module_name)
                suite.addTests(module_tests)
                print(f"✓ Loaded tests from {module_name}")
            except Exception as e:
                print(f"✗ Failed to load tests from {module_name}: {e}")
        
        print()
        print("-" * 80)
        print("RUNNING TESTS")
        print("-" * 80)
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=self.verbosity,
            stream=sys.stdout,
            buffer=True
        )
        
        result = runner.run(suite)
        
        # Print summary
        print()
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print()
            print("FAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.splitlines()[-1] if traceback.splitlines() else 'Unknown'}")
        
        if result.errors:
            print()
            print("ERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.splitlines()[-1] if traceback.splitlines() else 'Unknown'}")
        
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        if result.wasSuccessful():
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed")
        
        print("=" * 80)
        
        return result.wasSuccessful()
    
    def run_module_tests(self, module_name):
        """Run tests for a specific module."""
        print(f"Running tests for {module_name}...")
        
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.test_{module_name}')
        
        runner = unittest.TextTestRunner(verbosity=self.verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    def discover_and_run(self, test_dir=None):
        """Discover and run all tests in directory."""
        if test_dir is None:
            test_dir = os.path.dirname(__file__)
        
        loader = unittest.TestLoader()
        suite = loader.discover(test_dir, pattern='test_*.py')
        
        runner = unittest.TextTestRunner(verbosity=self.verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()


def run_specific_test_class(test_class_name):
    """Run a specific test class."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Try to find the test class in all modules
    for module_name in ['test_backup', 'test_config', 'test_notifications', 
                       'test_remote_upload', 'test_logger', 'test_config_validator']:
        try:
            module = __import__(f'tests.{module_name}', fromlist=[test_class_name])
            if hasattr(module, test_class_name):
                test_class = getattr(module, test_class_name)
                suite.addTests(loader.loadTestsFromTestCase(test_class))
                break
        except ImportError:
            continue
    
    if suite.countTestCases() == 0:
        print(f"Test class '{test_class_name}' not found")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_coverage_analysis():
    """Run tests with coverage analysis if coverage.py is available."""
    try:
        import coverage
        
        print("Running tests with coverage analysis...")
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        test_runner = TestRunner(verbosity=1)
        success = test_runner.run_all_tests()
        
        # Stop coverage
        cov.stop()
        cov.save()
        
        print("\n" + "=" * 80)
        print("COVERAGE REPORT")
        print("=" * 80)
        
        # Generate coverage report
        cov.report(show_missing=True)
        
        # Generate HTML report if possible
        try:
            cov.html_report(directory='htmlcov')
            print("\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")
        
        return success
        
    except ImportError:
        print("Coverage.py not available. Install with: pip install coverage")
        print("Running tests without coverage analysis...")
        
        test_runner = TestRunner()
        return test_runner.run_all_tests()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='SqlBackup Test Runner')
    parser.add_argument('--module', help='Run tests for specific module (backup, config, notifications, etc.)')
    parser.add_argument('--class', dest='test_class', help='Run specific test class')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage analysis')
    parser.add_argument('--discover', action='store_true', help='Auto-discover and run all tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Set verbosity
    verbosity = 2 if args.verbose else 1
    
    success = False
    
    if args.coverage:
        success = run_coverage_analysis()
    elif args.module:
        test_runner = TestRunner(verbosity)
        success = test_runner.run_module_tests(args.module)
    elif args.test_class:
        success = run_specific_test_class(args.test_class)
    elif args.discover:
        test_runner = TestRunner(verbosity)
        success = test_runner.discover_and_run()
    else:
        # Default: run all tests
        test_runner = TestRunner(verbosity)
        success = test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

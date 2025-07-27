#!/usr/bin/env python3
"""
Comprehensive test suite for sqlBackup project

This package contains comprehensive tests for all modules:
- test_backup.py: Tests for backup functionality
- test_config.py: Tests for configuration management
- test_notifications.py: Tests for notification systems
- test_remote_upload.py: Tests for remote upload functionality
- test_logger.py: Tests for logging system
- test_config_validator.py: Tests for configuration validation
- run_tests.py: Test runner with enhanced reporting

Usage:
    # Run all tests
    python -m tests.run_tests
    
    # Run specific module tests
    python -m tests.run_tests --module backup
    
    # Run with coverage
    python -m tests.run_tests --coverage
    
    # Run specific test class
    python -m tests.run_tests --class TestMySQLBackup
"""

import os
import sys

# Add src to path for test imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_MODULES = [
    'tests.test_backup',
    'tests.test_config',
    'tests.test_notifications', 
    'tests.test_remote_upload',
    'tests.test_logger',
    'tests.test_config_validator'
]

__version__ = "1.0.0"
__author__ = "SqlBackup Development Team"

# Test statistics (updated when tests are run)
TOTAL_TESTS = 0
TOTAL_ASSERTIONS = 0
COVERAGE_TARGET = 90  # Target coverage percentage

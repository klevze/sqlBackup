# Testing Documentation

## Overview

This document provides comprehensive information about the test suite for the sqlBackup project. The test suite ensures code quality, reliability, and maintainability through extensive testing coverage.

## Test Structure

### Test Modules

1. **test_backup.py** - Tests for backup functionality
   - MySQLBackup class testing
   - Utility function testing
   - Integration testing with compression
   - Error handling and edge cases

2. **test_config.py** - Tests for configuration management
   - Config class testing
   - Configuration loading and validation
   - Edge cases and error conditions
   - Integration with validation system

3. **test_notifications.py** - Tests for notification systems
   - NotificationManager testing
   - All notification channels (Telegram, Email, Slack, SMS, Viber)
   - API integration testing with mocks
   - Error handling for network failures

4. **test_remote_upload.py** - Tests for remote upload functionality
   - RemoteUploader class testing
   - SFTP, FTP, and SCP protocol testing
   - Authentication methods (password, key file)
   - Connection error handling

5. **test_logger.py** - Tests for logging system
   - ColoredFormatter testing
   - SqlBackupLogger functionality
   - Log level configuration
   - File and console output testing

6. **test_config_validator.py** - Tests for configuration validation
   - ConfigValidator testing
   - Section-specific validation
   - Helper function testing
   - Error collection and reporting

## Running Tests

### Using Built-in Test Runner

The project includes a comprehensive test runner with enhanced reporting:

```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Run specific module tests
python tests/run_tests.py --module backup
python tests/run_tests.py --module config
python tests/run_tests.py --module notifications

# Run specific test class
python tests/run_tests.py --class TestMySQLBackup

# Run with coverage analysis (requires coverage.py)
python tests/run_tests.py --coverage

# Auto-discover and run tests
python tests/run_tests.py --discover
```

### Using unittest

Standard unittest runner:

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_backup

# Run specific test class
python -m unittest tests.test_backup.TestMySQLBackup

# Run specific test method
python -m unittest tests.test_backup.TestMySQLBackup.test_backup_creation

# Verbose output
python -m unittest discover tests -v
```

### Using pytest (if installed)

If pytest is installed, you can use it as an alternative:

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_backup.py

# Run with verbose output
pytest -v

# Run specific test method
pytest tests/test_backup.py::TestMySQLBackup::test_backup_creation
```

## Test Coverage

### Current Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%
- **Critical Modules**: 95%+ (backup, config, notifications)

### Coverage Reports

Generate coverage reports:

```bash
# Using built-in runner
python tests/run_tests.py --coverage

# Using coverage.py directly
pip install coverage
coverage run -m unittest discover tests
coverage report -m
coverage html  # Generates HTML report in htmlcov/
```

### Coverage by Module

| Module | Coverage | Critical |
|--------|----------|----------|
| backup.py | 95%+ | ✓ |
| config.py | 90%+ | ✓ |
| notifications.py | 85%+ | ✓ |
| remote_upload.py | 85%+ |  |
| logger.py | 80%+ |  |
| config_validator.py | 90%+ |  |

## Test Categories

### Unit Tests

Test individual functions and methods in isolation:

- Function parameter validation
- Return value verification
- Error condition handling
- Edge case testing

### Integration Tests

Test interaction between components:

- Configuration loading and validation
- Backup creation with notifications
- Remote upload with different protocols
- End-to-end backup workflows

### Mock Tests

Tests using mocks for external dependencies:

- Database connections
- Network requests (HTTP, SMTP, FTP)
- File system operations
- External APIs (Telegram, Slack, Twilio)

### Error Handling Tests

Tests for error conditions and recovery:

- Network failures
- Permission errors
- Invalid configurations
- Resource exhaustion

## Mock Usage

The test suite extensively uses mocks to isolate components and test error conditions:

### Database Mocking

```python
@patch('mysql.connector.connect')
def test_database_connection(self, mock_connect):
    mock_connect.return_value = MagicMock()
    # Test database operations
```

### Network Mocking

```python
@patch('requests.post')
def test_telegram_notification(self, mock_post):
    mock_post.return_value.status_code = 200
    # Test notification sending
```

### File System Mocking

```python
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
def test_file_operations(self, mock_exists, mock_file):
    # Test file operations
```

## Writing New Tests

### Test Structure

Follow this structure for new test files:

```python
#!/usr/bin/env python3
"""
Test module for [component_name]
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.module_name import ClassToTest


class TestClassName(unittest.TestCase):
    """Test [class/functionality] description."""
    
    def setUp(self):
        """Set up test environment."""
        # Initialize test data and mocks
        pass
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up resources
        pass
    
    def test_method_name(self):
        """Test [specific functionality]."""
        # Arrange
        # Act
        # Assert
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

### Test Naming Conventions

- Test files: `test_[module_name].py`
- Test classes: `Test[ClassName]`
- Test methods: `test_[functionality_description]`

### Assertion Guidelines

Use descriptive assertions:

```python
# Good
self.assertEqual(result.status, 'success')
self.assertIn('backup completed', result.message)
self.assertIsNotNone(backup_file)

# Add custom messages for clarity
self.assertTrue(file_exists, f"Backup file {backup_path} should exist")
```

### Mock Best Practices

1. **Patch at the right level**: Patch where the function is used, not where it's defined
2. **Use descriptive mock names**: `mock_connection`, `mock_response`
3. **Set up realistic mock responses**: Match actual API responses
4. **Test both success and failure cases**

### Test Data Management

Use temporary files and directories for test data:

```python
def setUp(self):
    self.test_dir = tempfile.mkdtemp()
    self.config_file = os.path.join(self.test_dir, 'test_config.ini')

def tearDown(self):
    shutil.rmtree(self.test_dir, ignore_errors=True)
```

## Continuous Integration

### Test Automation

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python tests/run_tests.py --coverage
```

### Quality Gates

- All tests must pass
- Coverage must be above 80%
- No critical security issues
- Code style compliance (if using linters)

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `src` directory is in Python path
   - Check for circular imports
   - Verify test file structure

2. **Mock Issues**
   - Patch at the correct import location
   - Set up mock return values correctly
   - Use `MagicMock` for complex objects

3. **File Permission Errors**
   - Use temporary directories for test files
   - Clean up resources in `tearDown()`
   - Handle cross-platform path differences

4. **Network-dependent Tests**
   - Always mock external network calls
   - Test both success and failure scenarios
   - Use realistic response data

### Debugging Tests

```python
# Add debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pdb for debugging
import pdb; pdb.set_trace()

# Print mock call information
print(mock_function.call_args_list)
```

## Performance Testing

### Test Execution Time

Monitor test execution time:

```bash
# Show slowest tests
python tests/run_tests.py --verbose
pytest --durations=10
```

### Memory Usage

For memory-intensive operations:

```python
import tracemalloc

def test_memory_usage(self):
    tracemalloc.start()
    # Run memory-intensive operation
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Assert memory usage is reasonable
```

## Test Maintenance

### Regular Tasks

1. **Update test data** when adding new features
2. **Review mock setups** when external APIs change
3. **Update coverage targets** as codebase grows
4. **Refactor common test utilities** to reduce duplication

### Best Practices

- Keep tests simple and focused
- Test one thing at a time
- Use descriptive test names
- Maintain test independence
- Regular cleanup of obsolete tests

## Dependencies

### Required for Testing

- Python 3.6+
- unittest (built-in)
- tempfile (built-in)
- os, sys (built-in)

### Optional but Recommended

- `coverage` - For coverage analysis
- `pytest` - Alternative test runner
- `pytest-cov` - Coverage integration for pytest
- `mock` (Python < 3.3)

### Installation

```bash
# Basic testing
# No additional packages required

# Enhanced testing
pip install coverage pytest pytest-cov

# For development
pip install pytest pytest-cov coverage pytest-mock pytest-xdist
```

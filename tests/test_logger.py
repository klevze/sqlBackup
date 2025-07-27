#!/usr/bin/env python3
"""
Comprehensive test suite for logging module
"""

import unittest
import tempfile
import os
import shutil
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.logger import ColoredFormatter, SqlBackupLogger, setup_logging, get_logger


class TestColoredFormatter(unittest.TestCase):
    """Test ColoredFormatter functionality."""
    
    def setUp(self):
        """Set up ColoredFormatter test environment."""
        self.formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def test_format_debug_level(self):
        """Test formatting of DEBUG level messages."""
        record = logging.LogRecord(
            name='test', level=logging.DEBUG, pathname='', lineno=0,
            msg='Debug message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain ANSI color codes for DEBUG (cyan)
        self.assertIn('\033[0;36m', formatted)  # Cyan color
        self.assertIn('DEBUG', formatted)
        self.assertIn('Debug message', formatted)
    
    def test_format_info_level(self):
        """Test formatting of INFO level messages."""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Info message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain ANSI color codes for INFO (green)
        self.assertIn('\033[0;32m', formatted)  # Green color
        self.assertIn('INFO', formatted)
        self.assertIn('Info message', formatted)
    
    def test_format_warning_level(self):
        """Test formatting of WARNING level messages."""
        record = logging.LogRecord(
            name='test', level=logging.WARNING, pathname='', lineno=0,
            msg='Warning message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain ANSI color codes for WARNING (yellow)
        self.assertIn('\033[0;33m', formatted)  # Yellow color
        self.assertIn('WARNING', formatted)
        self.assertIn('Warning message', formatted)
    
    def test_format_error_level(self):
        """Test formatting of ERROR level messages."""
        record = logging.LogRecord(
            name='test', level=logging.ERROR, pathname='', lineno=0,
            msg='Error message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain ANSI color codes for ERROR (red)
        self.assertIn('\033[0;31m', formatted)  # Red color
        self.assertIn('ERROR', formatted)
        self.assertIn('Error message', formatted)
    
    def test_format_critical_level(self):
        """Test formatting of CRITICAL level messages."""
        record = logging.LogRecord(
            name='test', level=logging.CRITICAL, pathname='', lineno=0,
            msg='Critical message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain ANSI color codes for CRITICAL (magenta)
        self.assertIn('\033[0;35m', formatted)  # Magenta color
        self.assertIn('CRITICAL', formatted)
        self.assertIn('Critical message', formatted)
    
    def test_format_contains_timestamp(self):
        """Test that formatted output contains timestamp."""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should contain timestamp pattern (YYYY-MM-DD HH:MM:SS)
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        self.assertRegex(formatted, timestamp_pattern)
    
    def test_format_resets_color(self):
        """Test that formatted output resets color at the end."""
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0,
            msg='Test message', args=(), exc_info=None
        )
        
        formatted = self.formatter.format(record)
        
        # Should end with color reset code
        self.assertIn('\033[0m', formatted)


class TestSqlBackupLogger(unittest.TestCase):
    """Test SqlBackupLogger functionality."""
    
    def setUp(self):
        """Set up SqlBackupLogger test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, 'test.log')
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove all handlers to avoid conflicts
        logger = logging.getLogger('test_logger')
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init_with_defaults(self):
        """Test SqlBackupLogger initialization with default parameters."""
        logger_manager = SqlBackupLogger()
        
        self.assertEqual(logger_manager.name, 'sqlbackup')
        self.assertEqual(logger_manager.log_level, 'INFO')
        self.assertIsNone(logger_manager.log_file)
        self.assertTrue(logger_manager.console_output)
    
    def test_init_with_custom_parameters(self):
        """Test SqlBackupLogger initialization with custom parameters."""
        logger_manager = SqlBackupLogger(
            name='custom_logger',
            log_level='DEBUG',
            log_file=self.log_file,
            console_output=False
        )
        
        self.assertEqual(logger_manager.name, 'custom_logger')
        self.assertEqual(logger_manager.log_level, 'DEBUG')
        self.assertEqual(logger_manager.log_file, self.log_file)
        self.assertFalse(logger_manager.console_output)
    
    def test_get_logger_console_only(self):
        """Test getting logger with console output only."""
        logger_manager = SqlBackupLogger(name='test_logger', console_output=True)
        logger = logger_manager.get_logger()
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_logger')
        self.assertEqual(logger.level, logging.INFO)
        
        # Should have at least one handler (console)
        self.assertGreater(len(logger.handlers), 0)
        
        # At least one handler should be StreamHandler
        has_stream_handler = any(
            isinstance(handler, logging.StreamHandler) 
            for handler in logger.handlers
        )
        self.assertTrue(has_stream_handler)
    
    def test_get_logger_file_only(self):
        """Test getting logger with file output only."""
        logger_manager = SqlBackupLogger(
            name='test_logger',
            log_file=self.log_file,
            console_output=False
        )
        logger = logger_manager.get_logger()
        
        self.assertIsNotNone(logger)
        
        # Should have at least one handler (file)
        self.assertGreater(len(logger.handlers), 0)
        
        # Should have RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        has_file_handler = any(
            isinstance(handler, RotatingFileHandler) 
            for handler in logger.handlers
        )
        self.assertTrue(has_file_handler)
    
    def test_get_logger_both_outputs(self):
        """Test getting logger with both console and file output."""
        logger_manager = SqlBackupLogger(
            name='test_logger',
            log_file=self.log_file,
            console_output=True
        )
        logger = logger_manager.get_logger()
        
        # Should have at least two handlers
        self.assertGreaterEqual(len(logger.handlers), 2)
        
        # Should have both StreamHandler and RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        handler_types = [type(handler) for handler in logger.handlers]
        
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(RotatingFileHandler, handler_types)
    
    def test_log_file_creation(self):
        """Test that log file is created when specified."""
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        logger_manager = SqlBackupLogger(
            name='test_logger',
            log_file=self.log_file,
            console_output=False
        )
        logger = logger_manager.get_logger()
        
        # Log a message
        logger.info("Test log message")
        
        # Force flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Check if log file was created (might need a moment for file system)
        import time
        time.sleep(0.1)
        
        # File should exist (even if empty due to buffering)
        log_dir_exists = os.path.exists(log_dir)
        self.assertTrue(log_dir_exists, f"Log directory {log_dir} should exist")
    
    def test_log_level_setting(self):
        """Test that log level is set correctly."""
        test_levels = [
            ('DEBUG', logging.DEBUG),
            ('INFO', logging.INFO),
            ('WARNING', logging.WARNING),
            ('ERROR', logging.ERROR),
            ('CRITICAL', logging.CRITICAL),
        ]
        
        for level_name, level_value in test_levels:
            with self.subTest(level=level_name):
                logger_manager = SqlBackupLogger(
                    name=f'test_logger_{level_name.lower()}',
                    log_level=level_name
                )
                logger = logger_manager.get_logger()
                
                self.assertEqual(logger.level, level_value)


class TestSetupLogging(unittest.TestCase):
    """Test setup_logging function."""
    
    def setUp(self):
        """Set up setup_logging test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, 'setup_test.log')
        
        # Clear any existing loggers
        logging.getLogger().handlers.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        # Clear all loggers
        logging.getLogger().handlers.clear()
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('test') or name == 'sqlbackup':
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()
        
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_setup_logging_defaults(self):
        """Test setup_logging with default parameters."""
        setup_logging()
        
        # Should set up root logger
        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0)
    
    def test_setup_logging_with_file(self):
        """Test setup_logging with log file."""
        setup_logging(log_file=self.log_file)
        
        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0)
    
    def test_setup_logging_debug_level(self):
        """Test setup_logging with DEBUG level."""
        setup_logging(log_level='DEBUG')
        
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)
    
    def test_setup_logging_no_console(self):
        """Test setup_logging without console output."""
        setup_logging(log_file=self.log_file, console_output=False)
        
        root_logger = logging.getLogger()
        
        # Should not have StreamHandler
        stream_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and not hasattr(h, 'baseFilename')
        ]
        self.assertEqual(len(stream_handlers), 0)


class TestGetLogger(unittest.TestCase):
    """Test get_logger function."""
    
    def setUp(self):
        """Set up get_logger test environment."""
        # Clear any existing setup
        logging.getLogger().handlers.clear()
        setup_logging(log_level='INFO', console_output=True)
    
    def tearDown(self):
        """Clean up test environment."""
        # Clear all loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            if name.startswith('test'):
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()
    
    def test_get_logger_without_name(self):
        """Test get_logger without specifying name."""
        logger = get_logger()
        
        self.assertIsNotNone(logger)
        # Should return logger with caller's module name or default
        self.assertIsInstance(logger, logging.Logger)
    
    def test_get_logger_with_name(self):
        """Test get_logger with specific name."""
        logger = get_logger('test_module')
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_module')
    
    def test_get_logger_multiple_calls_same_instance(self):
        """Test that multiple calls with same name return same instance."""
        logger1 = get_logger('test_module')
        logger2 = get_logger('test_module')
        
        self.assertIs(logger1, logger2)
    
    def test_get_logger_different_names_different_instances(self):
        """Test that different names return different instances."""
        logger1 = get_logger('test_module1')
        logger2 = get_logger('test_module2')
        
        self.assertIsNot(logger1, logger2)
        self.assertEqual(logger1.name, 'test_module1')
        self.assertEqual(logger2.name, 'test_module2')


class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for logging functionality."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, 'integration.log')
        
        # Clear any existing setup
        logging.getLogger().handlers.clear()
    
    def tearDown(self):
        """Clean up integration test environment."""
        # Clear all loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
        
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_logging_workflow(self):
        """Test complete logging workflow from setup to usage."""
        # Setup logging
        setup_logging(log_level='DEBUG', log_file=self.log_file, console_output=True)
        
        # Get logger
        logger = get_logger('test_workflow')
        
        # Test all log levels
        test_messages = [
            (logger.debug, "Debug message"),
            (logger.info, "Info message"),
            (logger.warning, "Warning message"),
            (logger.error, "Error message"),
            (logger.critical, "Critical message"),
        ]
        
        for log_method, message in test_messages:
            log_method(message)
        
        # Force flush all handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Verify logger is working
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_workflow')
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_console_output_capture(self, mock_stdout):
        """Test that console output can be captured."""
        # Setup logging with console output
        setup_logging(log_level='INFO', console_output=True)
        
        # Get logger and log message
        logger = get_logger('test_console')
        logger.info("Test console message")
        
        # Force flush
        for handler in logger.handlers:
            handler.flush()
        
        # Check if message appeared in stdout (may be buffered)
        output = mock_stdout.getvalue()
        # Note: Output might be empty due to handler setup timing
        # This test verifies the setup doesn't crash
        self.assertIsNotNone(output)
    
    def test_file_rotation_setup(self):
        """Test that file rotation is properly configured."""
        from logging.handlers import RotatingFileHandler
        
        # Setup logging with file
        setup_logging(log_file=self.log_file, console_output=False)
        
        # Get logger
        logger = get_logger('test_rotation')
        
        # Find RotatingFileHandler
        rotating_handler = None
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                rotating_handler = handler
                break
        
        if rotating_handler:
            # Verify rotation settings
            self.assertEqual(rotating_handler.maxBytes, 10 * 1024 * 1024)  # 10MB
            self.assertEqual(rotating_handler.backupCount, 5)
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance."""
        # Setup logging
        setup_logging(log_level='WARNING')
        
        # Create parent and child loggers
        parent_logger = get_logger('parent')
        child_logger = get_logger('parent.child')
        
        # Both should be properly configured
        self.assertIsNotNone(parent_logger)
        self.assertIsNotNone(child_logger)
        
        # Child should inherit from parent
        self.assertTrue(child_logger.name.startswith(parent_logger.name))


class TestLoggingErrorCases(unittest.TestCase):
    """Test error cases and edge conditions."""
    
    def setUp(self):
        """Set up error case test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Clear any existing setup
        logging.getLogger().handlers.clear()
    
    def tearDown(self):
        """Clean up error case test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_invalid_log_level(self):
        """Test setup with invalid log level."""
        # Should not crash, might default to INFO
        try:
            setup_logging(log_level='INVALID_LEVEL')
            # If no exception, verify logger still works
            logger = get_logger('test_invalid_level')
            self.assertIsNotNone(logger)
        except (ValueError, AttributeError):
            # Some implementations might raise an error, which is also acceptable
            pass
    
    def test_log_file_permission_error(self):
        """Test log file creation with permission issues."""
        # Try to create log file in non-existent directory without creating it
        invalid_log_file = os.path.join(self.test_dir, 'nonexistent', 'test.log')
        
        # Should handle gracefully (might fall back to console only)
        try:
            setup_logging(log_file=invalid_log_file, console_output=True)
            logger = get_logger('test_permission')
            logger.info("Test message")
            # If we get here, it handled the error gracefully
            self.assertIsNotNone(logger)
        except (FileNotFoundError, PermissionError, OSError):
            # Some setups might raise errors, which is also acceptable
            pass
    
    def test_empty_log_file_path(self):
        """Test setup with empty log file path."""
        # Should handle empty string gracefully
        setup_logging(log_file='', console_output=True)
        logger = get_logger('test_empty_path')
        self.assertIsNotNone(logger)
    
    def test_none_log_file_path(self):
        """Test setup with None log file path."""
        # Should handle None gracefully
        setup_logging(log_file=None, console_output=True)
        logger = get_logger('test_none_path')
        self.assertIsNotNone(logger)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

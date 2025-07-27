#!/usr/bin/env python3
"""
Comprehensive test suite for config module
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
import configparser

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.config import Config


class TestConfig(unittest.TestCase):
    """Comprehensive tests for Config class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.ini')
        
        # Mock logger to avoid file creation during tests
        self.logger_patcher = patch('src.config.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_config(self, content=None):
        """Create test configuration file."""
        if content is None:
            content = """
[backup]
backup_dir = /tmp/backups
keep_days = 7
archive_type = gz

[mysql]
user = test_user
password = test_password
host = localhost
port = 3306
database = test_db

[telegram]
enabled = true
bot_token = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
chat_id = 987654321

[email]
enabled = false
smtp_server = smtp.gmail.com
smtp_port = 587
sender_email = test@example.com
sender_password = app_password
recipient_email = admin@example.com

[slack]
enabled = false
webhook_url = https://hooks.slack.com/services/test

[sms]
enabled = false
twilio_account_sid = ACtest123
twilio_auth_token = test_token
from_phone = +1234567890
to_phone = +0987654321

[viber]
enabled = false
auth_token = viber_token
receiver_id = viber_user

[messenger]
enabled = false
access_token = messenger_token
recipient_id = messenger_user

[notification]
channels = telegram

[export]
enabled = true
export_type = sftp
server = backup.example.com
username = backup_user
password = backup_password
remote_path = /backups

[logging]
level = INFO
file = logs/backup.log
"""
        
        with open(self.config_file, 'w') as f:
            f.write(content)
    
    def test_init_with_default_path(self):
        """Test initialization with default config path."""
        with patch('os.path.exists', return_value=True):
            config = Config()
            self.assertEqual(config.config_path, 'config.ini')
    
    def test_init_with_custom_path(self):
        """Test initialization with custom config path."""
        config = Config(self.config_file)
        self.assertEqual(config.config_path, self.config_file)
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        # Check that config is loaded
        self.assertIsNotNone(config.config)
        self.assertTrue(config.config.has_section('backup'))
        self.assertTrue(config.config.has_section('mysql'))
    
    def test_load_config_file_not_found(self):
        """Test configuration loading with nonexistent file."""
        config = Config('/nonexistent/config.ini')
        
        with self.assertRaises(FileNotFoundError):
            config.load_config()
    
    def test_load_config_invalid_format(self):
        """Test configuration loading with invalid format."""
        # Create invalid config file
        with open(self.config_file, 'w') as f:
            f.write("invalid config content\nno sections\n")
        
        config = Config(self.config_file)
        
        with self.assertRaises(configparser.Error):
            config.load_config()
    
    def test_get_existing_value(self):
        """Test getting existing configuration value."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.get('backup', 'backup_dir')
        self.assertEqual(value, '/tmp/backups')
    
    def test_get_with_fallback(self):
        """Test getting configuration value with fallback."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.get('backup', 'nonexistent_key', 'default_value')
        self.assertEqual(value, 'default_value')
    
    def test_get_nonexistent_section(self):
        """Test getting value from nonexistent section."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.get('nonexistent_section', 'key', 'default')
        self.assertEqual(value, 'default')
    
    def test_getboolean_true_values(self):
        """Test getting boolean values that should be True."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        # Test various true representations
        test_cases = [
            ('telegram', 'enabled'),  # 'true' in config
        ]
        
        for section, key in test_cases:
            with self.subTest(section=section, key=key):
                value = config.getboolean(section, key)
                self.assertTrue(value)
    
    def test_getboolean_false_values(self):
        """Test getting boolean values that should be False."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getboolean('email', 'enabled')
        self.assertFalse(value)
    
    def test_getboolean_with_fallback(self):
        """Test getting boolean value with fallback."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getboolean('backup', 'nonexistent_key', True)
        self.assertTrue(value)
        
        value = config.getboolean('nonexistent_section', 'key', False)
        self.assertFalse(value)
    
    def test_getint_valid_values(self):
        """Test getting integer values."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        port = config.getint('mysql', 'port')
        self.assertEqual(port, 3306)
        
        keep_days = config.getint('backup', 'keep_days')
        self.assertEqual(keep_days, 7)
    
    def test_getint_with_fallback(self):
        """Test getting integer value with fallback."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getint('backup', 'nonexistent_key', 42)
        self.assertEqual(value, 42)
        
        value = config.getint('nonexistent_section', 'key', 100)
        self.assertEqual(value, 100)
    
    def test_getint_invalid_value(self):
        """Test getting integer value from non-integer string."""
        config_content = """
[test]
invalid_int = not_a_number
"""
        self._create_test_config(config_content)
        config = Config(self.config_file)
        config.load_config()
        
        # Should return fallback when conversion fails
        value = config.getint('test', 'invalid_int', 0)
        self.assertEqual(value, 0)
    
    def test_getfloat_valid_values(self):
        """Test getting float values."""
        config_content = """
[test]
float_value = 3.14
int_as_float = 42
"""
        self._create_test_config(config_content)
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getfloat('test', 'float_value')
        self.assertEqual(value, 3.14)
        
        value = config.getfloat('test', 'int_as_float')
        self.assertEqual(value, 42.0)
    
    def test_getfloat_with_fallback(self):
        """Test getting float value with fallback."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getfloat('backup', 'nonexistent_key', 1.5)
        self.assertEqual(value, 1.5)
    
    def test_getfloat_invalid_value(self):
        """Test getting float value from non-float string."""
        config_content = """
[test]
invalid_float = not_a_number
"""
        self._create_test_config(config_content)
        config = Config(self.config_file)
        config.load_config()
        
        value = config.getfloat('test', 'invalid_float', 0.0)
        self.assertEqual(value, 0.0)
    
    def test_getlist_comma_separated(self):
        """Test getting list from comma-separated values."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        # Test single value
        channels = config.getlist('notification', 'channels')
        self.assertEqual(channels, ['telegram'])
        
        # Test multiple values
        config_content = """
[test]
multi_values = value1, value2, value3
spaced_values = item1 , item2 , item3
"""
        self._create_test_config(config_content)
        config.load_config()
        
        values = config.getlist('test', 'multi_values')
        self.assertEqual(values, ['value1', 'value2', 'value3'])
        
        values = config.getlist('test', 'spaced_values')
        self.assertEqual(values, ['item1', 'item2', 'item3'])
    
    def test_getlist_empty_values(self):
        """Test getting list from empty or whitespace values."""
        config_content = """
[test]
empty_value = 
whitespace_value =    
"""
        self._create_test_config(config_content)
        config = Config(self.config_file)
        config.load_config()
        
        values = config.getlist('test', 'empty_value')
        self.assertEqual(values, [])
        
        values = config.getlist('test', 'whitespace_value')
        self.assertEqual(values, [])
    
    def test_getlist_with_fallback(self):
        """Test getting list value with fallback."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        values = config.getlist('backup', 'nonexistent_key', ['default1', 'default2'])
        self.assertEqual(values, ['default1', 'default2'])
        
        values = config.getlist('nonexistent_section', 'key', [])
        self.assertEqual(values, [])
    
    def test_config_sections_present(self):
        """Test that all required sections are present."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        required_sections = [
            'backup', 'mysql', 'telegram', 'email', 'slack', 
            'sms', 'viber', 'messenger', 'notification', 'export'
        ]
        
        for section in required_sections:
            with self.subTest(section=section):
                self.assertTrue(config.config.has_section(section))
    
    def test_mysql_configuration(self):
        """Test MySQL-specific configuration."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        self.assertEqual(config.get('mysql', 'user'), 'test_user')
        self.assertEqual(config.get('mysql', 'password'), 'test_password')
        self.assertEqual(config.get('mysql', 'host'), 'localhost')
        self.assertEqual(config.getint('mysql', 'port'), 3306)
        self.assertEqual(config.get('mysql', 'database'), 'test_db')
    
    def test_notification_configuration(self):
        """Test notification configuration."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        # Telegram
        self.assertTrue(config.getboolean('telegram', 'enabled'))
        self.assertEqual(config.get('telegram', 'bot_token'), 
                        '123456789:ABCdefGHIjklMNOpqrsTUVwxyz')
        self.assertEqual(config.get('telegram', 'chat_id'), '987654321')
        
        # Email
        self.assertFalse(config.getboolean('email', 'enabled'))
        self.assertEqual(config.get('email', 'smtp_server'), 'smtp.gmail.com')
        self.assertEqual(config.getint('email', 'smtp_port'), 587)
        
        # Notification channels
        channels = config.getlist('notification', 'channels')
        self.assertEqual(channels, ['telegram'])
    
    def test_export_configuration(self):
        """Test export/upload configuration."""
        self._create_test_config()
        config = Config(self.config_file)
        config.load_config()
        
        self.assertTrue(config.getboolean('export', 'enabled'))
        self.assertEqual(config.get('export', 'export_type'), 'sftp')
        self.assertEqual(config.get('export', 'server'), 'backup.example.com')
        self.assertEqual(config.get('export', 'username'), 'backup_user')
        self.assertEqual(config.get('export', 'remote_path'), '/backups')


class TestConfigWithValidation(unittest.TestCase):
    """Test Config class with validation integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'validation_test.ini')
        
        # Mock logger
        self.logger_patcher = patch('src.config.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_config_with_validation(self):
        """Test configuration loading with validation."""
        # Create valid config
        config_content = """
[backup]
backup_dir = /tmp/backups
keep_days = 7
archive_type = gz

[mysql]
user = test_user
password = test_password
host = localhost
port = 3306
database = test_db

[notification]
channels = 
"""
        
        with open(self.config_file, 'w') as f:
            f.write(config_content)
        
        with patch('src.config_validator.ConfigValidator') as mock_validator:
            mock_validator.return_value.validate_configuration.return_value = (True, [], [])
            
            config = Config(self.config_file)
            config.load_config()
            
            # Verify validation was called
            mock_validator.assert_called_once_with(self.config_file)
            mock_validator.return_value.validate_configuration.assert_called_once()
    
    def test_load_config_validation_failure(self):
        """Test configuration loading with validation failure."""
        # Create invalid config
        config_content = """
[backup]
backup_dir = /nonexistent/directory

[mysql]
# Missing required fields
"""
        
        with open(self.config_file, 'w') as f:
            f.write(config_content)
        
        with patch('src.config_validator.ConfigValidator') as mock_validator:
            mock_validator.return_value.validate_configuration.return_value = (
                False, 
                ['MySQL user not specified', 'Backup directory does not exist'], 
                ['No notification channels configured']
            )
            
            config = Config(self.config_file)
            
            with self.assertRaises(ValueError):
                config.load_config()


class TestConfigEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock logger
        self.logger_patcher = patch('src.config.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters in config."""
        config_file = os.path.join(self.test_dir, 'unicode_config.ini')
        config_content = """
[test]
unicode_value = Test with unicode: ñáéíóú 中文 🚀
emoji_value = Backup completed! ✅
"""
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        config = Config(config_file)
        config.load_config()
        
        unicode_val = config.get('test', 'unicode_value')
        self.assertIn('ñáéíóú', unicode_val)
        self.assertIn('中文', unicode_val)
        self.assertIn('🚀', unicode_val)
        
        emoji_val = config.get('test', 'emoji_value')
        self.assertIn('✅', emoji_val)
    
    def test_special_characters_in_values(self):
        """Test handling of special characters in configuration values."""
        config_file = os.path.join(self.test_dir, 'special_config.ini')
        config_content = """
[test]
password_with_special = P@ssw0rd!#$%^&*()
path_with_spaces = /path/with spaces/backup
url_with_params = https://example.com/webhook?token=abc123&format=json
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        config = Config(config_file)
        config.load_config()
        
        password = config.get('test', 'password_with_special')
        self.assertEqual(password, 'P@ssw0rd!#$%^&*()')
        
        path = config.get('test', 'path_with_spaces')
        self.assertEqual(path, '/path/with spaces/backup')
        
        url = config.get('test', 'url_with_params')
        self.assertEqual(url, 'https://example.com/webhook?token=abc123&format=json')
    
    def test_empty_config_file(self):
        """Test handling of empty configuration file."""
        config_file = os.path.join(self.test_dir, 'empty_config.ini')
        with open(config_file, 'w') as f:
            f.write('')
        
        config = Config(config_file)
        config.load_config()
        
        # Should handle empty file gracefully
        value = config.get('nonexistent', 'key', 'default')
        self.assertEqual(value, 'default')
    
    def test_config_with_comments(self):
        """Test configuration file with comments."""
        config_file = os.path.join(self.test_dir, 'commented_config.ini')
        config_content = """
# This is a comment
[backup]
backup_dir = /tmp/backups  # Inline comment
# Another comment
keep_days = 7

; Semicolon comment
[mysql]
user = test_user ; Another inline comment
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        config = Config(config_file)
        config.load_config()
        
        backup_dir = config.get('backup', 'backup_dir')
        self.assertEqual(backup_dir, '/tmp/backups')
        
        user = config.get('mysql', 'user')
        self.assertEqual(user, 'test_user')


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""
Comprehensive test suite for configuration validator module
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.config_validator import (
    ConfigValidator, ValidationError, DatabaseConfig, 
    NotificationConfig, RemoteUploadConfig, ArchiveConfig,
    validate_email_format, validate_telegram_token, validate_file_path,
    validate_database_connection
)


class TestValidationError(unittest.TestCase):
    """Test ValidationError exception class."""
    
    def test_validation_error_creation(self):
        """Test ValidationError can be created with message."""
        error = ValidationError("Test error message")
        self.assertEqual(str(error), "Test error message")
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from Exception."""
        error = ValidationError("Test error")
        self.assertIsInstance(error, Exception)


class TestValidationHelpers(unittest.TestCase):
    """Test validation helper functions."""
    
    def test_validate_email_format_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "123@test.com",
            "test@subdomain.example.com"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                # Should not raise exception
                validate_email_format(email)
    
    def test_validate_email_format_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@.com",
            "",
            None
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    validate_email_format(email)
    
    def test_validate_telegram_token_valid(self):
        """Test Telegram token validation with valid tokens."""
        valid_tokens = [
            "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            "987654321:XYZabcDEFghiJKLmnoPQRstuv",
            "555555555:AABBCCDDEEFFGGHHIIJJKKLLmm"
        ]
        
        for token in valid_tokens:
            with self.subTest(token=token):
                # Should not raise exception
                validate_telegram_token(token)
    
    def test_validate_telegram_token_invalid(self):
        """Test Telegram token validation with invalid tokens."""
        invalid_tokens = [
            "invalid_token",
            "123456789",
            ":ABCdefGHIjklMNOpqrsTUVwxyz",
            "123456789:",
            "12345678:SHORT",
            "",
            None
        ]
        
        for token in invalid_tokens:
            with self.subTest(token=token):
                with self.assertRaises(ValidationError):
                    validate_telegram_token(token)
    
    def test_validate_file_path_existing(self):
        """Test file path validation with existing files."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Should not raise exception for existing file
            validate_file_path(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_path_nonexistent(self):
        """Test file path validation with non-existent files."""
        non_existent_path = "/path/that/does/not/exist/file.txt"
        
        with self.assertRaises(ValidationError):
            validate_file_path(non_existent_path)
    
    def test_validate_file_path_directory(self):
        """Test file path validation with directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValidationError):
                validate_file_path(temp_dir)
    
    @patch('mysql.connector.connect')
    def test_validate_database_connection_success(self, mock_connect):
        """Test database connection validation with successful connection."""
        # Mock successful connection
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection
        
        config = {
            'host': 'localhost',
            'port': '3306',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        # Should not raise exception
        validate_database_connection(config)
        
        # Verify connection was attempted
        mock_connect.assert_called_once_with(
            host='localhost',
            port=3306,
            user='testuser',
            password='testpass',
            database='testdb'
        )
        mock_connection.close.assert_called_once()
    
    @patch('mysql.connector.connect')
    def test_validate_database_connection_failure(self, mock_connect):
        """Test database connection validation with connection failure."""
        # Mock connection failure
        try:
            import mysql.connector.errors
            mock_connect.side_effect = mysql.connector.errors.DatabaseError("Connection failed")
        except ImportError:
            # If mysql.connector is not available, use generic Exception
            mock_connect.side_effect = Exception("Connection failed")
        
        config = {
            'host': 'invalid',
            'port': '3306',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        with self.assertRaises(ValidationError):
            validate_database_connection(config)


class TestDatabaseConfig(unittest.TestCase):
    """Test DatabaseConfig validation."""
    
    def test_database_config_valid(self):
        """Test DatabaseConfig with valid configuration."""
        config = {
            'host': 'localhost',
            'port': '3306',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        # Should not raise exception
        db_config = DatabaseConfig(config)
        self.assertEqual(db_config.config, config)
    
    def test_database_config_missing_required(self):
        """Test DatabaseConfig with missing required fields."""
        incomplete_configs = [
            {'host': 'localhost', 'port': '3306'},  # Missing user, password, database
            {'user': 'testuser', 'password': 'testpass'},  # Missing host, port, database
            {'database': 'testdb'},  # Missing host, port, user, password
            {}  # Missing everything
        ]
        
        for config in incomplete_configs:
            with self.subTest(config=config):
                with self.assertRaises(ValidationError):
                    DatabaseConfig(config)
    
    def test_database_config_invalid_port(self):
        """Test DatabaseConfig with invalid port."""
        invalid_ports = ['invalid', '-1', '0', '65536', '999999']
        
        for port in invalid_ports:
            with self.subTest(port=port):
                config = {
                    'host': 'localhost',
                    'port': port,
                    'user': 'testuser',
                    'password': 'testpass',
                    'database': 'testdb'
                }
                
                with self.assertRaises(ValidationError):
                    DatabaseConfig(config)
    
    def test_database_config_empty_values(self):
        """Test DatabaseConfig with empty required values."""
        config = {
            'host': '',
            'port': '3306',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        with self.assertRaises(ValidationError):
            DatabaseConfig(config)
    
    @patch('src.config_validator.validate_database_connection')
    def test_database_config_with_connection_test(self, mock_validate_connection):
        """Test DatabaseConfig with connection testing enabled."""
        config = {
            'host': 'localhost',
            'port': '3306',
            'user': 'testuser',
            'password': 'testpass',
            'database': 'testdb'
        }
        
        # Should call connection validation
        db_config = DatabaseConfig(config, test_connection=True)
        
        mock_validate_connection.assert_called_once_with(config)


class TestNotificationConfig(unittest.TestCase):
    """Test NotificationConfig validation."""
    
    def test_notification_config_telegram_valid(self):
        """Test NotificationConfig with valid Telegram configuration."""
        config = {
            'telegram_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
            'telegram_chat_id': '123456789'
        }
        
        # Should not raise exception
        notification_config = NotificationConfig(config)
        self.assertEqual(notification_config.config, config)
    
    def test_notification_config_email_valid(self):
        """Test NotificationConfig with valid email configuration."""
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'smtp_username': 'test@gmail.com',
            'smtp_password': 'password',
            'email_from': 'test@gmail.com',
            'email_to': 'recipient@gmail.com'
        }
        
        # Should not raise exception
        notification_config = NotificationConfig(config)
        self.assertEqual(notification_config.config, config)
    
    def test_notification_config_slack_valid(self):
        """Test NotificationConfig with valid Slack configuration (uses dummy URL, not a real secret)."""
        config = {
            # Dummy value, not a real Slack webhook
            'slack_webhook_url': 'https://hooks.slack.com/services/FAKE/WEBHOOK/URL'
        }

        # Should not raise exception
        notification_config = NotificationConfig(config)
        self.assertEqual(notification_config.config, config)
    
    def test_notification_config_sms_valid(self):
        """Test NotificationConfig with valid SMS configuration."""
        config = {
            'twilio_account_sid': 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'twilio_auth_token': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            'sms_from': '+1234567890',
            'sms_to': '+0987654321'
        }
        
        # Should not raise exception
        notification_config = NotificationConfig(config)
        self.assertEqual(notification_config.config, config)
    
    def test_notification_config_telegram_invalid_token(self):
        """Test NotificationConfig with invalid Telegram token."""
        config = {
            'telegram_token': 'invalid_token',
            'telegram_chat_id': '123456789'
        }
        
        with self.assertRaises(ValidationError):
            NotificationConfig(config)
    
    def test_notification_config_email_invalid(self):
        """Test NotificationConfig with invalid email configuration."""
        invalid_configs = [
            # Invalid email format
            {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587',
                'smtp_username': 'test@gmail.com',
                'smtp_password': 'password',
                'email_from': 'invalid_email',
                'email_to': 'recipient@gmail.com'
            },
            # Invalid port
            {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 'invalid',
                'smtp_username': 'test@gmail.com',
                'smtp_password': 'password',
                'email_from': 'test@gmail.com',
                'email_to': 'recipient@gmail.com'
            },
            # Missing required fields
            {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587'
                # Missing other required fields
            }
        ]
        
        for config in invalid_configs:
            with self.subTest(config=config):
                with self.assertRaises(ValidationError):
                    NotificationConfig(config)
    
    def test_notification_config_empty(self):
        """Test NotificationConfig with empty configuration."""
        # Empty config should be valid (notifications optional)
        config = {}
        
        notification_config = NotificationConfig(config)
        self.assertEqual(notification_config.config, config)


class TestRemoteUploadConfig(unittest.TestCase):
    """Test RemoteUploadConfig validation."""
    
    def test_remote_upload_config_sftp_valid(self):
        """Test RemoteUploadConfig with valid SFTP configuration."""
        config = {
            'remote_host': 'sftp.example.com',
            'remote_user': 'testuser',
            'remote_password': 'testpass',
            'remote_path': '/backup/',
            'upload_method': 'sftp'
        }
        
        # Should not raise exception
        remote_config = RemoteUploadConfig(config)
        self.assertEqual(remote_config.config, config)
    
    def test_remote_upload_config_ftp_valid(self):
        """Test RemoteUploadConfig with valid FTP configuration."""
        config = {
            'remote_host': 'ftp.example.com',
            'remote_user': 'testuser',
            'remote_password': 'testpass',
            'remote_path': '/backup/',
            'upload_method': 'ftp'
        }
        
        # Should not raise exception
        remote_config = RemoteUploadConfig(config)
        self.assertEqual(remote_config.config, config)
    
    def test_remote_upload_config_scp_valid(self):
        """Test RemoteUploadConfig with valid SCP configuration."""
        config = {
            'remote_host': 'scp.example.com',
            'remote_user': 'testuser',
            'remote_password': 'testpass',
            'remote_path': '/backup/',
            'upload_method': 'scp'
        }
        
        # Should not raise exception
        remote_config = RemoteUploadConfig(config)
        self.assertEqual(remote_config.config, config)
    
    def test_remote_upload_config_with_key_file(self):
        """Test RemoteUploadConfig with SSH key file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_key:
            temp_key_path = temp_key.name
        
        try:
            config = {
                'remote_host': 'sftp.example.com',
                'remote_user': 'testuser',
                'remote_key_file': temp_key_path,
                'remote_path': '/backup/',
                'upload_method': 'sftp'
            }
            
            # Should not raise exception
            remote_config = RemoteUploadConfig(config)
            self.assertEqual(remote_config.config, config)
        finally:
            os.unlink(temp_key_path)
    
    def test_remote_upload_config_invalid_method(self):
        """Test RemoteUploadConfig with invalid upload method."""
        config = {
            'remote_host': 'example.com',
            'remote_user': 'testuser',
            'remote_password': 'testpass',
            'remote_path': '/backup/',
            'upload_method': 'invalid_method'
        }
        
        with self.assertRaises(ValidationError):
            RemoteUploadConfig(config)
    
    def test_remote_upload_config_missing_credentials(self):
        """Test RemoteUploadConfig with missing credentials."""
        config = {
            'remote_host': 'example.com',
            'remote_user': 'testuser',
            'remote_path': '/backup/',
            'upload_method': 'sftp'
            # Missing password and key file
        }
        
        with self.assertRaises(ValidationError):
            RemoteUploadConfig(config)
    
    def test_remote_upload_config_invalid_key_file(self):
        """Test RemoteUploadConfig with non-existent key file."""
        config = {
            'remote_host': 'example.com',
            'remote_user': 'testuser',
            'remote_key_file': '/path/that/does/not/exist',
            'remote_path': '/backup/',
            'upload_method': 'sftp'
        }
        
        with self.assertRaises(ValidationError):
            RemoteUploadConfig(config)
    
    def test_remote_upload_config_empty(self):
        """Test RemoteUploadConfig with empty configuration."""
        # Empty config should be valid (remote upload optional)
        config = {}
        
        remote_config = RemoteUploadConfig(config)
        self.assertEqual(remote_config.config, config)


class TestArchiveConfig(unittest.TestCase):
    """Test ArchiveConfig validation."""
    
    def test_archive_config_valid_formats(self):
        """Test ArchiveConfig with valid archive formats."""
        valid_formats = ['none', 'gz', 'xz', 'tar.xz', 'zip', 'rar']
        
        for archive_format in valid_formats:
            with self.subTest(format=archive_format):
                config = {
                    'archive_format': archive_format
                }
                
                # Should not raise exception
                archive_config = ArchiveConfig(config)
                self.assertEqual(archive_config.config, config)
    
    def test_archive_config_invalid_format(self):
        """Test ArchiveConfig with invalid archive format."""
        invalid_formats = ['7z', 'bz2', 'invalid', 'tar.gz']
        
        for archive_format in invalid_formats:
            with self.subTest(format=archive_format):
                config = {
                    'archive_format': archive_format
                }
                
                with self.assertRaises(ValidationError):
                    ArchiveConfig(config)
    
    def test_archive_config_empty(self):
        """Test ArchiveConfig with empty configuration."""
        config = {}
        
        # Should default to 'none' or be valid
        archive_config = ArchiveConfig(config)
        self.assertEqual(archive_config.config, config)
    
    def test_archive_config_with_compression_level(self):
        """Test ArchiveConfig with compression level."""
        config = {
            'archive_format': 'gz',
            'compression_level': '6'
        }
        
        # Should not raise exception
        archive_config = ArchiveConfig(config)
        self.assertEqual(archive_config.config, config)
    
    def test_archive_config_invalid_compression_level(self):
        """Test ArchiveConfig with invalid compression level."""
        config = {
            'archive_format': 'gz',
            'compression_level': 'invalid'
        }
        
        with self.assertRaises(ValidationError):
            ArchiveConfig(config)


class TestConfigValidator(unittest.TestCase):
    """Test ConfigValidator main class."""
    
    def setUp(self):
        """Set up ConfigValidator test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.ini')
        
        # Create a valid test configuration
        self.valid_config = {
            'mysql': {
                'host': 'localhost',
                'port': '3306',
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb'
            },
            'backup': {
                'backup_dir': self.test_dir,
                'archive_format': 'gz',
                'keep_backups': '7'
            },
            'notifications': {
                'telegram_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
                'telegram_chat_id': '123456789'
            },
            'remote_upload': {
                'remote_host': 'sftp.example.com',
                'remote_user': 'testuser',
                'remote_password': 'testpass',
                'remote_path': '/backup/',
                'upload_method': 'sftp'
            }
        }
    
    def tearDown(self):
        """Clean up ConfigValidator test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_config_validator_init(self):
        """Test ConfigValidator initialization."""
        validator = ConfigValidator()
        self.assertIsInstance(validator, ConfigValidator)
    
    @patch('src.config_validator.validate_database_connection')
    def test_validate_config_valid(self, mock_validate_db):
        """Test validate_config with valid configuration."""
        validator = ConfigValidator()
        
        # Should not raise exception
        result = validator.validate_config(self.valid_config)
        
        self.assertTrue(result)
    
    def test_validate_config_missing_mysql(self):
        """Test validate_config with missing MySQL configuration."""
        invalid_config = self.valid_config.copy()
        del invalid_config['mysql']
        
        validator = ConfigValidator()
        
        with self.assertRaises(ValidationError):
            validator.validate_config(invalid_config)
    
    def test_validate_config_invalid_mysql(self):
        """Test validate_config with invalid MySQL configuration."""
        invalid_config = self.valid_config.copy()
        invalid_config['mysql']['port'] = 'invalid'
        
        validator = ConfigValidator()
        
        with self.assertRaises(ValidationError):
            validator.validate_config(invalid_config)
    
    def test_validate_config_invalid_notifications(self):
        """Test validate_config with invalid notification configuration."""
        invalid_config = self.valid_config.copy()
        invalid_config['notifications']['telegram_token'] = 'invalid'
        
        validator = ConfigValidator()
        
        with self.assertRaises(ValidationError):
            validator.validate_config(invalid_config)
    
    def test_validate_config_invalid_remote_upload(self):
        """Test validate_config with invalid remote upload configuration."""
        invalid_config = self.valid_config.copy()
        invalid_config['remote_upload']['upload_method'] = 'invalid'
        
        validator = ConfigValidator()
        
        with self.assertRaises(ValidationError):
            validator.validate_config(invalid_config)
    
    def test_validate_config_invalid_archive(self):
        """Test validate_config with invalid archive configuration."""
        invalid_config = self.valid_config.copy()
        invalid_config['backup']['archive_format'] = 'invalid'
        
        validator = ConfigValidator()
        
        with self.assertRaises(ValidationError):
            validator.validate_config(invalid_config)
    
    def test_validate_config_partial(self):
        """Test validate_config with minimal valid configuration."""
        minimal_config = {
            'mysql': {
                'host': 'localhost',
                'port': '3306',
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb'
            },
            'backup': {
                'backup_dir': self.test_dir
            }
        }
        
        validator = ConfigValidator()
        
        # Should not raise exception
        result = validator.validate_config(minimal_config)
        self.assertTrue(result)
    
    def test_validate_config_with_test_connections(self):
        """Test validate_config with connection testing enabled."""
        validator = ConfigValidator()
        
        with patch('src.config_validator.validate_database_connection') as mock_validate_db:
            result = validator.validate_config(self.valid_config, test_connections=True)
            
            # Should call database connection test
            mock_validate_db.assert_called_once()
            self.assertTrue(result)
    
    def test_validate_section_database(self):
        """Test validate_section for database configuration."""
        validator = ConfigValidator()
        
        # Should not raise exception
        validator.validate_section('mysql', self.valid_config['mysql'])
    
    def test_validate_section_notifications(self):
        """Test validate_section for notifications configuration."""
        validator = ConfigValidator()
        
        # Should not raise exception
        validator.validate_section('notifications', self.valid_config['notifications'])
    
    def test_validate_section_remote_upload(self):
        """Test validate_section for remote upload configuration."""
        validator = ConfigValidator()
        
        # Should not raise exception
        validator.validate_section('remote_upload', self.valid_config['remote_upload'])
    
    def test_validate_section_backup(self):
        """Test validate_section for backup configuration."""
        validator = ConfigValidator()
        
        # Should not raise exception
        validator.validate_section('backup', self.valid_config['backup'])
    
    def test_validate_section_unknown(self):
        """Test validate_section for unknown section."""
        validator = ConfigValidator()
        
        # Should not raise exception for unknown sections
        validator.validate_section('unknown', {'key': 'value'})
    
    def test_get_validation_errors_empty(self):
        """Test get_validation_errors with valid configuration."""
        validator = ConfigValidator()
        
        with patch('src.config_validator.validate_database_connection'):
            errors = validator.get_validation_errors(self.valid_config)
            
            self.assertEqual(len(errors), 0)
    
    def test_get_validation_errors_with_errors(self):
        """Test get_validation_errors with invalid configuration."""
        invalid_config = self.valid_config.copy()
        invalid_config['mysql']['port'] = 'invalid'
        invalid_config['notifications']['telegram_token'] = 'invalid'
        
        validator = ConfigValidator()
        
        errors = validator.get_validation_errors(invalid_config)
        
        # Should have multiple errors
        self.assertGreater(len(errors), 0)
        
        # Errors should be strings
        for error in errors:
            self.assertIsInstance(error, str)


class TestConfigValidatorIntegration(unittest.TestCase):
    """Integration tests for ConfigValidator."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'integration_config.ini')
    
    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow."""
        # Create comprehensive configuration
        config = {
            'mysql': {
                'host': 'localhost',
                'port': '3306',
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb'
            },
            'backup': {
                'backup_dir': self.test_dir,
                'archive_format': 'gz',
                'keep_backups': '7',
                'compression_level': '6'
            },
            'notifications': {
                'telegram_token': '123456789:ABCdefGHIjklMNOpqrsTUVwxyz',
                'telegram_chat_id': '123456789',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': '587',
                'smtp_username': 'test@gmail.com',
                'smtp_password': 'password',
                'email_from': 'test@gmail.com',
                'email_to': 'recipient@gmail.com'
            },
            'remote_upload': {
                'remote_host': 'sftp.example.com',
                'remote_user': 'testuser',
                'remote_password': 'testpass',
                'remote_path': '/backup/',
                'upload_method': 'sftp'
            }
        }
        
        validator = ConfigValidator()
        
        # Test validation
        with patch('src.config_validator.validate_database_connection'):
            result = validator.validate_config(config)
            self.assertTrue(result)
        
        # Test error collection
        errors = validator.get_validation_errors(config)
        self.assertEqual(len(errors), 0)
    
    def test_validation_with_multiple_errors(self):
        """Test validation with multiple configuration errors."""
        config = {
            'mysql': {
                'host': '',  # Invalid empty host
                'port': 'invalid',  # Invalid port
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb'
            },
            'backup': {
                'backup_dir': '/nonexistent/directory',  # May be invalid
                'archive_format': 'invalid_format',  # Invalid format
                'keep_backups': 'invalid'  # Invalid number
            },
            'notifications': {
                'telegram_token': 'invalid_token',  # Invalid token
                'email_from': 'invalid_email'  # Invalid email
            },
            'remote_upload': {
                'upload_method': 'invalid_method'  # Invalid method
            }
        }
        
        validator = ConfigValidator()
        
        # Should collect multiple errors
        errors = validator.get_validation_errors(config)
        
        # Should have multiple errors
        self.assertGreater(len(errors), 3)
        
        # Each error should be descriptive
        for error in errors:
            self.assertIsInstance(error, str)
            self.assertGreater(len(error), 10)  # Reasonable error message length


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

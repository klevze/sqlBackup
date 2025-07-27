#!/usr/bin/env python3
"""
Comprehensive test suite for backup module
"""

import unittest
import tempfile
import os
import shutil
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from pathlib import Path
import datetime

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.backup import MySQLBackup, format_size, should_upload
from sql_backup.config import Config


class TestFormatSize(unittest.TestCase):
    """Test size formatting utility function."""
    
    def test_format_size_bytes(self):
        """Test bytes formatting."""
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(1), "1 B")
    
    def test_format_size_kb(self):
        """Test kilobytes formatting."""
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(2048), "2.0 KB")
        self.assertEqual(format_size(1536), "1.5 KB")
    
    def test_format_size_mb(self):
        """Test megabytes formatting."""
        self.assertEqual(format_size(1048576), "1.0 MB")
        self.assertEqual(format_size(2097152), "2.0 MB")
        self.assertEqual(format_size(1572864), "1.5 MB")
    
    def test_format_size_gb(self):
        """Test gigabytes formatting."""
        self.assertEqual(format_size(1073741824), "1.0 GB")
        self.assertEqual(format_size(2147483648), "2.0 GB")
    
    def test_format_size_negative(self):
        """Test negative size handling."""
        self.assertEqual(format_size(-1), "0 B")
        self.assertEqual(format_size(-1024), "0 B")


class TestShouldUpload(unittest.TestCase):
    """Test upload condition checking."""
    
    def test_should_upload_daily(self):
        """Test daily upload condition."""
        self.assertTrue(should_upload("daily"))
    
    def test_should_upload_weekly(self):
        """Test weekly upload condition."""
        self.assertTrue(should_upload("weekly"))
    
    def test_should_upload_numeric_current_day(self):
        """Test numeric day matching current day."""
        now = datetime.datetime.now()
        self.assertTrue(should_upload(str(now.day)))
    
    def test_should_upload_numeric_different_day(self):
        """Test numeric day not matching current day."""
        now = datetime.datetime.now()
        different_day = (now.day + 1) % 31 + 1  # Ensure different day
        if different_day != now.day:
            self.assertFalse(should_upload(str(different_day)))
    
    def test_should_upload_invalid_input(self):
        """Test invalid upload condition."""
        self.assertFalse(should_upload("invalid"))
        self.assertFalse(should_upload(""))
        self.assertFalse(should_upload(None))


class TestMySQLBackup(unittest.TestCase):
    """Comprehensive tests for MySQLBackup class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.ini')
        self.backup_dir = os.path.join(self.test_dir, 'backups')
        os.makedirs(self.backup_dir)
        
        # Create test configuration
        self._create_test_config()
        
        # Mock logger to avoid file creation during tests
        self.logger_patcher = patch('src.backup.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_config(self):
        """Create test configuration file."""
        config_content = f"""
[backup]
backup_dir = {self.backup_dir}
keep_days = 7
archive_type = none

[mysql]
user = test_user
password = test_password
host = localhost
port = 3306
database = test_db

[notification]
channels = 

[export]
enabled = false

[logging]
level = INFO
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    def test_init_with_default_config(self):
        """Test initialization with default config path."""
        with patch('os.path.exists', return_value=True):
            with patch.object(Config, 'load_config'):
                backup = MySQLBackup()
                self.assertIsNotNone(backup.config)
    
    def test_init_with_custom_config(self):
        """Test initialization with custom config path."""
        backup = MySQLBackup(self.config_file)
        self.assertEqual(backup.config_path, self.config_file)
        self.assertIsNotNone(backup.config)
    
    def test_init_with_nonexistent_config(self):
        """Test initialization with nonexistent config file."""
        with self.assertRaises(FileNotFoundError):
            MySQLBackup('/nonexistent/config.ini')
    
    @patch('src.backup.subprocess.run')
    @patch('src.backup.os.path.exists')
    def test_execute_mysqldump_success(self, mock_exists, mock_subprocess):
        """Test successful mysqldump execution."""
        mock_exists.return_value = True
        mock_subprocess.return_value.returncode = 0
        
        backup = MySQLBackup(self.config_file)
        
        # Mock the backup file creation
        test_backup_file = os.path.join(self.backup_dir, 'test_backup.sql')
        with patch.object(backup, '_generate_backup_filename', return_value=test_backup_file):
            with open(test_backup_file, 'w') as f:
                f.write("-- Test backup content")
            
            result = backup._execute_mysqldump()
            
        self.assertEqual(result, test_backup_file)
        mock_subprocess.assert_called_once()
    
    @patch('src.backup.subprocess.run')
    def test_execute_mysqldump_failure(self, mock_subprocess):
        """Test mysqldump execution failure."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Database connection failed"
        
        backup = MySQLBackup(self.config_file)
        
        with self.assertRaises(subprocess.CalledProcessError):
            backup._execute_mysqldump()
    
    def test_generate_backup_filename(self):
        """Test backup filename generation."""
        backup = MySQLBackup(self.config_file)
        
        with patch('src.backup.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250127_103015"
            
            filename = backup._generate_backup_filename()
            
        expected_filename = os.path.join(
            self.backup_dir, 
            "test_db_20250127_103015.sql"
        )
        self.assertEqual(filename, expected_filename)
    
    def test_compress_backup_none(self):
        """Test no compression."""
        backup = MySQLBackup(self.config_file)
        test_file = os.path.join(self.backup_dir, 'test.sql')
        
        with open(test_file, 'w') as f:
            f.write("-- Test content")
        
        result = backup._compress_backup(test_file)
        self.assertEqual(result, test_file)
        self.assertTrue(os.path.exists(test_file))
    
    @patch('src.backup.gzip.open')
    @patch('builtins.open', new_callable=mock_open, read_data="test content")
    @patch('src.backup.os.remove')
    def test_compress_backup_gz(self, mock_remove, mock_file, mock_gzip):
        """Test gzip compression."""
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('backup', 'archive_type', 'gz')
        
        test_file = os.path.join(self.backup_dir, 'test.sql')
        result = backup._compress_backup(test_file)
        
        expected_file = test_file + '.gz'
        self.assertEqual(result, expected_file)
        mock_gzip.assert_called_once()
        mock_remove.assert_called_once_with(test_file)
    
    @patch('src.backup.lzma.open')
    @patch('builtins.open', new_callable=mock_open, read_data="test content")
    @patch('src.backup.os.remove')
    def test_compress_backup_xz(self, mock_remove, mock_file, mock_lzma):
        """Test XZ compression."""
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('backup', 'archive_type', 'xz')
        
        test_file = os.path.join(self.backup_dir, 'test.sql')
        result = backup._compress_backup(test_file)
        
        expected_file = test_file + '.xz'
        self.assertEqual(result, expected_file)
        mock_lzma.assert_called_once()
        mock_remove.assert_called_once_with(test_file)
    
    @patch('src.backup.ZipFile')
    @patch('src.backup.os.remove')
    def test_compress_backup_zip(self, mock_remove, mock_zipfile):
        """Test ZIP compression."""
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('backup', 'archive_type', 'zip')
        
        test_file = os.path.join(self.backup_dir, 'test.sql')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = backup._compress_backup(test_file)
        
        expected_file = test_file.replace('.sql', '.zip')
        self.assertEqual(result, expected_file)
        mock_zipfile.assert_called_once()
        mock_remove.assert_called_once_with(test_file)
    
    def test_compress_backup_unsupported(self):
        """Test unsupported compression type."""
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('backup', 'archive_type', 'unsupported')
        
        test_file = os.path.join(self.backup_dir, 'test.sql')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ValueError):
            backup._compress_backup(test_file)
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        backup = MySQLBackup(self.config_file)
        
        # Create test files
        temp_files = []
        for i in range(3):
            temp_file = os.path.join(self.test_dir, f'temp_{i}.tmp')
            with open(temp_file, 'w') as f:
                f.write(f"temp content {i}")
            temp_files.append(temp_file)
        
        # Verify files exist
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
        
        # Clean up files
        backup._cleanup_temp_files(temp_files)
        
        # Verify files are deleted
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))
    
    def test_cleanup_temp_files_nonexistent(self):
        """Test cleanup with nonexistent files."""
        backup = MySQLBackup(self.config_file)
        nonexistent_files = ['/nonexistent/file1.tmp', '/nonexistent/file2.tmp']
        
        # Should not raise exception
        backup._cleanup_temp_files(nonexistent_files)
    
    @patch('src.backup.MySQLBackup._execute_mysqldump')
    @patch('src.backup.MySQLBackup._compress_backup')
    @patch('src.remote_upload.RemoteUploader.upload_file')
    @patch('src.notifications.NotificationManager.send_notification')
    def test_create_backup_success_no_upload(self, mock_notify, mock_upload, 
                                           mock_compress, mock_mysqldump):
        """Test successful backup creation without upload."""
        # Setup mocks
        test_backup_file = os.path.join(self.backup_dir, 'test_backup.sql')
        mock_mysqldump.return_value = test_backup_file
        mock_compress.return_value = test_backup_file
        
        backup = MySQLBackup(self.config_file)
        result = backup.create_backup()
        
        self.assertTrue(result)
        mock_mysqldump.assert_called_once()
        mock_compress.assert_called_once_with(test_backup_file)
        mock_upload.assert_not_called()  # Upload disabled in config
        mock_notify.assert_called_once()
    
    @patch('src.backup.MySQLBackup._execute_mysqldump')
    @patch('src.backup.MySQLBackup._compress_backup')
    @patch('src.remote_upload.RemoteUploader.upload_file')
    @patch('src.notifications.NotificationManager.send_notification')
    def test_create_backup_success_with_upload(self, mock_notify, mock_upload, 
                                             mock_compress, mock_mysqldump):
        """Test successful backup creation with upload."""
        # Enable upload in config
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('export', 'enabled', 'true')
        
        # Setup mocks
        test_backup_file = os.path.join(self.backup_dir, 'test_backup.sql')
        mock_mysqldump.return_value = test_backup_file
        mock_compress.return_value = test_backup_file
        mock_upload.return_value = True
        
        result = backup.create_backup()
        
        self.assertTrue(result)
        mock_mysqldump.assert_called_once()
        mock_compress.assert_called_once_with(test_backup_file)
        mock_upload.assert_called_once_with(test_backup_file)
        mock_notify.assert_called_once()
    
    @patch('src.backup.MySQLBackup._execute_mysqldump')
    def test_create_backup_mysqldump_failure(self, mock_mysqldump):
        """Test backup creation with mysqldump failure."""
        mock_mysqldump.side_effect = subprocess.CalledProcessError(1, 'mysqldump')
        
        backup = MySQLBackup(self.config_file)
        result = backup.create_backup()
        
        self.assertFalse(result)
    
    @patch('src.backup.MySQLBackup._execute_mysqldump')
    @patch('src.backup.MySQLBackup._compress_backup')
    def test_create_backup_compression_failure(self, mock_compress, mock_mysqldump):
        """Test backup creation with compression failure."""
        test_backup_file = os.path.join(self.backup_dir, 'test_backup.sql')
        mock_mysqldump.return_value = test_backup_file
        mock_compress.side_effect = Exception("Compression failed")
        
        backup = MySQLBackup(self.config_file)
        result = backup.create_backup()
        
        self.assertFalse(result)
    
    @patch('src.backup.MySQLBackup._execute_mysqldump')
    @patch('src.backup.MySQLBackup._compress_backup')
    @patch('src.remote_upload.RemoteUploader.upload_file')
    def test_create_backup_upload_failure(self, mock_upload, mock_compress, mock_mysqldump):
        """Test backup creation with upload failure."""
        # Enable upload in config
        backup = MySQLBackup(self.config_file)
        backup.config.config.set('export', 'enabled', 'true')
        
        # Setup mocks
        test_backup_file = os.path.join(self.backup_dir, 'test_backup.sql')
        mock_mysqldump.return_value = test_backup_file
        mock_compress.return_value = test_backup_file
        mock_upload.return_value = False  # Upload fails
        
        result = backup.create_backup()
        
        self.assertFalse(result)


class TestMySQLBackupIntegration(unittest.TestCase):
    """Integration tests for MySQLBackup."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'integration_config.ini')
        self.backup_dir = os.path.join(self.test_dir, 'backups')
        os.makedirs(self.backup_dir)
        
        self._create_integration_config()
    
    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_integration_config(self):
        """Create integration test configuration."""
        config_content = f"""
[backup]
backup_dir = {self.backup_dir}
keep_days = 1
archive_type = none

[mysql]
user = nonexistent_user
password = fake_password
host = nonexistent_host
port = 3306
database = fake_db

[notification]
channels = 

[export]
enabled = false

[logging]
level = DEBUG
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    def test_config_loading_integration(self):
        """Test configuration loading in integration context."""
        backup = MySQLBackup(self.config_file)
        
        self.assertEqual(backup.config.get('backup', 'backup_dir'), self.backup_dir)
        self.assertEqual(backup.config.get('mysql', 'database'), 'fake_db')
        self.assertEqual(backup.config.get('backup', 'archive_type'), 'none')
    
    @patch('src.backup.subprocess.run')
    def test_backup_directory_creation(self, mock_subprocess):
        """Test that backup directory is created if it doesn't exist."""
        # Remove backup directory
        shutil.rmtree(self.backup_dir)
        self.assertFalse(os.path.exists(self.backup_dir))
        
        # Mock successful mysqldump
        mock_subprocess.return_value.returncode = 0
        
        backup = MySQLBackup(self.config_file)
        
        # Create a dummy backup file for the test
        os.makedirs(self.backup_dir)
        test_file = os.path.join(self.backup_dir, 'test.sql')
        with open(test_file, 'w') as f:
            f.write("-- Test backup")
        
        with patch.object(backup, '_generate_backup_filename', return_value=test_file):
            result = backup._execute_mysqldump()
            
        self.assertTrue(os.path.exists(self.backup_dir))


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

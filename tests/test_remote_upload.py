#!/usr/bin/env python3
"""
Comprehensive test suite for remote_upload module
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
import ftplib
import paramiko

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.remote_upload import RemoteUploader
from sql_backup.config import Config


class TestRemoteUploader(unittest.TestCase):
    """Comprehensive tests for RemoteUploader class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.uploader = RemoteUploader(self.mock_config)
        
        # Create test file
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test_backup.sql')
        with open(self.test_file, 'w') as f:
            f.write("-- Test backup content")
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init(self):
        """Test RemoteUploader initialization."""
        self.assertEqual(self.uploader.config, self.mock_config)
        self.assertIsNotNone(self.uploader.logger)
    
    def test_upload_file_export_disabled(self):
        """Test upload when export is disabled."""
        self.mock_config.getboolean.return_value = False
        
        result = self.uploader.upload_file(self.test_file)
        
        self.assertFalse(result)
        self.mock_config.getboolean.assert_called_with('export', 'enabled', False)
    
    def test_upload_file_nonexistent_file(self):
        """Test upload with nonexistent file."""
        self.mock_config.getboolean.return_value = True
        nonexistent_file = '/nonexistent/file.sql'
        
        result = self.uploader.upload_file(nonexistent_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    def test_upload_file_sftp_success(self):
        """Test successful SFTP upload."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'sftp'
        
        with patch.object(self.uploader, '_upload_sftp', return_value=True) as mock_sftp:
            result = self.uploader.upload_file(self.test_file)
            
        self.assertTrue(result)
        mock_sftp.assert_called_once_with(self.test_file)
    
    def test_upload_file_ftp_success(self):
        """Test successful FTP upload."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'ftp'
        
        with patch.object(self.uploader, '_upload_ftp', return_value=True) as mock_ftp:
            result = self.uploader.upload_file(self.test_file)
            
        self.assertTrue(result)
        mock_ftp.assert_called_once_with(self.test_file)
    
    def test_upload_file_scp_success(self):
        """Test successful SCP upload."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'scp'
        
        with patch.object(self.uploader, '_upload_scp', return_value=True) as mock_scp:
            result = self.uploader.upload_file(self.test_file)
            
        self.assertTrue(result)
        mock_scp.assert_called_once_with(self.test_file)
    
    def test_upload_file_unsupported_type(self):
        """Test upload with unsupported export type."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'unsupported'
        
        result = self.uploader.upload_file(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestSFTPUpload(unittest.TestCase):
    """Test SFTP upload functionality."""
    
    def setUp(self):
        """Set up SFTP test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.uploader = RemoteUploader(self.mock_config)
        
        # Create test file
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test_backup.sql')
        with open(self.test_file, 'w') as f:
            f.write("-- Test backup content")
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_upload_sftp_missing_config(self):
        """Test SFTP upload with missing configuration."""
        self.mock_config.get.side_effect = ['', 'username', 'password', '/remote/path']
        
        result = self.uploader._upload_sftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    def test_upload_sftp_success(self, mock_ssh_client):
        """Test successful SFTP upload."""
        # Setup config mocks
        self.mock_config.get.side_effect = [
            'sftp.example.com',  # server
            'sftp_user',         # username
            'sftp_password',     # password
            '/remote/backups'    # remote_path
        ]
        
        # Setup SSH client and SFTP mocks
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_client.return_value = mock_ssh
        
        result = self.uploader._upload_sftp(self.test_file)
        
        self.assertTrue(result)
        
        # Verify SSH operations
        mock_ssh_client.assert_called_once()
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            'sftp.example.com', 
            username='sftp_user', 
            password='sftp_password'
        )
        mock_ssh.open_sftp.assert_called_once()
        
        # Verify SFTP operations
        mock_sftp.put.assert_called_once()
        mock_sftp.close.assert_called_once()
        mock_ssh.close.assert_called_once()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    def test_upload_sftp_connection_error(self, mock_ssh_client):
        """Test SFTP upload with connection error."""
        self.mock_config.get.side_effect = [
            'sftp.example.com', 'sftp_user', 'sftp_password', '/remote/backups'
        ]
        
        # Setup connection error
        mock_ssh = Mock()
        mock_ssh.connect.side_effect = paramiko.AuthenticationException("Auth failed")
        mock_ssh_client.return_value = mock_ssh
        
        result = self.uploader._upload_sftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    def test_upload_sftp_transfer_error(self, mock_ssh_client):
        """Test SFTP upload with transfer error."""
        self.mock_config.get.side_effect = [
            'sftp.example.com', 'sftp_user', 'sftp_password', '/remote/backups'
        ]
        
        # Setup transfer error
        mock_ssh = Mock()
        mock_sftp = Mock()
        mock_sftp.put.side_effect = Exception("Transfer failed")
        mock_ssh.open_sftp.return_value = mock_sftp
        mock_ssh_client.return_value = mock_ssh
        
        result = self.uploader._upload_sftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestFTPUpload(unittest.TestCase):
    """Test FTP upload functionality."""
    
    def setUp(self):
        """Set up FTP test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.uploader = RemoteUploader(self.mock_config)
        
        # Create test file
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test_backup.sql')
        with open(self.test_file, 'w') as f:
            f.write("-- Test backup content")
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_upload_ftp_missing_config(self):
        """Test FTP upload with missing configuration."""
        self.mock_config.get.side_effect = ['', 'username', 'password', '/remote/path']
        
        result = self.uploader._upload_ftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.ftplib.FTP')
    @patch('builtins.open', new_callable=mock_open, read_data="test content")
    def test_upload_ftp_success(self, mock_file, mock_ftp_class):
        """Test successful FTP upload."""
        # Setup config mocks
        self.mock_config.get.side_effect = [
            'ftp.example.com',   # server
            'ftp_user',          # username
            'ftp_password',      # password
            '/remote/backups'    # remote_path
        ]
        
        # Setup FTP mock
        mock_ftp = Mock()
        mock_ftp_class.return_value = mock_ftp
        
        result = self.uploader._upload_ftp(self.test_file)
        
        self.assertTrue(result)
        
        # Verify FTP operations
        mock_ftp_class.assert_called_once_with('ftp.example.com')
        mock_ftp.login.assert_called_once_with('ftp_user', 'ftp_password')
        mock_ftp.cwd.assert_called_once_with('/remote/backups')
        mock_ftp.storbinary.assert_called_once()
        mock_ftp.quit.assert_called_once()
    
    @patch('src.remote_upload.ftplib.FTP')
    def test_upload_ftp_connection_error(self, mock_ftp_class):
        """Test FTP upload with connection error."""
        self.mock_config.get.side_effect = [
            'ftp.example.com', 'ftp_user', 'ftp_password', '/remote/backups'
        ]
        
        # Setup connection error
        mock_ftp_class.side_effect = ftplib.error_perm("530 Authentication failed")
        
        result = self.uploader._upload_ftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.ftplib.FTP')
    @patch('builtins.open', new_callable=mock_open, read_data="test content")
    def test_upload_ftp_transfer_error(self, mock_file, mock_ftp_class):
        """Test FTP upload with transfer error."""
        self.mock_config.get.side_effect = [
            'ftp.example.com', 'ftp_user', 'ftp_password', '/remote/backups'
        ]
        
        # Setup transfer error
        mock_ftp = Mock()
        mock_ftp.storbinary.side_effect = ftplib.error_temp("426 Transfer failed")
        mock_ftp_class.return_value = mock_ftp
        
        result = self.uploader._upload_ftp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestSCPUpload(unittest.TestCase):
    """Test SCP upload functionality."""
    
    def setUp(self):
        """Set up SCP test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.uploader = RemoteUploader(self.mock_config)
        
        # Create test file
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test_backup.sql')
        with open(self.test_file, 'w') as f:
            f.write("-- Test backup content")
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_upload_scp_missing_config(self):
        """Test SCP upload with missing configuration."""
        self.mock_config.get.side_effect = ['', 'username', 'password', '/remote/path']
        
        result = self.uploader._upload_scp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    @patch('src.remote_upload.SCPClient')
    def test_upload_scp_success(self, mock_scp_class, mock_ssh_client):
        """Test successful SCP upload."""
        # Setup config mocks
        self.mock_config.get.side_effect = [
            'scp.example.com',   # server
            'scp_user',          # username
            'scp_password',      # password
            '/remote/backups'    # remote_path
        ]
        
        # Setup SSH and SCP mocks
        mock_ssh = Mock()
        mock_scp = Mock()
        mock_ssh_client.return_value = mock_ssh
        mock_scp_class.return_value = mock_scp
        
        result = self.uploader._upload_scp(self.test_file)
        
        self.assertTrue(result)
        
        # Verify SSH operations
        mock_ssh_client.assert_called_once()
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        mock_ssh.connect.assert_called_once_with(
            'scp.example.com',
            username='scp_user',
            password='scp_password'
        )
        
        # Verify SCP operations
        mock_scp_class.assert_called_once_with(mock_ssh.get_transport())
        mock_scp.put.assert_called_once()
        mock_scp.close.assert_called_once()
        mock_ssh.close.assert_called_once()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    def test_upload_scp_connection_error(self, mock_ssh_client):
        """Test SCP upload with connection error."""
        self.mock_config.get.side_effect = [
            'scp.example.com', 'scp_user', 'scp_password', '/remote/backups'
        ]
        
        # Setup connection error
        mock_ssh = Mock()
        mock_ssh.connect.side_effect = paramiko.SSHException("Connection failed")
        mock_ssh_client.return_value = mock_ssh
        
        result = self.uploader._upload_scp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.remote_upload.paramiko.SSHClient')
    @patch('src.remote_upload.SCPClient')
    def test_upload_scp_transfer_error(self, mock_scp_class, mock_ssh_client):
        """Test SCP upload with transfer error."""
        self.mock_config.get.side_effect = [
            'scp.example.com', 'scp_user', 'scp_password', '/remote/backups'
        ]
        
        # Setup transfer error
        mock_ssh = Mock()
        mock_scp = Mock()
        mock_scp.put.side_effect = Exception("Transfer failed")
        mock_ssh_client.return_value = mock_ssh
        mock_scp_class.return_value = mock_scp
        
        result = self.uploader._upload_scp(self.test_file)
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestRemoteUploaderIntegration(unittest.TestCase):
    """Integration tests for RemoteUploader."""
    
    def setUp(self):
        """Set up integration test environment."""
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        # Create test file
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'integration_backup.sql.gz')
        with open(self.test_file, 'wb') as f:
            f.write(b"compressed backup content")
    
    def tearDown(self):
        """Clean up integration test environment."""
        self.logger_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_upload_workflow_all_types(self):
        """Test upload workflow for all supported types."""
        mock_config = Mock(spec=Config)
        uploader = RemoteUploader(mock_config)
        
        upload_types = ['sftp', 'ftp', 'scp']
        
        for upload_type in upload_types:
            with self.subTest(upload_type=upload_type):
                mock_config.getboolean.return_value = True
                mock_config.get.return_value = upload_type
                
                with patch.object(uploader, f'_upload_{upload_type}', return_value=True) as mock_upload:
                    result = uploader.upload_file(self.test_file)
                    
                    self.assertTrue(result)
                    mock_upload.assert_called_once_with(self.test_file)
    
    def test_upload_file_path_handling(self):
        """Test upload with various file path formats."""
        mock_config = Mock(spec=Config)
        mock_config.getboolean.return_value = True
        mock_config.get.return_value = 'sftp'
        
        uploader = RemoteUploader(mock_config)
        
        # Test with different path formats
        path_formats = [
            self.test_file,                           # Absolute path
            os.path.relpath(self.test_file),         # Relative path
            self.test_file.replace('\\', '/'),       # Forward slashes
        ]
        
        for file_path in path_formats:
            with self.subTest(file_path=file_path):
                with patch.object(uploader, '_upload_sftp', return_value=True) as mock_sftp:
                    result = uploader.upload_file(file_path)
                    
                    if os.path.exists(file_path):
                        self.assertTrue(result)
                        mock_sftp.assert_called_once()
                    else:
                        self.assertFalse(result)
    
    def test_error_recovery_and_logging(self):
        """Test error recovery and logging behavior."""
        mock_config = Mock(spec=Config)
        mock_config.getboolean.return_value = True
        mock_config.get.return_value = 'sftp'
        
        uploader = RemoteUploader(mock_config)
        
        with patch.object(uploader, '_upload_sftp', side_effect=Exception("Network error")):
            result = uploader.upload_file(self.test_file)
            
            self.assertFalse(result)
            
            # Verify error logging
            self.mock_logger.return_value.error.assert_called()
            
            # Verify that error message contains useful information
            error_calls = self.mock_logger.return_value.error.call_args_list
            self.assertTrue(any("Network error" in str(call) for call in error_calls))


class TestRemoteUploaderEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up edge case test environment."""
        # Mock logger
        self.logger_patcher = patch('src.remote_upload.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
    
    def tearDown(self):
        """Clean up edge case test environment."""
        self.logger_patcher.stop()
    
    def test_upload_empty_file(self):
        """Test upload of empty file."""
        mock_config = Mock(spec=Config)
        mock_config.getboolean.return_value = True
        mock_config.get.return_value = 'sftp'
        
        uploader = RemoteUploader(mock_config)
        
        # Create empty file
        test_dir = tempfile.mkdtemp()
        try:
            empty_file = os.path.join(test_dir, 'empty.sql')
            with open(empty_file, 'w') as f:
                pass  # Create empty file
            
            with patch.object(uploader, '_upload_sftp', return_value=True) as mock_sftp:
                result = uploader.upload_file(empty_file)
                
                self.assertTrue(result)
                mock_sftp.assert_called_once_with(empty_file)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_upload_large_file_simulation(self):
        """Test upload simulation for large files."""
        mock_config = Mock(spec=Config)
        mock_config.getboolean.return_value = True
        mock_config.get.return_value = 'ftp'
        
        uploader = RemoteUploader(mock_config)
        
        # Simulate large file
        test_dir = tempfile.mkdtemp()
        try:
            large_file = os.path.join(test_dir, 'large_backup.sql')
            with open(large_file, 'w') as f:
                f.write("-- Large backup simulation\n" * 1000)
            
            with patch.object(uploader, '_upload_ftp', return_value=True) as mock_ftp:
                result = uploader.upload_file(large_file)
                
                self.assertTrue(result)
                mock_ftp.assert_called_once_with(large_file)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_upload_with_special_characters_in_filename(self):
        """Test upload with special characters in filename."""
        mock_config = Mock(spec=Config)
        mock_config.getboolean.return_value = True
        mock_config.get.return_value = 'scp'
        
        uploader = RemoteUploader(mock_config)
        
        test_dir = tempfile.mkdtemp()
        try:
            # Create file with special characters (where allowed by OS)
            special_file = os.path.join(test_dir, 'backup_2025-01-27_10-30-15.sql.gz')
            with open(special_file, 'w') as f:
                f.write("-- Backup with special chars in name")
            
            with patch.object(uploader, '_upload_scp', return_value=True) as mock_scp:
                result = uploader.upload_file(special_file)
                
                self.assertTrue(result)
                mock_scp.assert_called_once_with(special_file)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

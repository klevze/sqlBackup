# sqlBackup Code Examples

This document provides practical code examples for using and extending the sqlBackup system.

## Basic Usage Examples

### Simple Backup

```python
#!/usr/bin/env python3
"""
Simple backup script - minimal configuration required
"""

from sql_backup.backup import MySQLBackup
from sql_backup.logger import setup_logging, get_logger

def main():
    # Setup logging
    setup_logging(log_level='INFO')
    logger = get_logger(__name__)
    
    try:
        # Create and run backup
        backup = MySQLBackup('config.ini')
        success = backup.create_backup()
        
        if success:
            logger.info("✅ Backup completed successfully")
        else:
            logger.error("❌ Backup failed")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Backup process failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
```

### Configuration Validation Script

```python
#!/usr/bin/env python3
"""
Validate configuration before running backup
"""

import sys
from sql_backup.config_validator import ConfigValidator
from sql_backup.logger import setup_logging, get_logger

def validate_config_file(config_path: str = 'config.ini'):
    """Validate configuration file and report results."""
    
    setup_logging(log_level='INFO')
    logger = get_logger(__name__)
    
    logger.info(f"🔍 Validating configuration file: {config_path}")
    
    try:
        validator = ConfigValidator(config_path)
        is_valid, errors, warnings = validator.validate_configuration()
        
        # Report warnings
        if warnings:
            logger.warning(f"⚠️  Found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  • {warning}")
        
        # Report errors
        if not is_valid:
            logger.error(f"❌ Configuration validation failed with {len(errors)} errors:")
            for error in errors:
                logger.error(f"  • {error}")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation process failed: {str(e)}")
        return False

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
    
    if validate_config_file(config_path):
        print("Configuration is valid and ready to use!")
        return 0
    else:
        print("Configuration validation failed. Please fix the errors and try again.")
        return 1

if __name__ == "__main__":
    exit(main())
```

## Advanced Usage Examples

### Custom Backup with Monitoring

```python
#!/usr/bin/env python3
"""
Advanced backup script with monitoring and custom logic
"""

import time
import psutil
from datetime import datetime
from sql_backup.backup import MySQLBackup
from sql_backup.config import Config
from sql_backup.notifications import NotificationManager
from sql_backup.logger import setup_logging, get_logger

class MonitoredBackup:
    """Enhanced backup with system monitoring."""
    
    def __init__(self, config_path: str = 'config.ini'):
        self.config = Config(config_path)
        self.config.load_config()
        self.logger = get_logger(__name__)
        self.notifier = NotificationManager(self.config)
        
    def check_system_resources(self) -> bool:
        """Check if system has enough resources for backup."""
        
        # Check available disk space (minimum 1GB)
        backup_dir = self.config.get('backup', 'backup_dir', '/tmp')
        disk_usage = psutil.disk_usage(backup_dir)
        free_gb = disk_usage.free / (1024**3)
        
        if free_gb < 1.0:
            self.logger.error(f"Insufficient disk space: {free_gb:.2f}GB available")
            return False
        
        # Check memory usage (don't start if > 90% used)
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            self.logger.warning(f"High memory usage: {memory.percent}%")
            return False
        
        self.logger.info(f"System check passed: {free_gb:.2f}GB disk, {memory.percent}% memory")
        return True
    
    def run_backup_with_monitoring(self) -> bool:
        """Run backup with system monitoring."""
        
        start_time = datetime.now()
        self.logger.info(f"🚀 Starting monitored backup at {start_time}")
        
        # Pre-backup checks
        if not self.check_system_resources():
            self.notifier.send_notification(
                "❌ Backup aborted: Insufficient system resources", 
                is_success=False
            )
            return False
        
        try:
            # Monitor system during backup
            backup = MySQLBackup(self.config)
            
            # Start monitoring in background
            initial_memory = psutil.virtual_memory().percent
            
            # Perform backup
            success = backup.create_backup()
            
            # Calculate metrics
            end_time = datetime.now()
            duration = end_time - start_time
            final_memory = psutil.virtual_memory().percent
            memory_delta = final_memory - initial_memory
            
            # Prepare detailed notification
            if success:
                message = (
                    f"✅ Backup completed successfully\n"
                    f"⏱️ Duration: {duration}\n"
                    f"💾 Memory usage change: {memory_delta:+.1f}%\n"
                    f"📅 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.logger.info(f"Backup completed in {duration}")
            else:
                message = f"❌ Backup failed after {duration}"
                self.logger.error(message)
            
            # Send notification
            self.notifier.send_notification(message, is_success=success)
            return success
            
        except Exception as e:
            error_message = f"❌ Backup process failed: {str(e)}"
            self.logger.error(error_message)
            self.notifier.send_notification(error_message, is_success=False)
            return False

def main():
    setup_logging(log_level='INFO', log_file='logs/monitored_backup.log')
    
    monitored_backup = MonitoredBackup()
    success = monitored_backup.run_backup_with_monitoring()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
```

### Multi-Database Backup

```python
#!/usr/bin/env python3
"""
Backup multiple databases with different configurations
"""

import os
from pathlib import Path
from sql_backup.backup import MySQLBackup
from sql_backup.config import Config
from sql_backup.logger import setup_logging, get_logger

class MultiDatabaseBackup:
    """Handle backup of multiple databases."""
    
    def __init__(self, config_dir: str = 'configs'):
        self.config_dir = Path(config_dir)
        self.logger = get_logger(__name__)
        
    def discover_config_files(self) -> list:
        """Find all config files in the config directory."""
        
        config_files = []
        if self.config_dir.exists():
            for config_file in self.config_dir.glob('*.ini'):
                config_files.append(str(config_file))
                
        self.logger.info(f"Found {len(config_files)} configuration files")
        return config_files
    
    def backup_database(self, config_path: str) -> bool:
        """Backup a single database."""
        
        try:
            config = Config(config_path)
            config.load_config()
            
            db_name = config.get('mysql', 'database', 'unknown')
            self.logger.info(f"🔄 Starting backup for database: {db_name}")
            
            backup = MySQLBackup(config_path)
            success = backup.create_backup()
            
            if success:
                self.logger.info(f"✅ Backup completed for database: {db_name}")
            else:
                self.logger.error(f"❌ Backup failed for database: {db_name}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error backing up {config_path}: {str(e)}")
            return False
    
    def backup_all_databases(self) -> dict:
        """Backup all configured databases."""
        
        config_files = self.discover_config_files()
        results = {}
        
        if not config_files:
            self.logger.warning("No configuration files found")
            return results
        
        self.logger.info(f"🚀 Starting multi-database backup for {len(config_files)} databases")
        
        for config_file in config_files:
            config_name = Path(config_file).stem
            success = self.backup_database(config_file)
            results[config_name] = success
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        self.logger.info(f"📊 Backup summary: {successful}/{total} successful")
        
        return results

def main():
    setup_logging(log_level='INFO', log_file='logs/multi_backup.log')
    
    multi_backup = MultiDatabaseBackup('configs')
    results = multi_backup.backup_all_databases()
    
    # Exit with error if any backup failed
    failed_backups = [name for name, success in results.items() if not success]
    
    if failed_backups:
        print(f"❌ Failed backups: {', '.join(failed_backups)}")
        return 1
    else:
        print("✅ All backups completed successfully")
        return 0

if __name__ == "__main__":
    exit(main())
```

## Extension Examples

### Custom Notification Channel

```python
#!/usr/bin/env python3
"""
Example: Adding Discord notification support
"""

import requests
from sql_backup.notifications import NotificationManager
from sql_backup.logger import get_logger

class DiscordNotificationManager(NotificationManager):
    """Extended notification manager with Discord support."""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    def _send_discord(self, message: str) -> bool:
        """Send notification via Discord webhook."""
        
        try:
            if not self.config.getboolean('discord', 'enabled', False):
                return False
            
            webhook_url = self.config.get('discord', 'webhook_url')
            if not webhook_url:
                self.logger.error("Discord webhook URL not configured")
                return False
            
            # Format message for Discord
            embed = {
                "title": "SQL Backup Notification",
                "description": message,
                "color": 0x00ff00 if "✅" in message else 0xff0000,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {"embeds": [embed]}
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                self.logger.info("Discord notification sent successfully")
                return True
            else:
                self.logger.error(f"Discord notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {str(e)}")
            return False
    
    def send_notification(self, message: str, is_success: bool = True) -> None:
        """Send notification through all enabled channels including Discord."""
        
        # Call parent method for existing channels
        super().send_notification(message, is_success)
        
        # Add Discord support
        channels = self.config.getlist('notification', 'channels', [])
        if 'discord' in [channel.lower() for channel in channels]:
            self._send_discord(message)

# Example usage
if __name__ == "__main__":
    from sql_backup.config import Config
    
    config = Config('config.ini')
    config.load_config()
    
    # Use extended notification manager
    notifier = DiscordNotificationManager(config)
    notifier.send_notification("🧪 Testing Discord integration", is_success=True)
```

### Custom Upload Protocol

```python
#!/usr/bin/env python3
"""
Example: Adding Google Drive upload support
"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from sql_backup.remote_upload import RemoteUploader
from sql_backup.logger import get_logger

class GoogleDriveUploader(RemoteUploader):
    """Extended uploader with Google Drive support."""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger(__name__)
        self._drive_service = None
    
    def _get_drive_service(self):
        """Initialize Google Drive service."""
        
        if self._drive_service:
            return self._drive_service
        
        try:
            credentials_file = self.config.get('gdrive', 'credentials_file')
            scopes = ['https://www.googleapis.com/auth/drive.file']
            
            credentials = Credentials.from_service_account_file(
                credentials_file, scopes=scopes
            )
            
            self._drive_service = build('drive', 'v3', credentials=credentials)
            return self._drive_service
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            raise
    
    def _upload_gdrive(self, local_file_path: str) -> bool:
        """Upload file to Google Drive."""
        
        try:
            service = self._get_drive_service()
            
            # Get configuration
            folder_id = self.config.get('gdrive', 'folder_id', None)
            
            # Prepare file metadata
            file_metadata = {
                'name': os.path.basename(local_file_path)
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Upload file
            media = MediaFileUpload(local_file_path, resumable=True)
            
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    self.logger.debug(f"Upload progress: {int(status.progress() * 100)}%")
            
            file_id = response.get('id')
            self.logger.info(f"File uploaded to Google Drive successfully: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Drive upload failed: {str(e)}")
            return False
    
    def upload_file(self, local_file_path: str) -> bool:
        """Upload file using configured method including Google Drive."""
        
        export_type = self.config.get('export', 'export_type', 'sftp')
        
        if export_type == 'gdrive':
            return self._upload_gdrive(local_file_path)
        else:
            # Use parent class for other protocols
            return super().upload_file(local_file_path)

# Example configuration for Google Drive
"""
[gdrive]
enabled = true
credentials_file = /path/to/service-account.json
folder_id = 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms

[export]
enabled = true
export_type = gdrive
"""
```

### Backup Scheduler

```python
#!/usr/bin/env python3
"""
Example: Advanced backup scheduler with different strategies
"""

import schedule
import time
from datetime import datetime, timedelta
from sql_backup.backup import MySQLBackup
from sql_backup.logger import setup_logging, get_logger

class BackupScheduler:
    """Advanced backup scheduler with multiple strategies."""
    
    def __init__(self, config_path: str = 'config.ini'):
        self.config_path = config_path
        self.logger = get_logger(__name__)
        self.last_backup = None
        
    def daily_backup(self):
        """Perform daily backup."""
        self.logger.info("🕐 Starting scheduled daily backup")
        self._run_backup('daily')
    
    def weekly_backup(self):
        """Perform weekly backup."""
        self.logger.info("📅 Starting scheduled weekly backup")
        self._run_backup('weekly')
    
    def emergency_backup(self):
        """Perform emergency backup (e.g., before maintenance)."""
        self.logger.info("🚨 Starting emergency backup")
        self._run_backup('emergency')
    
    def _run_backup(self, backup_type: str):
        """Run backup with type designation."""
        
        try:
            start_time = datetime.now()
            
            backup = MySQLBackup(self.config_path)
            success = backup.create_backup()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            if success:
                self.last_backup = end_time
                self.logger.info(
                    f"✅ {backup_type.title()} backup completed in {duration}"
                )
            else:
                self.logger.error(f"❌ {backup_type.title()} backup failed")
                
        except Exception as e:
            self.logger.error(f"❌ {backup_type.title()} backup error: {str(e)}")
    
    def health_check(self):
        """Check if backups are running as expected."""
        
        if self.last_backup:
            time_since_backup = datetime.now() - self.last_backup
            hours_since = time_since_backup.total_seconds() / 3600
            
            if hours_since > 25:  # More than 25 hours since last backup
                self.logger.warning(
                    f"⚠️ Last backup was {hours_since:.1f} hours ago"
                )
            else:
                self.logger.info(
                    f"✅ Backup health OK (last backup: {hours_since:.1f} hours ago)"
                )
        else:
            self.logger.warning("⚠️ No backup history available")
    
    def start_scheduler(self):
        """Start the backup scheduler."""
        
        self.logger.info("🚀 Starting backup scheduler")
        
        # Schedule daily backups at 2 AM
        schedule.every().day.at("02:00").do(self.daily_backup)
        
        # Schedule weekly backups on Sunday at 1 AM
        schedule.every().sunday.at("01:00").do(self.weekly_backup)
        
        # Schedule health checks every 6 hours
        schedule.every(6).hours.do(self.health_check)
        
        self.logger.info("📋 Scheduled jobs:")
        for job in schedule.jobs:
            self.logger.info(f"  - {job}")
        
        # Run scheduler
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    setup_logging(
        log_level='INFO', 
        log_file='logs/scheduler.log',
        console_output=True
    )
    
    scheduler = BackupScheduler()
    scheduler.start_scheduler()

if __name__ == "__main__":
    main()
```

## Testing Examples

### Unit Test Example

```python
#!/usr/bin/env python3
"""
Example unit tests for custom extensions
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sql_backup.config import Config
from examples.discord_notifier import DiscordNotificationManager

class TestDiscordNotificationManager:
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.getboolean.return_value = True
        config.get.return_value = "https://discord.com/api/webhooks/test"
        config.getlist.return_value = ['discord']
        return config
    
    @pytest.fixture
    def discord_manager(self, mock_config):
        """Discord notification manager instance."""
        return DiscordNotificationManager(mock_config)
    
    @patch('requests.post')
    def test_send_discord_success(self, mock_post, discord_manager):
        """Test successful Discord notification."""
        # Arrange
        mock_post.return_value.status_code = 204
        
        # Act
        result = discord_manager._send_discord("Test message")
        
        # Assert
        assert result is True
        mock_post.assert_called_once()
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert 'embeds' in payload
        assert len(payload['embeds']) == 1
        assert payload['embeds'][0]['description'] == "Test message"
    
    @patch('requests.post')
    def test_send_discord_failure(self, mock_post, discord_manager):
        """Test Discord notification failure."""
        # Arrange
        mock_post.return_value.status_code = 400
        
        # Act
        result = discord_manager._send_discord("Test message")
        
        # Assert
        assert result is False
        mock_post.assert_called_once()
    
    def test_discord_disabled(self, discord_manager):
        """Test Discord notification when disabled."""
        # Arrange
        discord_manager.config.getboolean.return_value = False
        
        # Act
        result = discord_manager._send_discord("Test message")
        
        # Assert
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__])
```

### Integration Test Example

```python
#!/usr/bin/env python3
"""
Integration test example for backup process
"""

import os
import tempfile
import shutil
from pathlib import Path
from sql_backup.backup import MySQLBackup
from sql_backup.config import Config

class TestBackupIntegration:
    
    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.ini')
        self._create_test_config()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def _create_test_config(self):
        """Create test configuration file."""
        config_content = f"""
[backup]
backup_dir = {self.test_dir}/backups
keep_days = 1
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
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = Config(self.config_file)
        config.load_config()
        
        assert config.get('backup', 'backup_dir') == f"{self.test_dir}/backups"
        assert config.get('mysql', 'database') == "test_db"
    
    @patch('src.backup.subprocess.run')
    def test_backup_creation(self, mock_subprocess):
        """Test backup creation process."""
        # Arrange
        mock_subprocess.return_value.returncode = 0
        
        # Create backup directory
        backup_dir = os.path.join(self.test_dir, 'backups')
        os.makedirs(backup_dir)
        
        # Act
        backup = MySQLBackup(self.config_file)
        
        # Mock successful backup creation
        test_backup_file = os.path.join(backup_dir, 'test_backup.sql')
        with open(test_backup_file, 'w') as f:
            f.write("-- Test backup content")
        
        # Simulate backup process
        with patch.object(backup, '_execute_mysqldump') as mock_dump:
            mock_dump.return_value = test_backup_file
            
            result = backup.create_backup()
        
        # Assert
        assert result is True
        mock_dump.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

These examples demonstrate practical usage patterns and extension techniques for the sqlBackup system, covering basic usage, advanced monitoring, multi-database scenarios, custom extensions, and comprehensive testing approaches.

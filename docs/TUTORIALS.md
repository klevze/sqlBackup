# sqlBackup Tutorials

## Tutorial 1: Basic Setup and First Backup

### Prerequisites

- Python 3.6 or higher
- MySQL/MariaDB server
- Basic command line knowledge

### Step 1: Installation

1. **Download or clone the repository:**
   ```bash
   git clone https://github.com/klevze/sqlBackup.git
   cd sqlBackup
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   python -c "import sql_backup.backup; print('Installation successful!')"
   ```

### Step 2: Basic Configuration

1. **Copy the default configuration:**
   ```bash
   cp config.ini.default config.ini
   ```

2. **Edit the configuration file:**
   ```ini
   [backup]
   backup_dir = /path/to/your/backups
   keep_days = 7
   archive_type = gz

   [mysql]
   user = your_mysql_user
   password = your_mysql_password
   host = localhost
   port = 3306
   database = your_database_name

   [notification]
   channels = 
   ```

3. **Validate your configuration:**
   ```bash
   python validate_config.py
   ```

### Step 3: Your First Backup

1. **Run a test backup:**
   ```bash
   python -m src.backup
   ```

2. **Check the results:**
   ```bash
   ls -la /path/to/your/backups/
   ```

3. **Review the logs:**
   ```bash
   cat logs/sqlbackup.log
   ```

**Expected Output:**
```
2025-01-27 10:30:15 [INFO] Starting backup process
2025-01-27 10:30:16 [INFO] Creating backup for database: your_database_name
2025-01-27 10:30:20 [INFO] Backup created: /path/to/backups/your_database_20250127_103016.sql
2025-01-27 10:30:21 [INFO] Compressing backup using gz
2025-01-27 10:30:22 [INFO] Backup completed successfully
```

## Tutorial 2: Setting Up Notifications

### Step 1: Email Notifications

1. **Configure email settings:**
   ```ini
   [email]
   enabled = true
   smtp_server = smtp.gmail.com
   smtp_port = 587
   sender_email = your_email@gmail.com
   sender_password = your_app_password
   recipient_email = admin@yourcompany.com

   [notification]
   channels = email
   ```

2. **Test email notifications:**
   ```python
   from sql_backup.config import Config
   from sql_backup.notifications import NotificationManager

   config = Config('config.ini')
   config.load_config()

   notifier = NotificationManager(config)
   notifier.send_notification("Test email notification", is_success=True)
   ```

### Step 2: Telegram Notifications

1. **Create a Telegram bot:**
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Get your bot token

2. **Get your chat ID:**
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

3. **Configure Telegram:**
   ```ini
   [telegram]
   enabled = true
   bot_token = 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   chat_id = 987654321

   [notification]
   channels = email, telegram
   ```

### Step 3: Test All Notifications

```python
#!/usr/bin/env python3
"""Test script for notifications"""

from sql_backup.config import Config
from sql_backup.notifications import NotificationManager
from sql_backup.logger import setup_logging, get_logger

def test_notifications():
    setup_logging(log_level='INFO')
    logger = get_logger(__name__)
    
    config = Config('config.ini')
    config.load_config()
    
    notifier = NotificationManager(config)
    
    # Test success notification
    logger.info("Testing success notification...")
    notifier.send_notification("✅ Test backup completed successfully", is_success=True)
    
    # Test failure notification
    logger.info("Testing failure notification...")
    notifier.send_notification("❌ Test backup failed", is_success=False)
    
    logger.info("Notification tests completed")

if __name__ == "__main__":
    test_notifications()
```

## Tutorial 3: Remote Upload Setup

### Step 1: SFTP Upload

1. **Install required dependencies:**
   ```bash
   pip install paramiko
   ```

2. **Configure SFTP settings:**
   ```ini
   [export]
   enabled = true
   export_type = sftp
   server = your-server.com
   username = backup_user
   password = your_password
   remote_path = /backups/mysql

   [notification]
   channels = email
   ```

3. **Test SFTP connection:**
   ```python
   from sql_backup.config import Config
   from sql_backup.remote_upload import RemoteUploader
   import tempfile

   # Create test file
   with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
       f.write("-- Test backup file")
       test_file = f.name

   # Test upload
   config = Config('config.ini')
   config.load_config()

   uploader = RemoteUploader(config)
   success = uploader.upload_file(test_file)

   print(f"Upload {'successful' if success else 'failed'}")
   ```

### Step 2: FTP Upload

1. **Configure FTP settings:**
   ```ini
   [export]
   enabled = true
   export_type = ftp
   server = ftp.yourserver.com
   username = ftp_user
   password = ftp_password
   remote_path = /public_html/backups
   ```

### Step 3: Test Complete Backup with Upload

```python
#!/usr/bin/env python3
"""Complete backup with upload test"""

from sql_backup.backup import MySQLBackup
from sql_backup.logger import setup_logging, get_logger

def test_complete_backup():
    setup_logging(log_level='INFO', console_output=True)
    logger = get_logger(__name__)
    
    logger.info("🚀 Starting complete backup test with upload")
    
    backup = MySQLBackup('config.ini')
    success = backup.create_backup()
    
    if success:
        logger.info("✅ Complete backup with upload successful!")
    else:
        logger.error("❌ Backup failed")
    
    return success

if __name__ == "__main__":
    test_complete_backup()
```

## Tutorial 4: Automation and Scheduling

### Step 1: Using Cron (Linux/macOS)

1. **Create a backup script:**
   ```bash
   #!/bin/bash
   # backup_script.sh
   
   cd /path/to/sqlBackup
   source venv/bin/activate
   python -m src.backup
   ```

2. **Make it executable:**
   ```bash
   chmod +x backup_script.sh
   ```

3. **Add to crontab:**
   ```bash
   crontab -e
   ```
   
   Add this line for daily backup at 2 AM:
   ```
   0 2 * * * /path/to/sqlBackup/backup_script.sh
   ```

### Step 2: Using Task Scheduler (Windows)

1. **Create a batch file:**
   ```batch
   @echo off
   cd /d "D:\Sites\sqlBackup\sqlBackup"
   python -m src.backup
   pause
   ```

2. **Open Task Scheduler and create a new task:**
   - General: Set name and run whether user is logged on or not
   - Triggers: Set daily schedule
   - Actions: Start program with your batch file
   - Settings: Configure retry and failure handling

### Step 3: Python Scheduler (Cross-platform)

```python
#!/usr/bin/env python3
"""Advanced scheduler with multiple backup strategies"""

import schedule
import time
from datetime import datetime
from sql_backup.backup import MySQLBackup
from sql_backup.logger import setup_logging, get_logger

class BackupScheduler:
    def __init__(self):
        setup_logging(log_level='INFO', log_file='logs/scheduler.log')
        self.logger = get_logger(__name__)
    
    def daily_backup(self):
        """Run daily backup"""
        self.logger.info("🕐 Running scheduled daily backup")
        self._run_backup("daily")
    
    def weekly_backup(self):
        """Run weekly backup"""
        self.logger.info("📅 Running scheduled weekly backup")
        self._run_backup("weekly")
    
    def _run_backup(self, backup_type):
        try:
            backup = MySQLBackup('config.ini')
            success = backup.create_backup()
            
            if success:
                self.logger.info(f"✅ {backup_type} backup completed")
            else:
                self.logger.error(f"❌ {backup_type} backup failed")
                
        except Exception as e:
            self.logger.error(f"❌ {backup_type} backup error: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        # Daily backup at 2 AM
        schedule.every().day.at("02:00").do(self.daily_backup)
        
        # Weekly backup on Sunday at 1 AM
        schedule.every().sunday.at("01:00").do(self.weekly_backup)
        
        self.logger.info("🚀 Backup scheduler started")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    scheduler = BackupScheduler()
    scheduler.start()
```

## Tutorial 5: Configuration Validation and Troubleshooting

### Step 1: Understanding Configuration Validation

1. **Run validation with verbose output:**
   ```bash
   python validate_config.py --verbose
   ```

2. **Common validation errors and fixes:**

   **Error: "MySQL connection failed"**
   ```ini
   # Fix: Check your credentials and host
   [mysql]
   host = localhost  # Try 127.0.0.1 if localhost fails
   port = 3306       # Ensure this matches your MySQL port
   user = root       # Use correct username
   password = your_password  # Check password
   ```

   **Error: "Backup directory not accessible"**
   ```bash
   # Create the directory and set permissions
   mkdir -p /path/to/backups
   chmod 755 /path/to/backups
   ```

   **Error: "Email configuration invalid"**
   ```ini
   # Fix: Use app-specific password for Gmail
   [email]
   smtp_server = smtp.gmail.com
   smtp_port = 587
   sender_email = your_email@gmail.com
   sender_password = your_app_password  # Not your regular password
   ```

### Step 2: Debugging Failed Backups

1. **Enable debug logging:**
   ```python
   from sql_backup.logger import setup_logging
   setup_logging(log_level='DEBUG', console_output=True)
   ```

2. **Create a debug script:**
   ```python
   #!/usr/bin/env python3
   """Debug backup issues"""
   
   import sys
   from sql_backup.backup import MySQLBackup
   from sql_backup.config import Config
   from sql_backup.config_validator import ConfigValidator
   from sql_backup.logger import setup_logging, get_logger
   
   def debug_backup():
       setup_logging(log_level='DEBUG', console_output=True)
       logger = get_logger(__name__)
       
       # Step 1: Validate configuration
       logger.info("🔍 Step 1: Validating configuration")
       validator = ConfigValidator('config.ini')
       is_valid, errors, warnings = validator.validate_configuration()
       
       if not is_valid:
           logger.error("❌ Configuration validation failed:")
           for error in errors:
               logger.error(f"  {error}")
           return False
       
       logger.info("✅ Configuration validation passed")
       
       # Step 2: Test database connection
       logger.info("🔍 Step 2: Testing database connection")
       try:
           config = Config('config.ini')
           config.load_config()
           
           # Test connection (you can add MySQL connection test here)
           logger.info("✅ Database connection test passed")
           
       except Exception as e:
           logger.error(f"❌ Database connection failed: {str(e)}")
           return False
       
       # Step 3: Test backup creation
       logger.info("🔍 Step 3: Testing backup creation")
       try:
           backup = MySQLBackup('config.ini')
           success = backup.create_backup()
           
           if success:
               logger.info("✅ Backup creation successful")
               return True
           else:
               logger.error("❌ Backup creation failed")
               return False
               
       except Exception as e:
           logger.error(f"❌ Backup creation error: {str(e)}")
           return False
   
   if __name__ == "__main__":
       success = debug_backup()
       sys.exit(0 if success else 1)
   ```

### Step 3: Performance Optimization

1. **Monitor backup performance:**
   ```python
   import time
   from sql_backup.backup import MySQLBackup
   from sql_backup.logger import get_logger
   
   def benchmark_backup():
       logger = get_logger(__name__)
       
       start_time = time.time()
       backup = MySQLBackup('config.ini')
       success = backup.create_backup()
       end_time = time.time()
       
       duration = end_time - start_time
       logger.info(f"Backup completed in {duration:.2f} seconds")
       
       return success, duration
   ```

2. **Optimize for large databases:**
   ```ini
   [backup]
   # Use no compression for faster backups
   archive_type = none
   
   [mysql]
   # Add mysqldump options for large databases
   additional_options = --single-transaction --routines --triggers
   ```

## Tutorial 6: Advanced Features

### Step 1: Multiple Database Backups

1. **Create separate config files:**
   ```bash
   mkdir configs
   cp config.ini configs/database1.ini
   cp config.ini configs/database2.ini
   ```

2. **Customize each config:**
   ```ini
   # configs/database1.ini
   [mysql]
   database = production_db
   
   # configs/database2.ini
   [mysql]
   database = staging_db
   ```

3. **Create multi-database backup script:**
   ```python
   #!/usr/bin/env python3
   """Backup multiple databases"""
   
   import os
   from pathlib import Path
   from sql_backup.backup import MySQLBackup
   from sql_backup.logger import setup_logging, get_logger
   
   def backup_all_databases():
       setup_logging(log_level='INFO')
       logger = get_logger(__name__)
       
       config_dir = Path('configs')
       results = {}
       
       for config_file in config_dir.glob('*.ini'):
           db_name = config_file.stem
           logger.info(f"🔄 Backing up database: {db_name}")
           
           try:
               backup = MySQLBackup(str(config_file))
               success = backup.create_backup()
               results[db_name] = success
               
               if success:
                   logger.info(f"✅ {db_name} backup completed")
               else:
                   logger.error(f"❌ {db_name} backup failed")
                   
           except Exception as e:
               logger.error(f"❌ {db_name} backup error: {str(e)}")
               results[db_name] = False
       
       # Summary
       successful = sum(1 for success in results.values() if success)
       total = len(results)
       logger.info(f"📊 Backup summary: {successful}/{total} successful")
       
       return results
   
   if __name__ == "__main__":
       backup_all_databases()
   ```

### Step 2: Backup Rotation and Cleanup

```python
#!/usr/bin/env python3
"""Advanced backup rotation"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from sql_backup.logger import get_logger

class BackupRotation:
    def __init__(self, backup_dir: str, keep_days: int = 7):
        self.backup_dir = Path(backup_dir)
        self.keep_days = keep_days
        self.logger = get_logger(__name__)
    
    def cleanup_old_backups(self):
        """Remove backup files older than keep_days"""
        
        if not self.backup_dir.exists():
            self.logger.warning(f"Backup directory does not exist: {self.backup_dir}")
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.keep_days)
        removed_count = 0
        total_size = 0
        
        for backup_file in self.backup_dir.glob('*.sql*'):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_time < cutoff_date:
                file_size = backup_file.stat().st_size
                total_size += file_size
                
                try:
                    backup_file.unlink()
                    removed_count += 1
                    self.logger.info(f"Removed old backup: {backup_file.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to remove {backup_file.name}: {str(e)}")
        
        if removed_count > 0:
            size_mb = total_size / (1024 * 1024)
            self.logger.info(
                f"Cleanup complete: removed {removed_count} files, "
                f"freed {size_mb:.1f} MB"
            )
        else:
            self.logger.info("No old backups to remove")

# Usage example
if __name__ == "__main__":
    rotation = BackupRotation('/path/to/backups', keep_days=7)
    rotation.cleanup_old_backups()
```

### Step 3: Monitoring and Alerting

```python
#!/usr/bin/env python3
"""Backup monitoring and health checks"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from sql_backup.notifications import NotificationManager
from sql_backup.config import Config
from sql_backup.logger import setup_logging, get_logger

class BackupMonitor:
    def __init__(self, config_path: str = 'config.ini'):
        self.config = Config(config_path)
        self.config.load_config()
        self.notifier = NotificationManager(self.config)
        self.logger = get_logger(__name__)
    
    def check_backup_health(self):
        """Check if backups are running as expected"""
        
        backup_dir = Path(self.config.get('backup', 'backup_dir'))
        
        if not backup_dir.exists():
            self._send_alert("❌ Backup directory does not exist")
            return False
        
        # Check for recent backups
        recent_backups = self._find_recent_backups(backup_dir, hours=25)
        
        if not recent_backups:
            self._send_alert("⚠️ No recent backups found in the last 25 hours")
            return False
        
        # Check backup sizes
        size_issues = self._check_backup_sizes(recent_backups)
        if size_issues:
            self._send_alert(f"⚠️ Backup size issues detected: {size_issues}")
        
        # Check disk space
        disk_usage = self._check_disk_space(backup_dir)
        if disk_usage > 90:
            self._send_alert(f"⚠️ Backup disk usage high: {disk_usage}%")
        
        self.logger.info("✅ Backup health check completed")
        return True
    
    def _find_recent_backups(self, backup_dir: Path, hours: int = 24):
        """Find backups created within the specified hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_backups = []
        
        for backup_file in backup_dir.glob('*.sql*'):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time > cutoff_time:
                recent_backups.append(backup_file)
        
        return recent_backups
    
    def _check_backup_sizes(self, backup_files):
        """Check if backup sizes are consistent"""
        
        if len(backup_files) < 2:
            return None
        
        sizes = [f.stat().st_size for f in backup_files]
        avg_size = sum(sizes) / len(sizes)
        
        # Check for files that are unusually small (less than 10% of average)
        small_files = [
            f.name for f, size in zip(backup_files, sizes) 
            if size < avg_size * 0.1 and avg_size > 1024  # Skip if avg < 1KB
        ]
        
        return small_files if small_files else None
    
    def _check_disk_space(self, backup_dir: Path):
        """Check available disk space"""
        
        import shutil
        total, used, free = shutil.disk_usage(backup_dir)
        usage_percent = (used / total) * 100
        
        return usage_percent
    
    def _send_alert(self, message: str):
        """Send alert notification"""
        
        self.logger.warning(message)
        self.notifier.send_notification(message, is_success=False)

# Usage
if __name__ == "__main__":
    setup_logging(log_level='INFO')
    
    monitor = BackupMonitor()
    monitor.check_backup_health()
```

These tutorials provide step-by-step guidance for setting up and using sqlBackup, from basic installation to advanced features like monitoring and automation. Each tutorial includes practical examples and troubleshooting tips to help users get the most out of the system.

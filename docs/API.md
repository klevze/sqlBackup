# sqlBackup API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Module Structure](#module-structure)
3. [Core APIs](#core-apis)
4. [Configuration System](#configuration-system)
5. [Logging System](#logging-system)
6. [Validation System](#validation-system)
7. [Notification System](#notification-system)
8. [Remote Upload System](#remote-upload-system)
9. [Backup System](#backup-system)
10. [Usage Examples](#usage-examples)
11. [Extension Guide](#extension-guide)

## Overview

sqlBackup is a comprehensive MySQL backup solution with multiple notification channels, remote upload capabilities, and robust configuration management. This documentation provides detailed information about the internal APIs for developers who want to extend or integrate with the system.

## Module Structure

```
src/
├── __init__.py              # Package initialization
├── backup.py                # Main backup functionality
├── config.py                # Configuration management
├── config_validator.py      # Configuration validation
├── logger.py                # Logging system
├── notifications.py         # Notification handlers
└── remote_upload.py         # Remote upload handlers
```

## Core APIs

### backup.py

The main backup module that orchestrates the entire backup process.

#### Classes

##### `MySQLBackup`

Main backup class that handles MySQL database backups with compression and remote upload.

```python
class MySQLBackup:
    def __init__(self, config_path: str = None)
    def create_backup(self) -> bool
    def _execute_mysqldump(self) -> str
    def _compress_backup(self, backup_file: str) -> str
    def _cleanup_temp_files(self, files: List[str]) -> None
```

**Constructor Parameters:**
- `config_path` (str, optional): Path to configuration file. Defaults to `config.ini`

**Methods:**

###### `create_backup() -> bool`

Creates a complete backup including database dump, compression, and remote upload.

**Returns:**
- `bool`: True if backup was successful, False otherwise

**Raises:**
- `Exception`: Various exceptions related to database connection, file operations, or remote upload

**Example:**
```python
from sql_backup.backup import MySQLBackup

backup = MySQLBackup('config.ini')
success = backup.create_backup()
if success:
    print("Backup completed successfully")
else:
    print("Backup failed")
```

###### `_execute_mysqldump() -> str`

Executes mysqldump command to create database backup.

**Returns:**
- `str`: Path to the created backup file

**Raises:**
- `subprocess.CalledProcessError`: If mysqldump command fails

###### `_compress_backup(backup_file: str) -> str`

Compresses the backup file using the configured compression method.

**Parameters:**
- `backup_file` (str): Path to the backup file to compress

**Returns:**
- `str`: Path to the compressed file

**Supported Compression Formats:**
- `none`: No compression
- `gz`: Gzip compression
- `xz`: XZ compression  
- `tar.xz`: TAR with XZ compression
- `zip`: ZIP compression
- `rar`: RAR compression (requires WinRAR)

## Configuration System

### config.py

Manages application configuration with validation and type conversion.

#### Classes

##### `Config`

Main configuration class that loads and manages application settings.

```python
class Config:
    def __init__(self, config_path: str = 'config.ini')
    def load_config(self) -> None
    def get(self, section: str, key: str, fallback=None) -> Any
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool
    def getint(self, section: str, key: str, fallback: int = 0) -> int
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float
    def getlist(self, section: str, key: str, fallback: List = None) -> List[str]
```

**Constructor Parameters:**
- `config_path` (str): Path to the configuration file

**Methods:**

###### `load_config() -> None`

Loads and validates the configuration file.

**Raises:**
- `FileNotFoundError`: If configuration file doesn't exist
- `ValidationError`: If configuration validation fails

###### `get(section: str, key: str, fallback=None) -> Any`

Gets a configuration value as string.

**Parameters:**
- `section` (str): Configuration section name
- `key` (str): Configuration key name
- `fallback` (Any, optional): Default value if key not found

**Returns:**
- `Any`: Configuration value or fallback

**Example:**
```python
from sql_backup.config import Config

config = Config('config.ini')
config.load_config()

# Get string values
backup_dir = config.get('backup', 'backup_dir', '/tmp/backups')
mysql_host = config.get('mysql', 'host', 'localhost')

# Get boolean values
telegram_enabled = config.getboolean('telegram', 'enabled', False)

# Get integer values
mysql_port = config.getint('mysql', 'port', 3306)

# Get list values
notification_channels = config.getlist('notification', 'channels', [])
```

### Configuration Sections

#### `[backup]`
- `backup_dir`: Directory for storing backups
- `keep_days`: Number of days to keep backups
- `archive_type`: Compression format (none, gz, xz, tar.xz, zip, rar)

#### `[mysql]`
- `user`: MySQL username
- `password`: MySQL password
- `host`: MySQL server host
- `port`: MySQL server port
- `database`: Database name to backup

#### `[telegram]`
- `enabled`: Enable Telegram notifications
- `bot_token`: Telegram bot token
- `chat_id`: Telegram chat ID

#### `[email]`
- `enabled`: Enable email notifications
- `smtp_server`: SMTP server address
- `smtp_port`: SMTP server port
- `sender_email`: Sender email address
- `sender_password`: Sender email password
- `recipient_email`: Recipient email address

#### `[slack]`
- `enabled`: Enable Slack notifications
- `webhook_url`: Slack webhook URL

#### `[sms]`
- `enabled`: Enable SMS notifications
- `twilio_account_sid`: Twilio account SID
- `twilio_auth_token`: Twilio auth token
- `from_phone`: Sender phone number
- `to_phone`: Recipient phone number

#### `[notification]`
- `channels`: Comma-separated list of notification channels

#### `[export]`
- `enabled`: Enable remote upload
- `export_type`: Upload method (sftp, ftp, scp)
- `server`: Remote server address
- `username`: Remote server username
- `password`: Remote server password
- `remote_path`: Remote directory path

## Logging System

### logger.py

Comprehensive logging system with colored console output and file rotation.

#### Classes

##### `ColoredFormatter`

Custom formatter that adds colors to console log output.

```python
class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str
```

##### `SqlBackupLogger`

Main logger class that configures both console and file logging.

```python
class SqlBackupLogger:
    def __init__(self, name: str = 'sqlbackup', log_level: str = 'INFO', 
                 log_file: str = None, console_output: bool = True)
    def get_logger(self) -> logging.Logger
```

**Constructor Parameters:**
- `name` (str): Logger name
- `log_level` (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file` (str, optional): Path to log file
- `console_output` (bool): Enable console output

#### Functions

##### `setup_logging(log_level: str = 'INFO', log_file: str = None, console_output: bool = True) -> None`

Sets up the global logging configuration.

**Parameters:**
- `log_level` (str): Logging level
- `log_file` (str, optional): Path to log file
- `console_output` (bool): Enable console output

##### `get_logger(name: str = None) -> logging.Logger`

Gets a logger instance.

**Parameters:**
- `name` (str, optional): Logger name

**Returns:**
- `logging.Logger`: Logger instance

**Example:**
```python
from sql_backup.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level='DEBUG', log_file='logs/backup.log')

# Get logger
logger = get_logger(__name__)

# Use logger
logger.info("Starting backup process")
logger.warning("Configuration file not found, using defaults")
logger.error("Failed to connect to database")
logger.debug("Processing file: backup_20250127.sql")
```

## Validation System

### config_validator.py

Robust configuration validation with detailed error reporting.

#### Classes

##### `ConfigValidator`

Validates configuration files and provides detailed error messages.

```python
class ConfigValidator:
    def __init__(self, config_path: str)
    def validate_configuration(self) -> Tuple[bool, List[str], List[str]]
    def _validate_section(self, section: str, config: configparser.ConfigParser) -> Tuple[List[str], List[str]]
```

**Constructor Parameters:**
- `config_path` (str): Path to configuration file to validate

**Methods:**

###### `validate_configuration() -> Tuple[bool, List[str], List[str]]`

Validates the entire configuration file.

**Returns:**
- `Tuple[bool, List[str], List[str]]`: (is_valid, errors, warnings)

**Example:**
```python
from sql_backup.config_validator import ConfigValidator

validator = ConfigValidator('config.ini')
is_valid, errors, warnings = validator.validate_configuration()

if not is_valid:
    print("Configuration validation failed:")
    for error in errors:
        print(f"ERROR: {error}")

if warnings:
    print("Configuration warnings:")
    for warning in warnings:
        print(f"WARNING: {warning}")
```

#### Validation Rules

The validator checks:
- **Required Sections**: Ensures all necessary sections exist
- **Required Fields**: Validates that required fields are present
- **Data Types**: Checks integers, booleans, emails, URLs, phone numbers
- **File Paths**: Verifies that files and directories exist
- **Cross-Dependencies**: Ensures related configuration options are consistent

## Notification System

### notifications.py

Multi-channel notification system supporting various platforms.

#### Classes

##### `NotificationManager`

Main notification manager that handles multiple notification channels.

```python
class NotificationManager:
    def __init__(self, config: Config)
    def send_notification(self, message: str, is_success: bool = True) -> None
    def _send_telegram(self, message: str) -> bool
    def _send_email(self, message: str) -> bool
    def _send_slack(self, message: str) -> bool
    def _send_sms(self, message: str) -> bool
    def _send_viber(self, message: str) -> bool
```

**Constructor Parameters:**
- `config` (Config): Configuration instance

**Methods:**

###### `send_notification(message: str, is_success: bool = True) -> None`

Sends notification through all enabled channels.

**Parameters:**
- `message` (str): Notification message
- `is_success` (bool): Whether this is a success or failure notification

**Example:**
```python
from sql_backup.config import Config
from sql_backup.notifications import NotificationManager

config = Config('config.ini')
config.load_config()

notifier = NotificationManager(config)

# Send success notification
notifier.send_notification("Backup completed successfully", is_success=True)

# Send failure notification
notifier.send_notification("Backup failed: Database connection error", is_success=False)
```

##### Individual Notification Methods

Each notification channel has its own private method:

- `_send_telegram()`: Sends via Telegram Bot API
- `_send_email()`: Sends via SMTP
- `_send_slack()`: Sends via Slack webhooks
- `_send_sms()`: Sends via Twilio SMS API
- `_send_viber()`: Sends via Viber API

## Remote Upload System

### remote_upload.py

Handles uploading backup files to remote servers via multiple protocols.

#### Classes

##### `RemoteUploader`

Manages remote upload operations with support for SFTP, FTP, and SCP.

```python
class RemoteUploader:
    def __init__(self, config: Config)
    def upload_file(self, local_file_path: str) -> bool
    def _upload_sftp(self, local_file_path: str) -> bool
    def _upload_ftp(self, local_file_path: str) -> bool
    def _upload_scp(self, local_file_path: str) -> bool
```

**Constructor Parameters:**
- `config` (Config): Configuration instance

**Methods:**

###### `upload_file(local_file_path: str) -> bool`

Uploads a file to the configured remote server.

**Parameters:**
- `local_file_path` (str): Path to the local file to upload

**Returns:**
- `bool`: True if upload was successful, False otherwise

**Example:**
```python
from sql_backup.config import Config
from sql_backup.remote_upload import RemoteUploader

config = Config('config.ini')
config.load_config()

uploader = RemoteUploader(config)
success = uploader.upload_file('/path/to/backup.sql.gz')

if success:
    print("File uploaded successfully")
else:
    print("Upload failed")
```

## Usage Examples

### Complete Backup Workflow

```python
from sql_backup.backup import MySQLBackup
from sql_backup.config import Config
from sql_backup.logger import setup_logging, get_logger

# Setup logging
setup_logging(log_level='INFO', log_file='logs/backup.log')
logger = get_logger(__name__)

try:
    # Create backup instance
    backup = MySQLBackup('config.ini')
    
    # Perform backup
    logger.info("Starting backup process")
    success = backup.create_backup()
    
    if success:
        logger.info("Backup completed successfully")
    else:
        logger.error("Backup failed")
        
except Exception as e:
    logger.error(f"Backup process failed: {str(e)}")
```

### Manual Configuration and Notification

```python
from sql_backup.config import Config
from sql_backup.notifications import NotificationManager
from sql_backup.logger import get_logger

logger = get_logger(__name__)

# Load configuration
config = Config('config.ini')
config.load_config()

# Create notification manager
notifier = NotificationManager(config)

# Send custom notification
try:
    notifier.send_notification("Custom backup process completed", is_success=True)
    logger.info("Notification sent successfully")
except Exception as e:
    logger.error(f"Failed to send notification: {str(e)}")
```

### Configuration Validation

```python
from sql_backup.config_validator import ConfigValidator
from sql_backup.logger import get_logger

logger = get_logger(__name__)

# Validate configuration
validator = ConfigValidator('config.ini')
is_valid, errors, warnings = validator.validate_configuration()

if not is_valid:
    logger.error("Configuration validation failed:")
    for error in errors:
        logger.error(f"  {error}")
    exit(1)

if warnings:
    logger.warning("Configuration warnings:")
    for warning in warnings:
        logger.warning(f"  {warning}")

logger.info("Configuration validation passed")
```

## Extension Guide

### Adding New Notification Channels

To add a new notification channel:

1. **Add configuration section** in your config file:
```ini
[mynewchannel]
enabled = true
api_key = your_api_key
channel_id = your_channel_id
```

2. **Extend NotificationManager** in `notifications.py`:
```python
def _send_mynewchannel(self, message: str) -> bool:
    """Send notification via new channel."""
    try:
        if not self.config.getboolean('mynewchannel', 'enabled', False):
            return False
            
        api_key = self.config.get('mynewchannel', 'api_key')
        channel_id = self.config.get('mynewchannel', 'channel_id')
        
        # Implement your notification logic here
        # ... your API call code ...
        
        self.logger.info("New channel notification sent successfully")
        return True
        
    except Exception as e:
        self.logger.error(f"Failed to send new channel notification: {str(e)}")
        return False
```

3. **Update channel list** in `send_notification()`:
```python
def send_notification(self, message: str, is_success: bool = True) -> None:
    channels = self.config.getlist('notification', 'channels', [])
    
    for channel in channels:
        if channel.lower() == 'mynewchannel':
            self._send_mynewchannel(message)
```

### Adding New Upload Protocols

To add a new upload protocol:

1. **Add configuration** for the new protocol
2. **Extend RemoteUploader** in `remote_upload.py`:
```python
def _upload_newprotocol(self, local_file_path: str) -> bool:
    """Upload file via new protocol."""
    try:
        # Implement your upload logic here
        # ... your upload code ...
        
        self.logger.info(f"File uploaded successfully via new protocol")
        return True
        
    except Exception as e:
        self.logger.error(f"New protocol upload failed: {str(e)}")
        return False
```

3. **Update protocol selection** in `upload_file()`:
```python
def upload_file(self, local_file_path: str) -> bool:
    export_type = self.config.get('export', 'export_type', 'sftp')
    
    if export_type == 'newprotocol':
        return self._upload_newprotocol(local_file_path)
```

### Adding New Compression Formats

To add a new compression format:

1. **Extend compression logic** in `backup.py`:
```python
def _compress_backup(self, backup_file: str) -> str:
    archive_type = self.config.get('backup', 'archive_type', 'none')
    
    if archive_type == 'newformat':
        return self._compress_newformat(backup_file)

def _compress_newformat(self, backup_file: str) -> str:
    """Compress backup using new format."""
    compressed_file = f"{backup_file}.newext"
    
    try:
        # Implement your compression logic here
        # ... your compression code ...
        
        os.remove(backup_file)  # Remove original
        self.logger.info(f"Backup compressed using new format: {compressed_file}")
        return compressed_file
        
    except Exception as e:
        self.logger.error(f"Failed to compress using new format: {str(e)}")
        raise
```

## Best Practices

### Error Handling
- Always use try-catch blocks for external operations
- Log errors with appropriate detail level
- Return boolean success indicators from methods
- Raise exceptions for critical failures

### Logging
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include context information in log messages
- Use structured logging for better parsing

### Configuration
- Validate configuration early in the application lifecycle
- Provide sensible defaults for optional parameters
- Use type-specific getters (getboolean, getint, etc.)

### Security
- Never log sensitive information (passwords, tokens)
- Validate all external inputs
- Use secure connection methods for remote operations

This API documentation provides comprehensive coverage of the sqlBackup system for developers who want to understand, extend, or integrate with the codebase.

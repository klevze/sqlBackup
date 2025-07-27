# sqlBackup

**sqlBackup** is a modern Python-based backup tool for MySQL databases. It supports advanced features such as multiple archiving formats, multi-channel notifications (Telegram, Email, Slack, SMS via Twilio, Viber, etc.), and remote uploads via protocols like SFTP, FTP, or SCP. This project is a significant upgrade from the original BackupSQL shell script.

## Features

- **MySQL Database Backup:**  
  Dumps databases using `mysqldump` with support for routines and events.
  
- **Flexible Archiving:**  
  Archive your backups in various formats:
  - `none` (plain SQL dump)
  - `gz` (gzip-compressed)
  - `xz` (xz-compressed)
  - `tar.xz` (tar archive compressed with xz)
  - `zip` (ZIP archive)
  - `rar` (RAR archive)

- **Multi-Channel Notifications:**  
  Send notifications via:
  - Telegram
  - Email
  - Slack
  - SMS (via Twilio)
  - Viber
  - Messenger (stub, to be implemented)
  
- **Remote Uploads:**  
  Optionally upload backups to a remote server using SFTP, FTP, or SCP with configurable scheduling (daily, first day, last day, specific weekday, or a numeric day of the month).

- **Wildcard Support for Ignored Databases:**  
  Use wildcard patterns (e.g., `projekti_*`) in `ignored_databases` to skip databases by name pattern.

- **Modular & Maintainable:**  
  Code is organized into multiple modules (configuration, backup logic, notifications, remote upload) for easier maintenance and extensibility.

- **Graceful Interruption:**  
  Handles CTRL+C gracefully, providing a user-friendly exit message.

- **Comprehensive Logging:**  
  Professional logging system with:
  - Colored console output with different levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - File logging with automatic rotation (10MB max, 5 backup files)
  - Detailed logging for debugging and audit trails
  - Configurable log levels and output destinations

- **Configuration Validation:**  
  Robust validation system that:
  - Validates all configuration parameters with detailed error messages
  - Checks file paths, email formats, phone numbers, and URL formats
  - Ensures required sections and fields are present
  - Validates data types and allowed values
  - Provides helpful warnings for potential issues
  - Includes a standalone validation tool for testing configurations

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Configuration Tutorial](#configuration-tutorial)
- [Usage](#usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Documentation

### For Users
- **[Installation Guide](#installation)** - Quick setup instructions
- **[Configuration Guide](#configuration-parameters)** - Complete configuration reference
- **[Tutorials](docs/TUTORIALS.md)** - Step-by-step tutorials for common tasks
- **[Configuration Validation](#configuration-validation)** - Validate your setup

### For Developers
- **[API Documentation](docs/API.md)** - Complete API reference and code documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup, architecture, and contribution guidelines
- **[Code Examples](docs/EXAMPLES.md)** - Practical examples and extension patterns
- **[Testing Guide](docs/DEVELOPER_GUIDE.md#testing-guidelines)** - Testing strategies and examples

## Installation

### Prerequisites

1. **Python 3.6+** is required.
2. **MySQL or MariaDB** client tools installed (e.g., `mysql`, `mysqldump`).

### Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/klevze/sqlBackup.git
   cd sqlBackup
   ```

2. **Install the Package:**
   
   **Option 1: Production installation (Recommended)**
   ```bash
   pip install .
   ```
   
   **Option 2: Development installation**
   ```bash
   pip install -e .
   ```
   
   **Option 3: Quick install scripts**
   
   For Linux/macOS:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   
   For Windows:
   ```batch
   install.bat
   ```
   
   **Option 4: Manual dependency installation**
   ```bash
   pip install -r requirements.txt
   ```

   **Required dependencies:**
   - `requests`: For HTTP requests (used in notifications and remote uploads).
   - `paramiko`: For SFTP uploads.
   - `twilio`: For sending SMS notifications.

3. **Project Structure:**
   The project is organized as a modern Python package:

   ```text
   sqlBackup/
   ├── setup.py              # Package installation and metadata
   ├── requirements.txt      # Runtime dependencies
   ├── requirements-dev.txt  # Development dependencies
   ├── config.ini.default    # Default configuration template
   ├── example.py            # Usage examples
   ├── validate_config.py    # Standalone validation tool
   ├── sql_backup/           # Main package
   │   ├── __init__.py       # Package initialization
   │   ├── __main__.py       # Module execution support
   │   ├── main.py           # Application entry point
   │   ├── backup.py         # Database backup functionality
   │   ├── config.py         # Configuration management
   │   ├── config_validator.py # Configuration validation
   │   ├── logger.py         # Logging system
   │   ├── notifications.py  # Multi-channel notifications
   │   └── remote_upload.py  # Remote upload capabilities
   ├── tests/                # Comprehensive test suite
   │   └── test_*.py         # Individual test modules
   └── docs/                 # Complete documentation
       ├── API.md            # API reference
       ├── DEVELOPER_GUIDE.md # Development guide
       ├── EXAMPLES.md       # Code examples
       └── TUTORIALS.md      # User tutorials
   ```

3. **Configuration File Setup:**
   - **Important:** Do not modify `config.ini.default` directly. Instead, copy it:

     ```bash
     cp config.ini.default config.ini
     ```

   - Open `config.ini` and adjust the settings to match your environment (e.g., MySQL credentials, notification channel settings, remote upload settings, etc.).

   > **Note:** If you pull new changes from this repo in the future, your local `config.ini` will remain untouched, preserving your production settings.

4. **(Optional) Unit Tests:**
   - If you want to run the included unit tests, you can install development dependencies and run:

     ```bash
     pip install -r requirements-dev.txt
     python3 -m unittest discover
     ```

## Logging

The application uses a comprehensive logging system that provides:

- **Console Logging:** Colored output with different levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File Logging:** Automatic log rotation with 10MB max file size and 5 backup files
- **Configurable Levels:** Control logging verbosity via configuration

Log files are stored in the `logs/` directory by default and include detailed information for debugging and audit trails.

## Configuration Validation

The tool includes a standalone configuration validator that checks your configuration before running backups:

   ```bash
   # Validate the default config file
   python validate_config.py

   # Validate a specific config file
   python validate_config.py --config path/to/your/config.ini

   # Verbose output showing all checks
   python validate_config.py --verbose
   ```

The validator will check:
- Required sections and parameters are present
- Data types are correct (integers, booleans, emails, URLs)
- File and directory paths exist and are accessible
- Email formats are valid
- Phone number formats are correct for SMS notifications
- URL formats are valid for webhooks
- Cross-dependencies between configuration options

## Configuration Parameters

The `config.ini` file is the central configuration file for **sqlBackup**. It is divided into several sections:

### [backup]
- **backup_dir:** Directory where backup files will be stored.
- **backup_retention_days:** Number of days to retain backups.
- **archive_format:** Archive format to use. Options: `none`, `gz`, `xz`, `tar.xz`, `zip`, `rar`.

### [mysql]
- **user, password, host:** MySQL credentials.
- **mysql_path:** Path to the MySQL client.
- **mysqldump_path:** Path to the mysqldump utility.
- **ignored_databases:** Comma-separated list of databases to skip.
  - **Now supports wildcards:** e.g. `sys, mysql, projekti_*`. Any database name matching `projekti_*` will be ignored (e.g., `projekti_alpha`, `projekti_1`).

### [telegram]
- **enabled:** Enable or disable Telegram notifications.
- **telegram_token:** Your Telegram Bot API token.
- **telegram_chatid:** Chat ID for notifications.
- **telegram_serverid:** A friendly name for your server (used in messages).

### [email]
- **enabled:** Enable or disable email notifications.
- **smtp_server, smtp_port:** SMTP server details.
- **username, password:** SMTP credentials.
- **from_address:** Sender email address.
- **to_addresses:** Comma-separated recipient email addresses.

### [slack]
- **enabled:** Enable or disable Slack notifications.
- **webhook_url:** Slack webhook URL for notifications.

### [sms]
- **enabled:** Enable or disable SMS notifications.
- **provider:** Currently supports "twilio".
- **account_sid, auth_token:** Twilio credentials.
- **from_number:** Twilio phone number.
- **to_numbers:** Comma-separated list of recipient phone numbers.

### [viber]
- **enabled:** Enable or disable Viber notifications.
- **auth_token:** Your Viber bot authentication token.
- **receiver_id:** Viber receiver ID (the user ID to send messages to).
- **sender_name:** (Optional) Sender name; defaults to "BackupBot" if not provided.

### [messenger]
- **enabled:** Enable or disable Messenger notifications.
- **page_access_token, recipient_id:** Messenger API credentials (currently not implemented).

### [notification]
- **channels:** Comma-separated list of notification channels to use (e.g., `telegram, email, slack, sms, viber`).

### [export]
- **include_routines:** Include stored procedures and functions.
- **include_events:** Include scheduled events.
- **column_statistics:** If set to false, the script adds `--column-statistics=0` to the dump command (helpful for older servers).

### [logging]
- **level:** Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- **enable_console:** Enable or disable colored console output.
- **enable_file_logging:** Enable or disable file logging with automatic rotation.
- **log_directory:** Directory where log files will be stored (created automatically).

### [remote]
- **upload_enabled:** Enable or disable remote upload of backups.
- **protocol:** Upload protocol (`sftp`, `ftp`, or `scp`).
- **host, port:** Remote server details.
- **username, password:** Remote server credentials.
- **remote_directory:** Remote directory where backups will be stored.
- **upload_schedule:** When to perform the upload (e.g., `daily`, `first_day`, `last_day`, weekday, or a specific day).
- **key_file, key_passphrase:** (Optional) For SFTP public key authentication.

## Usage

To run **sqlBackup**, you have several options depending on how you installed it:

### Console Script (After pip install):
```bash
# Primary command
sql-backup

# Alternative name (backward compatibility)
sqlbackup
```

### Module Execution:
```bash
# Run as Python module
python -m sql_backup
```

### Development/Direct Execution:
```bash
# From source directory (development)
python -m sql_backup

# Standalone validation tool
python validate_config.py config.ini
```

### Programmatic Usage:
```python
# Import and use programmatically
from sql_backup import main
from sql_backup.backup import MySQLBackup
from sql_backup.config import load_config

# Run complete backup process
main()

# Or use individual components
config = load_config()
backup = MySQLBackup(config)
```

The script will:
- Connect to MySQL and dump databases (skipping those in `ignored_databases`, including wildcards).
- Archive each dump according to the specified format.
- Display a summary table with database name, backup status, elapsed time, dump size, and archive size.
- Send notifications via the enabled channels.
- Upload backups to a remote server if enabled and if the schedule condition is met.

## Contributing

Contributions are welcome! Feel free to fork the repository, open issues, and submit pull requests. Please follow the existing code style and include tests for new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

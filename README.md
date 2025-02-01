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

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Configuration Tutorial](#configuration-tutorial)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

1. **Python 3.6+** is required.
2. **MySQL or MariaDB** client tools installed (e.g., `mysql`, `mysqldump`).
3. Install the necessary Python packages using `pip`:
   ```bash
   pip install requests paramiko twilio fnmatch 
   ```
   - `requests`: For HTTP requests (used in notifications and remote uploads).
   - `paramiko`: For SFTP uploads.
   - `twilio`: For sending SMS notifications.
   - `fnmatch`: For wildcard support

### Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/sqlBackup.git
   cd sqlBackup
   ```

2. **Project Structure:**
   The project is organized as follows:
   ```
   sqlBackup/
   ├── config.ini.default    # Default configuration file (do not modify directly)
   ├── main.py               # Main entry point
   └── src/
       ├── __init__.py       # Package marker (can be empty)
       ├── config.py         # Configuration loader
       ├── backup.py         # Backup logic (MySQL dump, archiving, table output)
       ├── notifications.py  # Multi-channel notification functions
       └── remote_upload.py  # Remote upload functionality
   ```

3. **Configuration File Setup:**
   - **Important:** Do not modify `config.ini.default` directly. Instead, copy it:
     ```bash
     cp config.ini.default config.ini
     ```
   - Open `config.ini` and adjust the settings to match your environment (e.g., MySQL credentials, notification channel settings, remote upload settings, etc.).

   > **Note:** If you pull new changes from this repo in the future, your local `config.ini` will remain untouched, preserving your production settings.

4. **(Optional) Unit Tests:**
   - If you want to run the included unit tests (if any), install `unittest` (bundled with Python), plus any additional test dependencies, and run:
     ```bash
     python3 -m unittest discover
     ```

## Configuration Tutorial

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

### [remote]
- **upload_enabled:** Enable or disable remote upload of backups.
- **protocol:** Upload protocol (`sftp`, `ftp`, or `scp`).
- **host, port:** Remote server details.
- **username, password:** Remote server credentials.
- **remote_directory:** Remote directory where backups will be stored.
- **upload_schedule:** When to perform the upload (e.g., `daily`, `first_day`, `last_day`, weekday, or a specific day).
- **key_file, key_passphrase:** (Optional) For SFTP public key authentication.

## Usage

To run **sqlBackup**, execute the main entry point from the project root:

```bash
python3 main.py
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

"""
Configuration validation module for sqlBackup.
Provides comprehensive validation of configuration parameters with detailed error reporting.
"""

import os
import re
import configparser
from typing import Dict, List, Tuple, Any, Optional
from .logger import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


class ConfigValidator:
    """Comprehensive configuration validator for sqlBackup."""
    
    def __init__(self):
        """Initialize the validator with validation rules."""
        self.errors = []
        self.warnings = []
        
        # Define required sections and their required fields
        self.required_sections = {
            'backup': ['backup_dir', 'archive_format'],
            'mysql': ['user', 'host', 'mysql_path', 'mysqldump_path']
        }
        
        # Define valid values for specific fields
        self.valid_values = {
            'archive_format': ['none', 'gz', 'xz', 'tar.xz', 'zip', 'rar'],
            'protocol': ['sftp', 'ftp', 'scp'],
            'level': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'provider': ['twilio']
        }
        
        # Define field types
        self.field_types = {
            'backup_retention_days': int,
            'smtp_port': int,
            'port': int,
            'min_api_version': int,
            'enabled': bool,
            'enable_console': bool,
            'enable_file_logging': bool,
            'upload_enabled': bool,
            'include_routines': bool,
            'include_events': bool,
            'column_statistics': bool
        }
        
        # Define path fields that should exist
        self.path_fields = {
            'backup_dir': 'directory',
            'mysql_path': 'file',
            'mysqldump_path': 'file',
            'key_file': 'file',
            'log_directory': 'directory'
        }
    
    def validate_config(self, config: configparser.ConfigParser) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the entire configuration.
        
        Args:
            config: ConfigParser instance to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        logger.info("Starting comprehensive configuration validation")
        self.errors = []
        self.warnings = []
        
        # Validate required sections and fields
        self._validate_required_sections(config)
        
        # Validate individual sections
        self._validate_backup_section(config)
        self._validate_mysql_section(config)
        self._validate_logging_section(config)
        self._validate_notification_sections(config)
        self._validate_remote_section(config)
        self._validate_export_section(config)
        
        # Validate field types and values
        self._validate_field_types(config)
        self._validate_field_values(config)
        self._validate_paths(config)
        
        # Cross-section validation
        self._validate_cross_section_dependencies(config)
        
        is_valid = len(self.errors) == 0
        
        if is_valid:
            logger.info("Configuration validation passed successfully")
        else:
            logger.error(f"Configuration validation failed with {len(self.errors)} errors")
            
        if self.warnings:
            logger.warning(f"Configuration validation completed with {len(self.warnings)} warnings")
            
        return is_valid, self.errors, self.warnings
    
    def _validate_required_sections(self, config: configparser.ConfigParser):
        """Validate that required sections and fields exist."""
        for section_name, required_fields in self.required_sections.items():
            if not config.has_section(section_name):
                self.errors.append(f"Required section [{section_name}] is missing")
                continue
                
            for field in required_fields:
                if not config.has_option(section_name, field):
                    self.errors.append(f"Required field '{field}' is missing in section [{section_name}]")
    
    def _validate_backup_section(self, config: configparser.ConfigParser):
        """Validate backup section parameters."""
        if not config.has_section('backup'):
            return
            
        # Validate backup directory
        backup_dir = config.get('backup', 'backup_dir', fallback=None)
        if backup_dir:
            try:
                # Try to create the directory if it doesn't exist
                os.makedirs(backup_dir, exist_ok=True)
                if not os.access(backup_dir, os.W_OK):
                    self.errors.append(f"Backup directory '{backup_dir}' is not writable")
            except Exception as e:
                self.errors.append(f"Cannot create or access backup directory '{backup_dir}': {e}")
        
        # Validate retention days
        try:
            retention_days = config.getint('backup', 'backup_retention_days', fallback=30)
            if retention_days < 1:
                self.errors.append("backup_retention_days must be at least 1")
            elif retention_days > 365:
                self.warnings.append("backup_retention_days is very high (>365 days), ensure you have enough disk space")
        except ValueError:
            self.errors.append("backup_retention_days must be a valid integer")
    
    def _validate_mysql_section(self, config: configparser.ConfigParser):
        """Validate MySQL section parameters."""
        if not config.has_section('mysql'):
            return
            
        # Validate MySQL executables
        mysql_path = config.get('mysql', 'mysql_path', fallback=None)
        mysqldump_path = config.get('mysql', 'mysqldump_path', fallback=None)
        
        if mysql_path and not os.path.isfile(mysql_path):
            self.errors.append(f"MySQL client not found at '{mysql_path}'")
        if mysqldump_path and not os.path.isfile(mysqldump_path):
            self.errors.append(f"mysqldump not found at '{mysqldump_path}'")
            
        # Validate ignored databases patterns
        ignored_dbs = config.get('mysql', 'ignored_databases', fallback='')
        if ignored_dbs:
            patterns = [p.strip() for p in ignored_dbs.split(',')]
            for pattern in patterns:
                if not pattern:
                    self.warnings.append("Empty pattern found in ignored_databases")
                elif len(pattern) > 64:
                    self.warnings.append(f"Very long database pattern '{pattern}' may cause issues")
    
    def _validate_logging_section(self, config: configparser.ConfigParser):
        """Validate logging section parameters."""
        if not config.has_section('logging'):
            self.warnings.append("No [logging] section found, using default logging settings")
            return
            
        # Validate log directory
        log_dir = config.get('logging', 'log_directory', fallback='logs')
        try:
            os.makedirs(log_dir, exist_ok=True)
            if not os.access(log_dir, os.W_OK):
                self.errors.append(f"Log directory '{log_dir}' is not writable")
        except Exception as e:
            self.errors.append(f"Cannot create or access log directory '{log_dir}': {e}")
    
    def _validate_notification_sections(self, config: configparser.ConfigParser):
        """Validate notification-related sections."""
        # Check for notification configuration
        has_notification_config = False
        
        # Check individual notification sections
        notification_sections = ['telegram', 'email', 'slack', 'sms', 'viber', 'messenger']
        enabled_notifications = []
        
        for section in notification_sections:
            if config.has_section(section) and config.getboolean(section, 'enabled', fallback=False):
                enabled_notifications.append(section)
                has_notification_config = True
                self._validate_notification_section(config, section)
        
        # Check notification channels configuration
        if config.has_section('notification'):
            channels = config.get('notification', 'channels', fallback='')
            if channels:
                channel_list = [ch.strip().lower() for ch in channels.split(',')]
                for channel in channel_list:
                    if channel not in notification_sections:
                        self.errors.append(f"Unknown notification channel '{channel}' in [notification] section")
                    elif not config.has_section(channel):
                        self.warnings.append(f"Notification channel '{channel}' configured but no [{channel}] section found")
        
        if not has_notification_config:
            self.warnings.append("No notification channels are enabled")
    
    def _validate_notification_section(self, config: configparser.ConfigParser, section: str):
        """Validate specific notification section."""
        if section == 'telegram':
            self._validate_telegram_config(config)
        elif section == 'email':
            self._validate_email_config(config)
        elif section == 'slack':
            self._validate_slack_config(config)
        elif section == 'sms':
            self._validate_sms_config(config)
        elif section == 'viber':
            self._validate_viber_config(config)
    
    def _validate_telegram_config(self, config: configparser.ConfigParser):
        """Validate Telegram notification configuration."""
        token = config.get('telegram', 'telegram_token', fallback='')
        chat_id = config.get('telegram', 'telegram_chatid', fallback='')
        
        if not token:
            self.errors.append("telegram_token is required when Telegram notifications are enabled")
        elif not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            self.errors.append("telegram_token format appears invalid (should be 'botid:token')")
            
        if not chat_id:
            self.errors.append("telegram_chatid is required when Telegram notifications are enabled")
        elif not (chat_id.isdigit() or (chat_id.startswith('-') and chat_id[1:].isdigit())):
            self.warnings.append("telegram_chatid should be numeric (user ID or group ID)")
    
    def _validate_email_config(self, config: configparser.ConfigParser):
        """Validate email notification configuration."""
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password', 'from_address', 'to_addresses']
        
        for field in required_fields:
            if not config.get('email', field, fallback=''):
                self.errors.append(f"Email field '{field}' is required when email notifications are enabled")
        
        # Validate email addresses
        from_addr = config.get('email', 'from_address', fallback='')
        to_addrs = config.get('email', 'to_addresses', fallback='')
        
        if from_addr and not self._is_valid_email(from_addr):
            self.errors.append(f"Invalid from_address email format: '{from_addr}'")
            
        if to_addrs:
            for addr in [a.strip() for a in to_addrs.split(',')]:
                if addr and not self._is_valid_email(addr):
                    self.errors.append(f"Invalid to_addresses email format: '{addr}'")
        
        # Validate SMTP port
        try:
            port = config.getint('email', 'smtp_port', fallback=587)
            if port < 1 or port > 65535:
                self.errors.append("SMTP port must be between 1 and 65535")
        except ValueError:
            self.errors.append("SMTP port must be a valid integer")
    
    def _validate_slack_config(self, config: configparser.ConfigParser):
        """Validate Slack notification configuration."""
        webhook_url = config.get('slack', 'webhook_url', fallback='')
        
        if not webhook_url:
            self.errors.append("webhook_url is required when Slack notifications are enabled")
        elif not webhook_url.startswith('https://hooks.slack.com/'):
            self.warnings.append("webhook_url doesn't appear to be a valid Slack webhook URL")
    
    def _validate_sms_config(self, config: configparser.ConfigParser):
        """Validate SMS notification configuration."""
        required_fields = ['account_sid', 'auth_token', 'from_number', 'to_numbers']
        
        for field in required_fields:
            if not config.get('sms', field, fallback=''):
                self.errors.append(f"SMS field '{field}' is required when SMS notifications are enabled")
        
        # Validate phone numbers
        from_number = config.get('sms', 'from_number', fallback='')
        to_numbers = config.get('sms', 'to_numbers', fallback='')
        
        if from_number and not self._is_valid_phone(from_number):
            self.warnings.append(f"from_number format may be invalid: '{from_number}' (should include country code)")
            
        if to_numbers:
            for number in [n.strip() for n in to_numbers.split(',')]:
                if number and not self._is_valid_phone(number):
                    self.warnings.append(f"to_numbers format may be invalid: '{number}' (should include country code)")
    
    def _validate_viber_config(self, config: configparser.ConfigParser):
        """Validate Viber notification configuration."""
        required_fields = ['auth_token', 'receiver_id']
        
        for field in required_fields:
            if not config.get('viber', field, fallback=''):
                self.errors.append(f"Viber field '{field}' is required when Viber notifications are enabled")
    
    def _validate_remote_section(self, config: configparser.ConfigParser):
        """Validate remote upload section."""
        if not config.has_section('remote'):
            return
            
        if config.getboolean('remote', 'upload_enabled', fallback=False):
            required_fields = ['protocol', 'host', 'username', 'remote_directory']
            
            for field in required_fields:
                if not config.get('remote', field, fallback=''):
                    self.errors.append(f"Remote field '{field}' is required when remote upload is enabled")
            
            # Validate upload schedule
            schedule = config.get('remote', 'upload_schedule', fallback='daily')
            valid_schedules = ['daily', 'first_day', 'last_day', 'monday', 'tuesday', 'wednesday', 
                             'thursday', 'friday', 'saturday', 'sunday']
            
            if schedule not in valid_schedules:
                try:
                    day = int(schedule)
                    if day < 1 or day > 31:
                        self.errors.append("upload_schedule day must be between 1 and 31")
                except ValueError:
                    self.errors.append(f"Invalid upload_schedule '{schedule}'. Must be 'daily', weekday, or day number (1-31)")
            
            # Validate SSH key file if specified
            key_file = config.get('remote', 'key_file', fallback='')
            if key_file and not os.path.isfile(key_file):
                self.errors.append(f"SSH key file not found: '{key_file}'")
    
    def _validate_export_section(self, config: configparser.ConfigParser):
        """Validate export section parameters."""
        if not config.has_section('export'):
            self.warnings.append("No [export] section found, using default export settings")
    
    def _validate_field_types(self, config: configparser.ConfigParser):
        """Validate field data types."""
        for section_name in config.sections():
            section = config[section_name]
            for option_name, option_value in section.items():
                if option_name in self.field_types:
                    expected_type = self.field_types[option_name]
                    try:
                        if expected_type == bool:
                            config.getboolean(section_name, option_name)
                        elif expected_type == int:
                            config.getint(section_name, option_name)
                        elif expected_type == float:
                            config.getfloat(section_name, option_name)
                    except ValueError:
                        self.errors.append(f"Field '{option_name}' in section [{section_name}] must be of type {expected_type.__name__}")
    
    def _validate_field_values(self, config: configparser.ConfigParser):
        """Validate field values against allowed values."""
        for section_name in config.sections():
            section = config[section_name]
            for option_name, option_value in section.items():
                if option_name in self.valid_values:
                    valid_options = self.valid_values[option_name]
                    if option_value.lower() not in [v.lower() for v in valid_options]:
                        self.errors.append(f"Invalid value '{option_value}' for '{option_name}'. Valid options: {', '.join(valid_options)}")
    
    def _validate_paths(self, config: configparser.ConfigParser):
        """Validate file and directory paths."""
        for section_name in config.sections():
            section = config[section_name]
            for option_name, option_value in section.items():
                if option_name in self.path_fields and option_value:
                    path_type = self.path_fields[option_name]
                    
                    if path_type == 'file':
                        if not os.path.isfile(option_value):
                            self.errors.append(f"File not found: '{option_value}' (configured in [{section_name}].{option_name})")
                    elif path_type == 'directory':
                        if option_name == 'backup_dir' or option_name == 'log_directory':
                            # These directories can be created automatically
                            continue
                        if not os.path.isdir(option_value):
                            self.errors.append(f"Directory not found: '{option_value}' (configured in [{section_name}].{option_name})")
    
    def _validate_cross_section_dependencies(self, config: configparser.ConfigParser):
        """Validate dependencies between different sections."""
        # If remote upload is enabled and uses SFTP, check for paramiko
        if (config.has_section('remote') and 
            config.getboolean('remote', 'upload_enabled', fallback=False) and
            config.get('remote', 'protocol', fallback='').lower() == 'sftp'):
            try:
                import paramiko
            except ImportError:
                self.warnings.append("SFTP protocol selected but paramiko library not available. Install with: pip install paramiko")
        
        # If SMS notifications are enabled, check for twilio
        if (config.has_section('sms') and 
            config.getboolean('sms', 'enabled', fallback=False)):
            try:
                import twilio
            except ImportError:
                self.warnings.append("SMS notifications enabled but twilio library not available. Install with: pip install twilio")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format (basic check for international format)."""
        # Remove spaces and dashes for validation
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Should start with + and contain only digits after that
        pattern = r'^\+[1-9]\d{7,14}$'
        return re.match(pattern, clean_phone) is not None


def validate_configuration(config: configparser.ConfigParser) -> None:
    """
    Validate configuration and raise ConfigurationError if validation fails.
    
    Args:
        config: ConfigParser instance to validate
        
    Raises:
        ConfigurationError: If validation fails
    """
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_config(config)
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    # Raise exception for errors
    if not is_valid:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(error_message)
        raise ConfigurationError(error_message)
    
    logger.info("Configuration validation completed successfully")


def get_validation_report(config: configparser.ConfigParser) -> Dict[str, Any]:
    """
    Get a detailed validation report without raising exceptions.
    
    Args:
        config: ConfigParser instance to validate
        
    Returns:
        Dictionary containing validation results
    """
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_config(config)
    
    return {
        'is_valid': is_valid,
        'errors': errors,
        'warnings': warnings,
        'error_count': len(errors),
        'warning_count': len(warnings)
    }

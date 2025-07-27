"""
sql_backup - A modern Python-based backup tool for MySQL databases.

This package provides comprehensive backup functionality with support for:
- MySQL database backups
- Multi-channel notifications (Email, Telegram, Slack, SMS)
- Remote upload capabilities (SFTP, FTP)
- Configurable scheduling and retention policies
- Comprehensive logging and error handling
"""

__version__ = "1.0.0"
__author__ = "Gregor"
__email__ = ""
__description__ = "A modern Python-based backup tool for MySQL databases"

# Import main functionality
from .main import main, cli_main

# Package metadata
__all__ = ['main', 'cli_main', '__version__', '__author__', '__description__']

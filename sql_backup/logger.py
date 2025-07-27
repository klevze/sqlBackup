"""
Logging configuration for sqlBackup.
Provides centralized logging setup with color support and multiple output formats.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color coding to console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[0;36m',     # Cyan
        'INFO': '\033[0;32m',      # Green
        'WARNING': '\033[0;33m',   # Yellow
        'ERROR': '\033[0;31m',     # Red
        'CRITICAL': '\033[0;35m',  # Magenta
        'RESET': '\033[0m'         # Reset
    }
    
    def format(self, record):
        """Format the log record with color coding."""
        # Add color to the level name
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


class SqlBackupLogger:
    """Central logging manager for sqlBackup application."""
    
    def __init__(self, name: str = 'sqlbackup', log_level: str = 'INFO', 
                 log_file: Optional[str] = None, enable_console: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            enable_console: Whether to enable console output
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Setup console handler
        if enable_console:
            self._setup_console_handler()
        
        # Setup file handler if specified
        if log_file:
            self._setup_file_handler(log_file)
    
    def _setup_console_handler(self):
        """Setup colored console output handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self, log_file: str):
        """Setup file output handler with rotation."""
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB max, 5 backups
        )
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger


def setup_logging(config=None, module_name: str = 'sqlbackup') -> logging.Logger:
    """
    Setup logging for the application.
    
    Args:
        config: Configuration object (ConfigParser instance)
        module_name: Name for the logger
    
    Returns:
        Configured logger instance
    """
    # Default values
    log_level = 'INFO'
    log_file = None
    enable_console = True
    
    # Read configuration if provided
    if config and config.has_section('logging'):
        log_level = config.get('logging', 'level', fallback='INFO')
        
        # Setup log file path
        if config.getboolean('logging', 'enable_file_logging', fallback=False):
            log_dir = config.get('logging', 'log_directory', fallback='logs')
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = os.path.join(log_dir, f'sqlbackup_{timestamp}.log')
        
        enable_console = config.getboolean('logging', 'enable_console', fallback=True)
    
    # Create and configure logger
    logger_manager = SqlBackupLogger(
        name=module_name,
        log_level=log_level,
        log_file=log_file,
        enable_console=enable_console
    )
    
    return logger_manager.get_logger()


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (uses caller's module if not provided)
    
    Returns:
        Logger instance
    """
    if name is None:
        # Get the caller's module name
        frame = sys._getframe(1)
        module = frame.f_globals.get('__name__', 'sqlbackup')
        name = module
    
    return logging.getLogger(name)


# Convenience functions for common log levels
def log_info(message: str, logger_name: str = None):
    """Log an info message."""
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: str = None):
    """Log a warning message."""
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: str = None):
    """Log an error message."""
    get_logger(logger_name).error(message)


def log_debug(message: str, logger_name: str = None):
    """Log a debug message."""
    get_logger(logger_name).debug(message)


def log_critical(message: str, logger_name: str = None):
    """Log a critical message."""
    get_logger(logger_name).critical(message)

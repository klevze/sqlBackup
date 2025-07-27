import configparser
import os
import sys
from .logger import setup_logging, get_logger
from .config_validator import validate_configuration, ConfigurationError

RED = "\033[0;31m"
YELLOW = "\033[0;33m"
RESET = "\033[0m"

def load_config():
    """Load and return the configuration from config.ini located at the project root."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config.ini")
    
    if not os.path.exists(config_path):
        print(f"{RED}Error: Configuration file '{config_path}' not found. Please create a config.ini file in the project root.{RESET}")
        print(f"{YELLOW}Hint: Copy config.ini.default to config.ini and modify as needed.{RESET}")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    try:
        config.read(config_path)
    except configparser.Error as e:
        print(f"{RED}Error parsing configuration file: {e}{RESET}")
        sys.exit(1)
    
    # Initialize logging first (before validation)
    setup_logging(config)
    
    # Get logger after logging is set up
    logger = get_logger(__name__)
    logger.info(f"Loading configuration from: {config_path}")
    
    # Validate configuration
    try:
        validate_configuration(config)
        logger.info("Configuration loaded and validated successfully")
    except ConfigurationError as e:
        logger.critical(f"Configuration validation failed: {e}")
        print(f"{RED}Configuration validation failed:{RESET}")
        for line in str(e).split('\n')[1:]:  # Skip the first line "Configuration validation failed:"
            if line.strip():
                print(f"{RED}{line}{RESET}")
        print(f"{YELLOW}Please fix the configuration errors and try again.{RESET}")
        sys.exit(1)
    
    return config

# Global configuration instance - lazy loaded
CONFIG = None

def get_config():
    """Get the global configuration instance, loading it if necessary."""
    global CONFIG
    if CONFIG is None:
        CONFIG = load_config()
    return CONFIG

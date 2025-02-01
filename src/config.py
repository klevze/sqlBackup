import configparser
import os
import sys

RED = "\033[0;31m"
RESET = "\033[0m"

def load_config():
    """Load and return the configuration from config.ini located at the project root."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config.ini")
    
    if not os.path.exists(config_path):
        print(f"{RED}Error: Configuration file '{config_path}' not found. Please create a config.ini file in the project root.{RESET}")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

# Global configuration instance
CONFIG = load_config()

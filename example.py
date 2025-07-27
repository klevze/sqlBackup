#!/usr/bin/env python3
"""
Example script showing how to use sqlBackup programmatically.
This demonstrates importing and using the sqlBackup modules directly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sql_backup.config import load_config
from sql_backup.backup import run_backups, should_upload
from sql_backup.notifications import notify_all
from sql_backup.remote_upload import upload_backups
from sql_backup.logger import get_logger

# Get logger for this example
logger = get_logger('example')

def example_backup():
    """Example function demonstrating programmatic backup usage."""
    logger.info("Starting example backup demonstration")
    print("Loading configuration...")
    config = load_config()
    
    print("Starting backup process...")
    # Run backups and get summary
    errors, summary = run_backups(config)
    
    # Prepare notification message
    if errors:
        message = "Databases with backup errors: " + ", ".join(errors)
        logger.warning(f"Example backup completed with errors: {', '.join(errors)}")
        print(f"❌ {message}")
    else:
        message = "All backups completed successfully."
        logger.info("Example backup completed successfully")
        print(f"✅ {message}")
    
    print("\nBackup Summary:")
    print(summary)
    
    # Send notifications
    print("\nSending notifications...")
    notify_all(config, message)
    
    # Handle remote upload if configured
    if config.has_section("remote") and config.getboolean("remote", "upload_enabled", fallback=False):
        upload_schedule = config.get("remote", "upload_schedule", fallback="daily")
        if should_upload(upload_schedule):
            remote_config = dict(config.items("remote"))
            logger.info("Starting remote upload in example")
            print("Uploading backups to remote server...")
            upload_backups(remote_config)
        else:
            logger.info("Remote upload schedule condition not met in example")
            print("Remote upload schedule condition not met. Skipping remote upload.")
    
    logger.info("Example backup demonstration completed")
    return len(errors) == 0  # Return True if successful

if __name__ == "__main__":
    try:
        success = example_backup()
        if success:
            logger.info("Example backup process completed successfully")
            print("\n🎉 Backup process completed successfully!")
            sys.exit(0)
        else:
            logger.warning("Example backup process completed with errors")
            print("\n⚠️  Backup process completed with errors!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Example backup interrupted by user. Exiting gracefully...")
        print("\n🛑 Backup interrupted by user. Exiting gracefully...")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error in example: {e}", exc_info=True)
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

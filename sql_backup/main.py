#!/usr/bin/env python3
"""
Main entry point for the backup project.
Loads configuration, runs backups, sends multi-channel notifications,
and optionally uploads backups remotely.
"""

import sys
from .config import load_config
from .backup import run_backups, should_upload
from .notifications import notify_all
from .remote_upload import upload_backups
from .logger import get_logger

# Get logger for main module
logger = get_logger('main')

def main():
    """Main entry point for the sqlBackup application."""
    logger.info("Starting sqlBackup application")
    config = load_config()
        
    # Run backups and get summary.
    logger.info("Initiating backup process")
    errors, summary = run_backups(config)
    if errors:
        message = "Databases with backup errors: " + ", ".join(errors)
        logger.warning(f"Backup completed with errors: {', '.join(errors)}")
    else:
        message = "All backups completed successfully."
        logger.info("All backups completed successfully")
    
    print(summary)
    print(message)
    
    # Send notifications through enabled channels.
    logger.info("Sending notifications")
    notify_all(config, message)
    
    # Remote upload if enabled and schedule condition is met.
    if config.has_section("remote") and config.getboolean("remote", "upload_enabled", fallback=False):
        upload_schedule = config.get("remote", "upload_schedule", fallback="daily")
        logger.debug(f"Checking upload schedule: {upload_schedule}")
        if should_upload(upload_schedule):
            remote_config = dict(config.items("remote"))
            logger.info("Starting remote upload")
            print("Uploading backups to remote server...")
            upload_backups(remote_config)
        else:
            logger.info("Remote upload schedule condition not met. Skipping remote upload")
            print("Remote upload schedule condition not met. Skipping remote upload.")
    else:
        logger.debug("Remote upload not enabled or configured")
    
    logger.info("sqlBackup application completed")

def cli_main():
    """Command-line interface entry point with error handling."""
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Backup interrupted by user. Exiting gracefully...")
        print("\nBackup interrupted by user. Exiting gracefully...")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()

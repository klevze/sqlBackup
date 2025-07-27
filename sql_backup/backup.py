import os
import sys
import subprocess
import datetime
import tarfile
import tempfile
import time
import threading
from itertools import cycle
from fnmatch import fnmatch

from .config import get_config
from .logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# --- Global Color Codes ---
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
RESET = "\033[0m"
TIMESTAMP = datetime.datetime.now().strftime("%F")

# --- Configuration Variables (lazy-loaded) ---
_config = None
def _get_config():
    global _config
    if _config is None:
        _config = get_config()
    return _config

def get_backup_dir():
    return _get_config().get("backup", "backup_dir")

def get_archive_format():
    return _get_config().get("backup", "archive_format").lower()

def get_ignored_db_patterns():
    return [p.strip() for p in _get_config().get("mysql", "ignored_databases").split(",")]

def get_mysql_path():
    return _get_config().get("mysql", "mysql_path")

def get_mysqldump_path():
    return _get_config().get("mysql", "mysqldump_path")

def run_backups(config):
    """Main function to run database backups with the provided configuration."""
    # Ensure backup directory exists
    backup_dir = config.get("backup", "backup_dir")
    try:
        os.makedirs(backup_dir, exist_ok=True)
        logger.info(f"Backup directory ready: {backup_dir}")
    except PermissionError as e:
        logger.critical(f"Permission error creating backup directory '{backup_dir}': {e}")
        sys.exit(1)

# --- Spinner Class ---
class Spinner:
    def __init__(self, message="Working..."):
        self.spinner = cycle(["-", "\\", "|", "/"])
        self.message = message
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._spin, daemon=True).start()

    def _spin(self):
        while self.running:
            print(f"\r{self.message} {next(self.spinner)}", end="", flush=True)
            time.sleep(0.1)

    def stop(self):
        self.running = False
        print("\r", end="")

def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"

def create_temp_mysql_config() -> str:
    """Create a temporary MySQL configuration file with credentials."""
    config = get_config()
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
    tmp.write("[client]\n")
    tmp.write(f"user = {config.get('mysql', 'user')}\n")
    tmp.write(f"password = {config.get('mysql', 'password')}\n")
    tmp.write(f"host = {config.get('mysql', 'host')}\n")
    tmp.close()
    return tmp.name

def get_client_config_path():
    """Get or create the MySQL client configuration file path."""
    global _client_config_path
    if _client_config_path is None:
        _client_config_path = create_temp_mysql_config()
    return _client_config_path

# Global variable for client config path (lazy-loaded)
_client_config_path = None

def check_mysql_connection() -> None:
    logger.debug("Testing MySQL connection...")
    config = get_config()
    mysql_path = config.get("mysql", "mysql_path")
    client_config_path = get_client_config_path()
    try:
        subprocess.run(
            [mysql_path, f"--defaults-extra-file={client_config_path}", "-e", "SELECT 1;"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("MySQL connection successful")
        print(f"{GREEN}MySQL connection successful.{RESET}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Unable to connect to MySQL: {e.stderr}")
        print(f"{RED}Error: Unable to connect to MySQL. Check credentials and permissions.{RESET}")
        print(f"{RED}Details: {e.stderr}{RESET}")
        sys.exit(1)

def get_all_databases() -> list:
    logger.debug("Retrieving list of all databases")
    config = get_config()
    mysql_path = config.get("mysql", "mysql_path")
    client_config_path = get_client_config_path()
    try:
        result = subprocess.run(
            [mysql_path, f"--defaults-extra-file={client_config_path}", "-e", "SHOW DATABASES;"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        lines = result.stdout.splitlines()
        databases = [line.strip() for line in lines[1:]]
        logger.info(f"Found {len(databases)} databases")
        return databases
    except subprocess.CalledProcessError as e:
        logger.error(f"Error retrieving databases: {e.stderr}")
        print(f"{RED}Error retrieving databases: {e.stderr}{RESET}")
        sys.exit(1)

def is_ignored(db_name: str) -> bool:
    """
    Return True if db_name matches any of the patterns in ignored_databases config.
    We use fnmatch to support wildcards (like projekti_*).
    """
    ignored_patterns = get_ignored_db_patterns()
    for pattern in ignored_patterns:
        if fnmatch(db_name, pattern):
            logger.debug(f"Database '{db_name}' ignored (matches pattern '{pattern}')")
            return True
    return False

def backup_database(db: str) -> tuple:
    """
    Dump the given database, archive it, and return a tuple:
      (status, dump_size, archive_size)
    """
    logger.info(f"Starting backup for database: {db}")
    config = get_config()
    backup_dir = config.get("backup", "backup_dir")
    mysqldump_path = config.get("mysql", "mysqldump_path")
    client_config_path = get_client_config_path()
    archive_format = config.get("backup", "archive_format").lower()
    
    status = "Success"
    temp_sql_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.sql")
    dump_cmd = [
        mysqldump_path,
        f"--defaults-extra-file={client_config_path}",
        "--default-character-set=utf8mb4",
        "--single-transaction",
        "--force",
        "--opt"
    ]
    if config.has_section("export") and config.getboolean("export", "include_routines", fallback=False):
        dump_cmd.append("--routines")
    if config.has_section("export") and config.getboolean("export", "include_events", fallback=False):
        dump_cmd.append("--events")
    if config.has_section("export") and not config.getboolean("export", "column_statistics", fallback=True):
        dump_cmd.append("--column-statistics=0")
    dump_cmd.extend(["--databases", db])
    
    logger.debug(f"Dump command: {' '.join(dump_cmd)}")
    
    spinner = Spinner(f"Dumping {db}")
    spinner.start()
    try:
        with open(temp_sql_file, "w") as f:
            subprocess.run(dump_cmd, check=True, stdout=f)
        spinner.stop()
        dump_size = os.path.getsize(temp_sql_file) if os.path.exists(temp_sql_file) else 0
        logger.debug(f"Database {db} dumped successfully, size: {format_size(dump_size)}")

        if archive_format == "none":
            archive_file = temp_sql_file
            archive_size = dump_size
            logger.debug(f"No compression applied for {db}")
        elif archive_format == "gz":
            archive_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.sql.gz")
            import gzip
            with open(temp_sql_file, "rb") as f_in, open(archive_file, "wb") as f_out:
                with gzip.GzipFile(fileobj=f_out, mode="wb") as gz_out:
                    gz_out.writelines(f_in)
            archive_size = os.path.getsize(archive_file)
            logger.debug(f"Database {db} compressed with gzip, size: {format_size(archive_size)}")
        elif archive_format == "xz":
            archive_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.sql.xz")
            import lzma
            with open(temp_sql_file, "rb") as f_in, lzma.open(archive_file, "wb") as f_out:
                f_out.write(f_in.read())
            archive_size = os.path.getsize(archive_file)
            logger.debug(f"Database {db} compressed with xz, size: {format_size(archive_size)}")
        elif archive_format == "tar.xz":
            archive_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.tar.xz")
            with tarfile.open(archive_file, "w:xz") as tar:
                tar.add(temp_sql_file, arcname=os.path.basename(temp_sql_file))
            archive_size = os.path.getsize(archive_file)
            logger.debug(f"Database {db} compressed with tar.xz, size: {format_size(archive_size)}")
        elif archive_format == "zip":
            archive_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.zip")
            import zipfile
            with zipfile.ZipFile(archive_file, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_sql_file, arcname=os.path.basename(temp_sql_file))
            archive_size = os.path.getsize(archive_file)
            logger.debug(f"Database {db} compressed with zip, size: {format_size(archive_size)}")
        elif archive_format == "rar":
            archive_file = os.path.join(backup_dir, f"{db}-{TIMESTAMP}.rar")
            try:
                subprocess.run(["rar", "a", archive_file, temp_sql_file], check=True)
                archive_size = os.path.getsize(archive_file)
                logger.debug(f"Database {db} compressed with rar, size: {format_size(archive_size)}")
            except Exception as e:
                spinner.stop()
                logger.error(f"Error archiving {db} with rar: {e}")
                print(f"\n{RED}Error archiving {db} with rar: {e}{RESET}")
                status = "Error"
                archive_size = 0
        else:
            logger.warning(f"Unknown archive format: {archive_format}. Using plain backup (none).")
            print(f"{RED}Unknown archive format: {archive_format}. Using plain backup (none).{RESET}")
            archive_file = temp_sql_file
            archive_size = dump_size
    except subprocess.CalledProcessError as e:
        spinner.stop()
        logger.error(f"Error dumping {db}: {e}")
        print(f"\n{RED}Error dumping {db}: {e}{RESET}")
        status = "Error"
        dump_size = 0
        archive_size = 0
    except Exception as e:
        spinner.stop()
        logger.error(f"Error archiving {db}: {e}")
        print(f"\n{RED}Error archiving {db}: {e}{RESET}")
        status = "Error"
        dump_size = 0
        archive_size = 0
    finally:
        if archive_format != "none" and os.path.exists(temp_sql_file):
            os.remove(temp_sql_file)
            logger.debug(f"Temporary SQL file removed for {db}")
    
    logger.info(f"Backup completed for {db}: {status}")
    return status, dump_size, archive_size

def should_upload(schedule: str) -> bool:
    """
    Determine if the current day meets the upload schedule criteria.
    Supported values: "daily", "first_day", "last_day", weekday names, or a numeric day.
    """
    from datetime import datetime
    import calendar
    now = datetime.now()
    schedule = schedule.lower().strip()
    if schedule == "daily":
        return True
    elif schedule == "first_day":
        return now.day == 1
    elif schedule == "last_day":
        last_day = calendar.monthrange(now.year, now.month)[1]
        return now.day == last_day
    elif schedule in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        return now.strftime("%A").lower() == schedule
    else:
        try:
            day = int(schedule)
            return now.day == day
        except ValueError:
            return False

def print_table_header() -> None:
    header = f"| {'Database':25} | {'Status':15} | {'Time (s)':10} | {'Dump Size':12} | {'Archive Size':12} |"
    separator = f"|{'-'*27}|{'-'*17}|{'-'*12}|{'-'*14}|{'-'*16}|"
    print(header)
    print(separator)

def print_table_row(db: str, status: str, elapsed: str, dump_size: int, archive_size: int) -> None:
    if status == "Success":
        color = GREEN
        dump_str = format_size(dump_size)
        archive_str = format_size(archive_size)
    elif status == "Error":
        color = RED
        dump_str = "N/A"
        archive_str = "N/A"
    else:
        color = YELLOW
        dump_str = "-"
        archive_str = "-"
    print(f"| {db:25} | {color}{status:15}{RESET} | {elapsed:10} | {dump_str:12} | {archive_str:12} |")

def run_backups(config) -> tuple:
    """
    Run backups for all databases and return a tuple:
      (list_of_errors, summary_message)
    """
    logger.info("Starting backup process")
    check_mysql_connection()
    databases = get_all_databases()
    errors = []
    summary_lines = []
    
    logger.info(f"Processing {len(databases)} databases")
    print_table_header()
    for db in databases:
        if is_ignored(db):
            logger.debug(f"Skipping database: {db} (ignored)")
            print_table_row(db, "Skipped", "-", "-", "-")
            continue

        start = time.time()
        status, dump_size, archive_size = backup_database(db)
        elapsed = f"{time.time() - start:.1f}"
        if status == "Error":
            errors.append(db)
        
        print_table_row(db, status, elapsed, dump_size, archive_size)
        summary_lines.append(f"{db}: {status} in {elapsed}s")
    
    separator = f"|{'-'*27}|{'-'*17}|{'-'*12}|{'-'*14}|{'-'*16}|"
    print(separator)
    summary = "\n".join(summary_lines)
    
    if errors:
        logger.warning(f"Backup completed with errors for: {', '.join(errors)}")
    else:
        logger.info("All backups completed successfully")
    
    return errors, summary

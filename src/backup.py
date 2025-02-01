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

from .config import CONFIG

# --- Global Color Codes ---
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
RESET = "\033[0m"

# --- Configuration Variables ---
BACKUP_DIR = CONFIG.get("backup", "backup_dir")
ARCHIVE_FORMAT = CONFIG.get("backup", "archive_format").lower()
# Split, then strip whitespace from each pattern
IGNORED_DB_PATTERNS = [p.strip() for p in CONFIG.get("mysql", "ignored_databases").split(",")]
MYSQL = CONFIG.get("mysql", "mysql_path")
MYSQLDUMP = CONFIG.get("mysql", "mysqldump_path")
TIMESTAMP = datetime.datetime.now().strftime("%F")

# Ensure backup directory exists
try:
    os.makedirs(BACKUP_DIR, exist_ok=True)
except PermissionError as e:
    print(f"{RED}Permission error creating backup directory '{BACKUP_DIR}': {e}{RESET}")
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
    from .config import CONFIG
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
    tmp.write("[client]\n")
    tmp.write(f"user = {CONFIG.get('mysql', 'user')}\n")
    tmp.write(f"password = {CONFIG.get('mysql', 'password')}\n")
    tmp.write(f"host = {CONFIG.get('mysql', 'host')}\n")
    tmp.close()
    return tmp.name

CLIENT_CONFIG_PATH = create_temp_mysql_config()

def check_mysql_connection() -> None:
    try:
        subprocess.run(
            [MYSQL, f"--defaults-extra-file={CLIENT_CONFIG_PATH}", "-e", "SELECT 1;"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"{GREEN}MySQL connection successful.{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error: Unable to connect to MySQL. Check credentials and permissions.{RESET}")
        print(f"{RED}Details: {e.stderr}{RESET}")
        sys.exit(1)

def get_all_databases() -> list:
    try:
        result = subprocess.run(
            [MYSQL, f"--defaults-extra-file={CLIENT_CONFIG_PATH}", "-e", "SHOW DATABASES;"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        lines = result.stdout.splitlines()
        return [line.strip() for line in lines[1:]]
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error retrieving databases: {e.stderr}{RESET}")
        sys.exit(1)

def is_ignored(db_name: str) -> bool:
    """
    Return True if db_name matches any of the patterns in IGNORED_DB_PATTERNS.
    We use fnmatch to support wildcards (like projekti_*).
    """
    for pattern in IGNORED_DB_PATTERNS:
        if fnmatch(db_name, pattern):
            return True
    return False

def backup_database(db: str) -> tuple:
    """
    Dump the given database, archive it, and return a tuple:
      (status, dump_size, archive_size)
    """
    status = "Success"
    temp_sql_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.sql")
    dump_cmd = [
        MYSQLDUMP,
        f"--defaults-extra-file={CLIENT_CONFIG_PATH}",
        "--default-character-set=utf8mb4",
        "--single-transaction",
        "--force",
        "--opt"
    ]
    if CONFIG.getboolean("export", "include_routines"):
        dump_cmd.append("--routines")
    if CONFIG.getboolean("export", "include_events"):
        dump_cmd.append("--events")
    if not CONFIG.getboolean("export", "column_statistics"):
        dump_cmd.append("--column-statistics=0")
    dump_cmd.extend(["--databases", db])
    
    spinner = Spinner(f"Dumping {db}")
    spinner.start()
    try:
        with open(temp_sql_file, "w") as f:
            subprocess.run(dump_cmd, check=True, stdout=f)
        spinner.stop()
        dump_size = os.path.getsize(temp_sql_file) if os.path.exists(temp_sql_file) else 0

        if ARCHIVE_FORMAT == "none":
            archive_file = temp_sql_file
            archive_size = dump_size
        elif ARCHIVE_FORMAT == "gz":
            archive_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.sql.gz")
            import gzip
            with open(temp_sql_file, "rb") as f_in, open(archive_file, "wb") as f_out:
                with gzip.GzipFile(fileobj=f_out, mode="wb") as gz_out:
                    gz_out.writelines(f_in)
            archive_size = os.path.getsize(archive_file)
        elif ARCHIVE_FORMAT == "xz":
            archive_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.sql.xz")
            import lzma
            with open(temp_sql_file, "rb") as f_in, lzma.open(archive_file, "wb") as f_out:
                f_out.write(f_in.read())
            archive_size = os.path.getsize(archive_file)
        elif ARCHIVE_FORMAT == "tar.xz":
            archive_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.tar.xz")
            with tarfile.open(archive_file, "w:xz") as tar:
                tar.add(temp_sql_file, arcname=os.path.basename(temp_sql_file))
            archive_size = os.path.getsize(archive_file)
        elif ARCHIVE_FORMAT == "zip":
            archive_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.zip")
            import zipfile
            with zipfile.ZipFile(archive_file, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_sql_file, arcname=os.path.basename(temp_sql_file))
            archive_size = os.path.getsize(archive_file)
        elif ARCHIVE_FORMAT == "rar":
            archive_file = os.path.join(BACKUP_DIR, f"{db}-{TIMESTAMP}.rar")
            try:
                subprocess.run(["rar", "a", archive_file, temp_sql_file], check=True)
                archive_size = os.path.getsize(archive_file)
            except Exception as e:
                spinner.stop()
                print(f"\n{RED}Error archiving {db} with rar: {e}{RESET}")
                status = "Error"
                archive_size = 0
        else:
            print(f"{RED}Unknown archive format: {ARCHIVE_FORMAT}. Using plain backup (none).{RESET}")
            archive_file = temp_sql_file
            archive_size = dump_size
    except subprocess.CalledProcessError as e:
        spinner.stop()
        print(f"\n{RED}Error dumping {db}: {e}{RESET}")
        status = "Error"
        dump_size = 0
        archive_size = 0
    except Exception as e:
        spinner.stop()
        print(f"\n{RED}Error archiving {db}: {e}{RESET}")
        status = "Error"
        dump_size = 0
        archive_size = 0
    finally:
        if ARCHIVE_FORMAT != "none" and os.path.exists(temp_sql_file):
            os.remove(temp_sql_file)
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
    check_mysql_connection()
    databases = get_all_databases()
    errors = []
    summary_lines = []
    
    print_table_header()
    for db in databases:
        if is_ignored(db):
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
    return errors, summary

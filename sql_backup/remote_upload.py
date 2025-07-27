import os
import subprocess
import datetime
from .logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Color codes
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
RESET = "\033[0m"
TIMESTAMP = datetime.datetime.now().strftime("%F")

def upload_backups(remote_config: dict) -> None:
    """
    Upload backup files (those containing the current TIMESTAMP) to a remote server.
    Supports protocols: sftp, ftp, scp.
    """
    from .config import get_config
    
    config = get_config()
    backup_dir = config.get("backup", "backup_dir")
    
    logger.info("Starting remote backup upload")
    pattern = f"-{TIMESTAMP}."
    files_to_upload = [f for f in os.listdir(backup_dir) if pattern in f]
    if not files_to_upload:
        logger.warning("No backup files found for upload")
        print(f"{YELLOW}No backup files found for upload.{RESET}")
        return
    
    logger.info(f"Found {len(files_to_upload)} files to upload: {files_to_upload}")
    protocol = remote_config.get("protocol", "sftp").lower()
    host = remote_config.get("host")
    port = int(remote_config.get("port", 22))
    username = remote_config.get("username")
    password = remote_config.get("password", "")
    remote_directory = remote_config.get("remote_directory", "/")
    
    logger.debug(f"Upload config - Protocol: {protocol}, Host: {host}:{port}, User: {username}, Remote dir: {remote_directory}")
    
    if protocol == "sftp":
        try:
            import paramiko
        except ImportError:
            logger.error("Paramiko not installed. SFTP upload not available")
            print(f"{RED}Paramiko not installed. SFTP upload not available.{RESET}")
            return
        try:
            transport = paramiko.Transport((host, port))
            key_file = remote_config.get("key_file", "").strip()
            if key_file and os.path.exists(key_file):
                key_passphrase = remote_config.get("key_passphrase", None)
                private_key = paramiko.RSAKey.from_private_key_file(key_file, password=key_passphrase)
                transport.connect(username=username, pkey=private_key)
                logger.debug("Connected to SFTP using key authentication")
            else:
                transport.connect(username=username, password=password)
                logger.debug("Connected to SFTP using password authentication")
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                sftp.chdir(remote_directory)
            except IOError:
                logger.info(f"Creating remote directory: {remote_directory}")
                sftp.mkdir(remote_directory)
                sftp.chdir(remote_directory)
            for file in files_to_upload:
                local_path = os.path.join(backup_dir, file)
                remote_path = os.path.join(remote_directory, file)
                logger.info(f"Uploading {file} to {host}:{remote_path}")
                print(f"{BLUE}Uploading {file} to {host}:{remote_path}{RESET}")
                sftp.put(local_path, remote_path)
            sftp.close()
            transport.close()
            logger.info("SFTP upload completed successfully")
        except Exception as e:
            logger.error(f"SFTP upload failed: {e}")
            print(f"{RED}SFTP upload failed: {e}{RESET}")
    elif protocol == "ftp":
        from ftplib import FTP
        try:
            ftp = FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            logger.info("Connected to FTP server")
            try:
                ftp.cwd(remote_directory)
            except:
                logger.info(f"Creating FTP directory: {remote_directory}")
                ftp.mkd(remote_directory)
                ftp.cwd(remote_directory)
            for file in files_to_upload:
                local_path = os.path.join(backup_dir, file)
                logger.info(f"Uploading {file} to FTP server")
                print(f"{BLUE}Uploading {file} to {host}:{remote_directory}{RESET}")
                with open(local_path, "rb") as f:
                    ftp.storbinary(f"STOR {file}", f)
            ftp.quit()
            logger.info("FTP upload completed successfully")
        except Exception as e:
            logger.error(f"FTP upload failed: {e}")
            print(f"{RED}FTP upload failed: {e}{RESET}")
    elif protocol == "scp":
        for file in files_to_upload:
            local_path = os.path.join(backup_dir, file)
            remote_path = f"{username}@{host}:{remote_directory}"
            logger.info(f"Uploading {file} via SCP")
            print(f"{BLUE}Uploading {file} via SCP to {remote_path}{RESET}")
            try:
                subprocess.run(["scp", local_path, remote_path], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"SCP upload failed for {file}: {e}")
                print(f"{RED}SCP upload failed for {file}: {e}{RESET}")
        logger.info("SCP upload completed")
    else:
        logger.error(f"Unsupported protocol: {protocol}")
        print(f"{RED}Unsupported protocol: {protocol}. No upload performed.{RESET}")

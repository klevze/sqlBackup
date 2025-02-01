import os
import subprocess
from .backup import TIMESTAMP, BACKUP_DIR, BLUE, YELLOW, RED, RESET

def upload_backups(remote_config: dict) -> None:
    """
    Upload backup files (those containing the current TIMESTAMP) to a remote server.
    Supports protocols: sftp, ftp, scp.
    """
    pattern = f"-{TIMESTAMP}."
    files_to_upload = [f for f in os.listdir(BACKUP_DIR) if pattern in f]
    if not files_to_upload:
        print(f"{YELLOW}No backup files found for upload.{RESET}")
        return
    protocol = remote_config.get("protocol", "sftp").lower()
    host = remote_config.get("host")
    port = int(remote_config.get("port", 22))
    username = remote_config.get("username")
    password = remote_config.get("password", "")
    remote_directory = remote_config.get("remote_directory", "/")
    if protocol == "sftp":
        try:
            import paramiko
        except ImportError:
            print(f"{RED}Paramiko not installed. SFTP upload not available.{RESET}")
            return
        try:
            transport = paramiko.Transport((host, port))
            key_file = remote_config.get("key_file", "").strip()
            if key_file and os.path.exists(key_file):
                key_passphrase = remote_config.get("key_passphrase", None)
                private_key = paramiko.RSAKey.from_private_key_file(key_file, password=key_passphrase)
                transport.connect(username=username, pkey=private_key)
            else:
                transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                sftp.chdir(remote_directory)
            except IOError:
                sftp.mkdir(remote_directory)
                sftp.chdir(remote_directory)
            for file in files_to_upload:
                local_path = os.path.join(BACKUP_DIR, file)
                remote_path = os.path.join(remote_directory, file)
                print(f"{BLUE}Uploading {file} to {host}:{remote_path}{RESET}")
                sftp.put(local_path, remote_path)
            sftp.close()
            transport.close()
        except Exception as e:
            print(f"{RED}SFTP upload failed: {e}{RESET}")
    elif protocol == "ftp":
        from ftplib import FTP
        try:
            ftp = FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            try:
                ftp.cwd(remote_directory)
            except:
                ftp.mkd(remote_directory)
                ftp.cwd(remote_directory)
            for file in files_to_upload:
                local_path = os.path.join(BACKUP_DIR, file)
                print(f"{BLUE}Uploading {file} to {host}:{remote_directory}{RESET}")
                with open(local_path, "rb") as f:
                    ftp.storbinary(f"STOR {file}", f)
            ftp.quit()
        except Exception as e:
            print(f"{RED}FTP upload failed: {e}{RESET}")
    elif protocol == "scp":
        for file in files_to_upload:
            local_path = os.path.join(BACKUP_DIR, file)
            remote_path = f"{username}@{host}:{remote_directory}"
            print(f"{BLUE}Uploading {file} via SCP to {remote_path}{RESET}")
            try:
                subprocess.run(["scp", local_path, remote_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"{RED}SCP upload failed for {file}: {e}{RESET}")
    else:
        print(f"{RED}Unsupported protocol: {protocol}. No upload performed.{RESET}")

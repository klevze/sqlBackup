import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import CONFIG

# --- Global Color Codes ---
RED = "\033[0;31m"
BLUE = "\033[0;34m"
YELLOW = "\033[0;33m"
GREEN = "\033[0;32m"
RESET = "\033[0m"

def send_telegram_notification(config, message: str) -> None:
    if config.has_section("telegram") and config.getboolean("telegram", "enabled", fallback=False):
        telegram_token = config.get("telegram", "telegram_token")
        telegram_chatid = config.get("telegram", "telegram_chatid")
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {"chat_id": telegram_chatid, "text": message}
        try:
            requests.post(url, data=data)
            print(f"{BLUE}Telegram notification sent.{RESET}")
        except Exception as e:
            print(f"{RED}Telegram notification failed: {e}{RESET}")

def send_email_notification(config, message: str) -> None:
    if config.has_section("email") and config.getboolean("email", "enabled", fallback=False):
        smtp_server = config.get("email", "smtp_server")
        smtp_port = config.getint("email", "smtp_port")
        username = config.get("email", "username")
        password = config.get("email", "password")
        from_address = config.get("email", "from_address")
        to_addresses = config.get("email", "to_addresses").split(',')
        to_addresses = [addr.strip() for addr in to_addresses if addr.strip()]
        subject = "Backup Notification"
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = ", ".join(to_addresses)
        msg.attach(MIMEText(message, "plain"))
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.sendmail(from_address, to_addresses, msg.as_string())
            server.quit()
            print(f"{BLUE}Email notification sent.{RESET}")
        except Exception as e:
            print(f"{RED}Email notification failed: {e}{RESET}")

def send_slack_notification(config, message: str) -> None:
    if config.has_section("slack") and config.getboolean("slack", "enabled", fallback=False):
        webhook_url = config.get("slack", "webhook_url")
        try:
            payload = {"text": message}
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                print(f"{RED}Slack notification failed: {response.text}{RESET}")
            else:
                print(f"{BLUE}Slack notification sent.{RESET}")
        except Exception as e:
            print(f"{RED}Slack notification error: {e}{RESET}")

def send_sms_notification(config, message: str) -> None:
    if config.has_section("sms") and config.getboolean("sms", "enabled", fallback=False):
        try:
            from twilio.rest import Client
            account_sid = config.get("sms", "account_sid")
            auth_token = config.get("sms", "auth_token")
            from_number = config.get("sms", "from_number")
            to_numbers = config.get("sms", "to_numbers").split(',')
            to_numbers = [num.strip() for num in to_numbers if num.strip()]
            client = Client(account_sid, auth_token)
            for number in to_numbers:
                client.messages.create(body=message, from_=from_number, to=number)
            print(f"{BLUE}SMS notification sent.{RESET}")
        except Exception as e:
            print(f"{RED}SMS notification failed: {e}{RESET}")

def send_viber_notification(config, message: str) -> None:
    if config.has_section("viber") and config.getboolean("viber", "enabled", fallback=False):
        auth_token = config.get("viber", "auth_token")
        receiver_id = config.get("viber", "receiver_id")
        sender_name = config.get("viber", "sender_name", fallback="BackupBot")
        url = "https://chatapi.viber.com/pa/send_message"
        headers = {
            "Content-Type": "application/json",
            "X-Viber-Auth-Token": auth_token
        }
        payload = {
            "receiver": receiver_id,
            "min_api_version": 2,
            "sender": {"name": sender_name},
            "type": "text",
            "text": message
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"{RED}Viber notification failed: {response.text}{RESET}")
            else:
                print(f"{BLUE}Viber notification sent.{RESET}")
        except Exception as e:
            print(f"{RED}Viber notification error: {e}{RESET}")

def send_messenger_notification(config, message: str) -> None:
    if config.has_section("messenger") and config.getboolean("messenger", "enabled", fallback=False):
        print(f"{YELLOW}Messenger notification not implemented yet.{RESET}")

def notify_all(config, message: str) -> None:
    if config.has_section("notification"):
        channels = config.get("notification", "channels").split(',')
        channels = [ch.strip().lower() for ch in channels if ch.strip()]
        for channel in channels:
            if channel == "telegram":
                send_telegram_notification(config, message)
            elif channel == "email":
                send_email_notification(config, message)
            elif channel == "slack":
                send_slack_notification(config, message)
            elif channel == "sms":
                send_sms_notification(config, message)
            elif channel == "viber":
                send_viber_notification(config, message)
            elif channel == "messenger":
                send_messenger_notification(config, message)
            else:
                print(f"{YELLOW}Unknown notification channel: {channel}{RESET}")

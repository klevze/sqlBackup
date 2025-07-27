import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

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
            response = requests.post(url, data=data)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully")
            print(f"{BLUE}Telegram notification sent.{RESET}")
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
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
            logger.info(f"Email notification sent to {len(to_addresses)} recipients")
            print(f"{BLUE}Email notification sent.{RESET}")
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            print(f"{RED}Email notification failed: {e}{RESET}")

def send_slack_notification(config, message):
    if config.has_section("slack") and config.getboolean("slack", "enabled", fallback=False):
        webhook_url = config.get("slack", "webhook_url")
        try:
            payload = {"text": message}
            # Note: use json=payload, not data=payload
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Slack notification failed: {response.text}")
                print(f"Slack notification failed: {response.text}")
            else:
                logger.info("Slack notification sent successfully")
                print("Slack notification sent.")
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            print(f"Slack notification error: {e}")
            
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
            logger.info(f"SMS notification sent to {len(to_numbers)} recipients")
            print(f"{BLUE}SMS notification sent.{RESET}")
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
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
                logger.error(f"Viber notification failed: {response.text}")
                print(f"{RED}Viber notification failed: {response.text}{RESET}")
            else:
                logger.info("Viber notification sent successfully")
                print(f"{BLUE}Viber notification sent.{RESET}")
        except Exception as e:
            logger.error(f"Viber notification error: {e}")
            print(f"{RED}Viber notification error: {e}{RESET}")

def send_messenger_notification(config, message: str) -> None:
    if config.has_section("messenger") and config.getboolean("messenger", "enabled", fallback=False):
        logger.warning("Messenger notification not implemented yet")
        print(f"{YELLOW}Messenger notification not implemented yet.{RESET}")

def notify_all(config, message: str) -> None:
    logger.info("Sending notifications to all enabled channels")
    if config.has_section("notification"):
        channels = config.get("notification", "channels").split(',')
        channels = [ch.strip().lower() for ch in channels if ch.strip()]
        logger.debug(f"Configured notification channels: {channels}")
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
                logger.warning(f"Unknown notification channel: {channel}")
                print(f"{YELLOW}Unknown notification channel: {channel}{RESET}")
    else:
        logger.info("No notification section found in config, trying individual channel sections")
        # Fallback: check individual sections
        if config.has_section("telegram") and config.getboolean("telegram", "enabled", fallback=False):
            send_telegram_notification(config, message)
        if config.has_section("email") and config.getboolean("email", "enabled", fallback=False):
            send_email_notification(config, message)
        if config.has_section("slack") and config.getboolean("slack", "enabled", fallback=False):
            send_slack_notification(config, message)
        if config.has_section("sms") and config.getboolean("sms", "enabled", fallback=False):
            send_sms_notification(config, message)
        if config.has_section("viber") and config.getboolean("viber", "enabled", fallback=False):
            send_viber_notification(config, message)

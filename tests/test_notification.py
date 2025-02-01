import unittest
from unittest.mock import patch, MagicMock
from src.notifications import send_telegram_notification, send_email_notification, send_slack_notification
from src.config import CONFIG

class TestNotifications(unittest.TestCase):
    @patch("src.notifications.requests.post")
    def test_send_telegram_notification(self, mock_post):
        # Prepare a dummy config with telegram enabled
        dummy_config = CONFIG
        dummy_config["telegram"] = {
            "enabled": "true",
            "telegram_token": "dummy_token",
            "telegram_chatid": "dummy_chat"
        }
        send_telegram_notification(dummy_config, "Test Telegram message")
        self.assertTrue(mock_post.called, "requests.post was not called for Telegram")

    @patch("src.notifications.smtplib.SMTP")
    def test_send_email_notification(self, mock_smtp):
        dummy_config = CONFIG
        dummy_config["email"] = {
            "enabled": "true",
            "smtp_server": "smtp.example.com",
            "smtp_port": "587",
            "username": "user@example.com",
            "password": "secret",
            "from_address": "from@example.com",
            "to_addresses": "to@example.com"
        }
        send_email_notification(dummy_config, "Test Email message")
        self.assertTrue(mock_smtp.called, "SMTP was not called for Email")

    @patch("src.notifications.requests.post")
    def test_send_slack_notification(self, mock_post):
        # Configure the mock to simulate a successful Slack response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        dummy_config = CONFIG
        dummy_config["slack"] = {
            "enabled": "true",
            "webhook_url": "https://hooks.slack.com/services/dummy"
        }

        # Call the Slack notification function
        send_slack_notification(dummy_config, "Test Slack message")

        # Ensure requests.post was actually called
        self.assertTrue(mock_post.called, "requests.post was not called for Slack")

        # Verify we call requests.post with the correct URL and JSON payload
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/dummy",
            json={"text": "Test Slack message"}
        )

if __name__ == "__main__":
    unittest.main()

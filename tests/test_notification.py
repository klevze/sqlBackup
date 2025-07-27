import unittest
import configparser
from unittest.mock import patch, MagicMock
from sql_backup.notifications import send_telegram_notification, send_email_notification, send_slack_notification

class TestNotifications(unittest.TestCase):
    def setUp(self):
        """Set up test configuration."""
        self.dummy_config = configparser.ConfigParser()
    
    @patch("sql_backup.notifications.requests.post")
    def test_send_telegram_notification(self, mock_post):
        # Prepare a dummy config with telegram enabled
        self.dummy_config.add_section("telegram")
        self.dummy_config.set("telegram", "enabled", "true")
        self.dummy_config.set("telegram", "telegram_token", "dummy_token")
        self.dummy_config.set("telegram", "telegram_chatid", "dummy_chat")
        
        send_telegram_notification(self.dummy_config, "Test Telegram message")
        self.assertTrue(mock_post.called, "requests.post was not called for Telegram")

    @patch("sql_backup.notifications.smtplib.SMTP")
    def test_send_email_notification(self, mock_smtp):
        self.dummy_config.add_section("email")
        self.dummy_config.set("email", "enabled", "true")
        self.dummy_config.set("email", "smtp_server", "smtp.example.com")
        self.dummy_config.set("email", "smtp_port", "587")
        self.dummy_config.set("email", "username", "user@example.com")
        self.dummy_config.set("email", "password", "secret")
        self.dummy_config.set("email", "from_address", "from@example.com")
        self.dummy_config.set("email", "to_addresses", "to@example.com")
        
        send_email_notification(self.dummy_config, "Test Email message")
        self.assertTrue(mock_smtp.called, "SMTP was not called for Email")

    @patch("sql_backup.notifications.requests.post")
    def test_send_slack_notification(self, mock_post):
        # Configure the mock to simulate a successful Slack response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        self.dummy_config.add_section("slack")
        self.dummy_config.set("slack", "enabled", "true")
        self.dummy_config.set("slack", "webhook_url", "https://hooks.slack.com/services/dummy")

        # Call the Slack notification function
        send_slack_notification(self.dummy_config, "Test Slack message")

        # Ensure requests.post was actually called
        self.assertTrue(mock_post.called, "requests.post was not called for Slack")

        # Verify we call requests.post with the correct URL and JSON payload
        mock_post.assert_called_once_with(
            "https://hooks.slack.com/services/dummy",
            json={"text": "Test Slack message"}
        )

if __name__ == "__main__":
    unittest.main()

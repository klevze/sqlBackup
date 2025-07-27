#!/usr/bin/env python3
"""
Comprehensive test suite for notifications module
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock, call
import smtplib
import requests

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sql_backup.notifications import NotificationManager
from sql_backup.config import Config


class TestNotificationManager(unittest.TestCase):
    """Comprehensive tests for NotificationManager class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock config
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.notifications.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        # Create notification manager instance
        self.notifier = NotificationManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
    
    def test_init(self):
        """Test NotificationManager initialization."""
        self.assertEqual(self.notifier.config, self.mock_config)
        self.assertIsNotNone(self.notifier.logger)
    
    def test_send_notification_no_channels(self):
        """Test sending notification when no channels are configured."""
        self.mock_config.getlist.return_value = []
        
        self.notifier.send_notification("Test message")
        
        # Should log info about no channels
        self.mock_logger.return_value.info.assert_called()
    
    def test_send_notification_multiple_channels(self):
        """Test sending notification to multiple channels."""
        self.mock_config.getlist.return_value = ['telegram', 'email', 'slack']
        
        with patch.object(self.notifier, '_send_telegram', return_value=True) as mock_telegram, \
             patch.object(self.notifier, '_send_email', return_value=True) as mock_email, \
             patch.object(self.notifier, '_send_slack', return_value=True) as mock_slack:
            
            self.notifier.send_notification("Test message")
            
            mock_telegram.assert_called_once_with("Test message")
            mock_email.assert_called_once_with("Test message")
            mock_slack.assert_called_once_with("Test message")
    
    def test_send_notification_unknown_channel(self):
        """Test sending notification to unknown channel."""
        self.mock_config.getlist.return_value = ['unknown_channel']
        
        self.notifier.send_notification("Test message")
        
        # Should log warning about unknown channel
        self.mock_logger.return_value.warning.assert_called()


class TestTelegramNotifications(unittest.TestCase):
    """Test Telegram notification functionality."""
    
    def setUp(self):
        """Set up Telegram test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.notifications.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.notifier = NotificationManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
    
    def test_send_telegram_disabled(self):
        """Test Telegram notification when disabled."""
        self.mock_config.getboolean.return_value = False
        
        result = self.notifier._send_telegram("Test message")
        
        self.assertFalse(result)
        self.mock_config.getboolean.assert_called_with('telegram', 'enabled', False)
    
    def test_send_telegram_missing_config(self):
        """Test Telegram notification with missing configuration."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['', '12345']  # Empty bot_token, valid chat_id
        
        result = self.notifier._send_telegram("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.requests.post')
    def test_send_telegram_success(self, mock_post):
        """Test successful Telegram notification."""
        # Setup config mocks
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['123456789:ABCdef', '987654321']
        
        # Setup successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_post.return_value = mock_response
        
        result = self.notifier._send_telegram("Test message")
        
        self.assertTrue(result)
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        expected_url = 'https://api.telegram.org/bot123456789:ABCdef/sendMessage'
        self.assertEqual(call_args[0][0], expected_url)
        
        # Check payload
        payload = call_args[1]['json']
        self.assertEqual(payload['chat_id'], '987654321')
        self.assertEqual(payload['text'], 'Test message')
        self.assertEqual(payload['parse_mode'], 'HTML')
    
    @patch('src.notifications.requests.post')
    def test_send_telegram_api_error(self, mock_post):
        """Test Telegram notification with API error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['123456789:ABCdef', '987654321']
        
        # Setup error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response
        
        result = self.notifier._send_telegram("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.requests.post')
    def test_send_telegram_network_error(self, mock_post):
        """Test Telegram notification with network error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['123456789:ABCdef', '987654321']
        
        # Setup network error
        mock_post.side_effect = requests.RequestException("Network error")
        
        result = self.notifier._send_telegram("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestEmailNotifications(unittest.TestCase):
    """Test Email notification functionality."""
    
    def setUp(self):
        """Set up Email test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.notifications.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.notifier = NotificationManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
    
    def test_send_email_disabled(self):
        """Test email notification when disabled."""
        self.mock_config.getboolean.return_value = False
        
        result = self.notifier._send_email("Test message")
        
        self.assertFalse(result)
    
    def test_send_email_missing_config(self):
        """Test email notification with missing configuration."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['', 'smtp.gmail.com', '587', 'password', 'recipient@test.com']
        
        result = self.notifier._send_email("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class):
        """Test successful email notification."""
        # Setup config mocks
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = [
            'sender@test.com',      # sender_email
            'smtp.gmail.com',       # smtp_server
            'app_password',         # sender_password
            'recipient@test.com'    # recipient_email
        ]
        self.mock_config.getint.return_value = 587  # smtp_port
        
        # Setup SMTP mock
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        
        result = self.notifier._send_email("Test message")
        
        self.assertTrue(result)
        
        # Verify SMTP operations
        mock_smtp_class.assert_called_once_with('smtp.gmail.com', 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with('sender@test.com', 'app_password')
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    @patch('src.notifications.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp_class):
        """Test email notification with SMTP error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = [
            'sender@test.com', 'smtp.gmail.com', 'password', 'recipient@test.com'
        ]
        self.mock_config.getint.return_value = 587
        
        # Setup SMTP error
        mock_smtp_class.side_effect = smtplib.SMTPException("SMTP error")
        
        result = self.notifier._send_email("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.smtplib.SMTP')
    def test_send_email_auth_error(self, mock_smtp_class):
        """Test email notification with authentication error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = [
            'sender@test.com', 'smtp.gmail.com', 'wrong_password', 'recipient@test.com'
        ]
        self.mock_config.getint.return_value = 587
        
        mock_smtp = Mock()
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp_class.return_value = mock_smtp
        
        result = self.notifier._send_email("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestSlackNotifications(unittest.TestCase):
    """Test Slack notification functionality."""
    
    def setUp(self):
        """Set up Slack test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.notifications.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.notifier = NotificationManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
    
    def test_send_slack_disabled(self):
        """Test Slack notification when disabled."""
        self.mock_config.getboolean.return_value = False
        
        result = self.notifier._send_slack("Test message")
        
        self.assertFalse(result)
    
    def test_send_slack_missing_webhook(self):
        """Test Slack notification with missing webhook URL."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = ''  # Empty webhook URL
        
        result = self.notifier._send_slack("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.requests.post')
    def test_send_slack_success(self, mock_post):
        """Test successful Slack notification."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'https://hooks.slack.com/services/test'
        
        # Setup successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'ok'
        mock_post.return_value = mock_response
        
        result = self.notifier._send_slack("Test message")
        
        self.assertTrue(result)
        
        # Verify webhook call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        self.assertEqual(call_args[0][0], 'https://hooks.slack.com/services/test')
        
        payload = call_args[1]['json']
        self.assertEqual(payload['text'], 'Test message')
    
    @patch('src.notifications.requests.post')
    def test_send_slack_webhook_error(self, mock_post):
        """Test Slack notification with webhook error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.return_value = 'https://hooks.slack.com/services/test'
        
        # Setup error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'invalid_payload'
        mock_post.return_value = mock_response
        
        result = self.notifier._send_slack("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


class TestSMSNotifications(unittest.TestCase):
    """Test SMS notification functionality."""
    
    def setUp(self):
        """Set up SMS test environment."""
        self.mock_config = Mock(spec=Config)
        
        # Mock logger
        self.logger_patcher = patch('src.notifications.get_logger')
        self.mock_logger = self.logger_patcher.start()
        self.mock_logger.return_value = MagicMock()
        
        self.notifier = NotificationManager(self.mock_config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.logger_patcher.stop()
    
    def test_send_sms_disabled(self):
        """Test SMS notification when disabled."""
        self.mock_config.getboolean.return_value = False
        
        result = self.notifier._send_sms("Test message")
        
        self.assertFalse(result)
    
    def test_send_sms_missing_config(self):
        """Test SMS notification with missing configuration."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = ['', 'auth_token', '+1234567890', '+0987654321']
        
        result = self.notifier._send_sms("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()
    
    @patch('src.notifications.Client')
    def test_send_sms_success(self, mock_client_class):
        """Test successful SMS notification."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = [
            'ACtest123',         # account_sid
            'auth_token',        # auth_token
            '+1234567890',       # from_phone
            '+0987654321'        # to_phone
        ]
        
        # Setup Twilio client mock
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = 'SM123456'
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client
        
        result = self.notifier._send_sms("Test message")
        
        self.assertTrue(result)
        
        # Verify Twilio API call
        mock_client_class.assert_called_once_with('ACtest123', 'auth_token')
        mock_client.messages.create.assert_called_once_with(
            body='Test message',
            from_='+1234567890',
            to='+0987654321'
        )
    
    @patch('src.notifications.Client')
    def test_send_sms_twilio_error(self, mock_client_class):
        """Test SMS notification with Twilio error."""
        self.mock_config.getboolean.return_value = True
        self.mock_config.get.side_effect = [
            'ACtest123', 'auth_token', '+1234567890', '+0987654321'
        ]
        
        # Setup Twilio error
        from twilio.base.exceptions import TwilioException
        mock_client = Mock()
        mock_client.messages.create.side_effect = TwilioException("SMS failed")
        mock_client_class.return_value = mock_client
        
        result = self.notifier._send_sms("Test message")
        
        self.assertFalse(result)
        self.mock_logger.return_value.error.assert_called()


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)

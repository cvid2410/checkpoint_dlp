from unittest.mock import MagicMock, patch

from django.test import TestCase

from dlp.utils import add_bot_to_channel, enqueue_message


class EnqueueMessageTestCase(TestCase):
    @patch("dlp.utils.pika.BlockingConnection")
    def test_enqueue_message(self, mock_blocking_connection):
        # Arrange
        mock_connection = MagicMock()
        mock_channel = MagicMock()

        mock_blocking_connection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        message_text = "Test message"
        additional_info = {
            "user": "U123",
            "channel": "C123",
            "ts": "1624325400.000200",
        }

        # Act

        enqueue_message(message_text, additional_info)

        # Assert
        mock_blocking_connection.assert_called_once()
        mock_connection.channel.assert_called_once()
        mock_channel.queue_declare.assert_called_once_with(
            queue="slack_messages", durable=True
        )
        mock_channel.basic_publish.assert_called_once()
        mock_connection.close.assert_called_once()


class AddBotToChannelTestCase(TestCase):
    @patch("dlp.utils.WebClient")
    def test_add_bot_to_channel(self, mock_web_client):
        # Arrange
        mock_client = MagicMock()
        mock_web_client.return_value = mock_client

        channel_id = "C123"
        channel_name = "general"

        # Act
        add_bot_to_channel(channel_id, channel_name)

        # Assert
        mock_client.conversations_join.assert_called_once_with(channel=channel_id)

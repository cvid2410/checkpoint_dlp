import json
from unittest.mock import patch

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from dlp.enums import SlackEventType, SlackWebhookEventType
from dlp.models import CaughtMessage, Pattern
from dlp.serializers import PatternSerializer
from dlp.views import slack_event_webhooks_handler


class PatternListAPIViewTestCase(APITestCase):
    def setUp(self):
        _, key = APIKey.objects.create_key(name="Test API Key")
        self.api_key = key

        Pattern.objects.create(
            name="Credit Card", regex_pattern=r"\b\d{4}-?\d{4}-?\d{4}-?\d{4}\b"
        )
        Pattern.objects.create(name="SSN", regex_pattern=r"\b\d{3}-\d{2}-\d{4}\b")

    def test_get_patterns_unauthorized(self):
        response = self.client.get("/api/patterns/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_patterns(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.api_key}")
        response = self.client.get("/api/patterns/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        patterns = Pattern.objects.all()
        serializer = PatternSerializer(patterns, many=True)
        self.assertEqual(response.data, serializer.data)


class CaughtMessageCreateAPIViewTestCase(APITestCase):
    def setUp(self):
        self.pattern = Pattern.objects.create(
            name="Credit Card", regex_pattern=r"\b\d{4}-?\d{4}-?\d{4}-?\d{4}\b"
        )

        self.api_key, self.key = APIKey.objects.create_key(name="test-key")

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.key}")

    def test_create_caught_message(self):
        # Arrange
        data = {
            "user_id": "U123456",
            "channel": "C123456",
            "timestamp": "1730222429.482539",
            "message_content": "This is a test message with 1234-5678-9012-3456.",
            "pattern_matched": self.pattern.id,
        }

        # Act
        response = self.client.post("/api/caught_messages/", data, format="json")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        caught_message = CaughtMessage.objects.get(user_id="U123456")
        self.assertEqual(
            caught_message.message_content,
            "This is a test message with 1234-5678-9012-3456.",
        )


class SlackEventWebhooksHandlerTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.slack_signing_secret = "test_secret"

    @patch("dlp.views.SignatureVerifier.is_valid_request")
    def test_url_verification(self, mock_is_valid_request):
        # Arrange
        mock_is_valid_request.return_value = True

        payload = {
            "type": SlackWebhookEventType.URL_VERIFICATION.value,
            "challenge": "test_challenge",
        }

        # Act
        request = self.factory.post(
            "/slack/events/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Test",
        )

        response = slack_event_webhooks_handler(request)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertJSONEqual(response.content, {"challenge": "test_challenge"})

    @patch("dlp.views.SignatureVerifier.is_valid_request")
    @patch("dlp.views.enqueue_message")
    def test_event_callback_message(self, mock_enqueue_message, mock_is_valid_request):
        # Arrange
        mock_is_valid_request.return_value = True

        payload = {
            "type": SlackWebhookEventType.EVENT_CALLBACK.value,
            "event": {
                "type": SlackEventType.MESSAGE.value,
                "user": "U123",
                "channel": "C123",
                "ts": "1624325400.000200",
                "text": "Test message",
                "bot_id": None,
                "files": [],
            },
        }

        # Act
        request = self.factory.post(
            "/slack/events/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Test",
        )

        # Assert
        response = slack_event_webhooks_handler(request)
        self.assertEqual(response.status_code, 200)
        mock_enqueue_message.assert_called_once_with(
            "Test message",
            {
                "user": "U123",
                "channel": "C123",
                "ts": "1624325400.000200",
                "files": [],
            },
        )

    @patch("dlp.views.SignatureVerifier.is_valid_request")
    @patch("dlp.views.add_bot_to_channel")
    def test_event_callback_channel_created(
        self, mock_add_bot_to_channel, mock_is_valid_request
    ):
        # Arrange
        mock_is_valid_request.return_value = True

        payload = {
            "type": SlackWebhookEventType.EVENT_CALLBACK.value,
            "event": {
                "type": SlackEventType.CHANNEL_CREATED.value,
                "channel": {
                    "id": "C123",
                    "name": "general",
                },
            },
        }

        # Act
        request = self.factory.post(
            "/slack/events/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Test",
        )

        response = slack_event_webhooks_handler(request)

        # Assert
        self.assertEqual(response.status_code, 200)
        mock_add_bot_to_channel.assert_called_once_with("C123", "general")

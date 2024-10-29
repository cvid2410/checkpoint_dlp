from enum import Enum


class SlackWebhookEventType(str, Enum):
    URL_VERIFICATION = "url_verification"
    EVENT_CALLBACK = "event_callback"


class SlackEventType(str, Enum):
    MESSAGE = "message"
    CHANNEL_CREATED = "channel_created"

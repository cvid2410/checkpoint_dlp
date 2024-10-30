import json
import logging
import os

import pika
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


def enqueue_message(message_text: str, additional_info: dict) -> None:
    """
    Enqueues a message to RabbitMQ to be processed by the dlp_processor service
    """
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
    credentials = pika.PlainCredentials(str(rabbitmq_user), str(rabbitmq_password))

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", credentials=credentials)
    )

    task_message = {
        "task": "scan_message",
        "args": (message_text,),
        "kwargs": {"additional_info": additional_info},
    }

    channel = connection.channel()
    channel.queue_declare(queue="slack_messages", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="slack_messages",
        body=json.dumps(task_message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )
    connection.close()


def add_bot_to_channel(channel_id: str, channel_name: str) -> None:
    """
    Adds dlp_scanner to a given channel
    """
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    client = WebClient(token=slack_bot_token)

    try:
        client.conversations_join(channel=channel_id)
        print(f"Joined channel {channel_name} ({channel_id})")
    except SlackApiError as e:
        logger.exception(
            f"Slack API Error while joining channel {channel_name} ({channel_id}): {e.response['error']}"
        )


def delete_slack_message(channel: str, ts: str) -> None:
    """
    Deletes a Slack message based on channel ID and timestamp.
    """
    slack_bot_token = os.getenv("SLACK_BOT_USER")
    client = WebClient(token=slack_bot_token)

    try:
        client.chat_delete(channel=channel, ts=ts)
        logger.info(f"Message deleted in channel {channel} at timestamp {ts}")
    except SlackApiError as e:
        logger.error(f"Slack API Error while deleting message: {e.response['error']}")

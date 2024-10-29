import json
import os

import pika
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def enqueue_message(message_text: str, additional_info: dict) -> None:
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
    slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
    client = WebClient(token=slack_bot_token)

    try:
        client.conversations_join(channel=channel_id)
        print(f"Joined channel {channel_name} ({channel_id})")
    except SlackApiError as e:
        print(
            f"Slack API Error while joining channel {channel_name} ({channel_id}): {e.response['error']}"
        )

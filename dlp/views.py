import json
import os

import pika
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

from dlp.models import Pattern

from .serializers import CaughtMessageSerializer, PatternSerializer


@csrf_exempt
def slack_event_webhooks_handler(request):

    slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    verifier = SignatureVerifier(signing_secret=str(slack_signing_secret))

    if not verifier.is_valid_request(request.body, request.headers):
        return HttpResponse(status=403)

    if request.method == "POST":
        event_data = json.loads(request.body)

        if event_data.get("type") == "url_verification":
            return JsonResponse({"challenge": event_data.get("challenge")})

        elif event_data.get("type") == "event_callback":
            # Handle the event
            event = event_data.get("event")
            if event.get("type") == "message" and not event.get("bot_id"):

                additional_info = {
                    "user": event.get("user"),
                    "channel": event.get("channel"),
                    "ts": event.get("ts"),
                    "files": event.get("files", []),
                }
                enqueue_message(event.get("text", ""), additional_info)

            elif event.get("type") == "channel_created":
                channel_info = event.get("channel")
                channel_id = channel_info.get("id")
                channel_name = channel_info.get("name")

                if channel_id:
                    add_bot_to_channel(channel_id, channel_name)

            return HttpResponse(status=200)

    else:
        return HttpResponse(status=405)


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


class PatternListAPIView(APIView):
    permission_classes = [HasAPIKey]

    def get(self, request):
        """@TODO: include caching here"""
        patterns = Pattern.objects.all()
        serializer = PatternSerializer(patterns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CaughtMessageCreateAPIView(APIView):
    permission_classes = [HasAPIKey]

    def post(self, request):
        serializer = CaughtMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

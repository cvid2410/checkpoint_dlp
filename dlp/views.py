import json
import os

import pika
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from slack_sdk.signature import SignatureVerifier

from dlp.models import Pattern

from .serializers import PatternSerializer


@csrf_exempt
def slack_event_webhooks_handler(request):

    slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    verifier = SignatureVerifier(signing_secret=str(slack_signing_secret))

    if not verifier.is_valid_request(request.body, request.headers):
        raise ValueError("Invalid request/credentials.")

    if request.method == "POST":
        event_data = json.loads(request.body)

        if event_data.get("type") == "url_verification":
            return JsonResponse({"challenge": event_data.get("challenge")})

        if event_data.get("type") == "event_callback":
            # Handle the event
            event = event_data.get("event")
            if event.get("type") == "message" and not event.get("bot_id"):

                message_data = {
                    "user": event.get("user"),
                    "text": event.get("text"),
                    "channel": event.get("channel"),
                    "ts": event.get("ts"),
                }

                enqueue_message(message_data)

            return HttpResponse(status=200)

    else:
        return HttpResponse(status=405)


def enqueue_message(message_data: dict) -> None:
    rabbitmq_user = os.getenv("RABBITMQ_USER")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
    credentials = pika.PlainCredentials(str(rabbitmq_user), str(rabbitmq_password))

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", credentials=credentials)
    )

    channel = connection.channel()
    channel.queue_declare(queue="slack_messages", durable=True)
    channel.basic_publish(
        exchange="",
        routing_key="slack_messages",
        body=json.dumps(message_data),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )
    connection.close()


class PatternListAPIView(APIView):
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request):
        patterns = Pattern.objects.all()
        serializer = PatternSerializer(patterns, many=True)
        return Response(serializer.data)

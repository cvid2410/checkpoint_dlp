import json
import os
from typing import Union

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey
from slack_sdk.signature import SignatureVerifier

from dlp.enums import SlackEventType, SlackWebhookEventType
from dlp.models import Pattern
from dlp.utils import add_bot_to_channel, delete_slack_message, enqueue_message

from .serializers import CaughtMessageSerializer, PatternSerializer


@csrf_exempt
def slack_event_webhooks_handler(
    request: HttpRequest,
) -> Union[HttpResponse, JsonResponse]:

    slack_signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    verifier = SignatureVerifier(signing_secret=str(slack_signing_secret))

    if not verifier.is_valid_request(request.body, dict(request.headers)):
        return HttpResponse(status=403)

    if request.method == "POST":
        event_data = json.loads(request.body)

        if event_data.get("type") == SlackWebhookEventType.URL_VERIFICATION:
            return JsonResponse({"challenge": event_data.get("challenge")})

        elif event_data.get("type") == SlackWebhookEventType.EVENT_CALLBACK:
            event = event_data.get("event")

            if event.get("type") == SlackEventType.MESSAGE and not event.get("bot_id"):

                additional_info = {
                    "user": event.get("user"),
                    "channel": event.get("channel"),
                    "ts": event.get("ts"),
                    "files": event.get("files", []),
                }
                enqueue_message(event.get("text", ""), additional_info)

            elif event.get("type") == SlackEventType.CHANNEL_CREATED:
                channel_info = event.get("channel")
                channel_id = channel_info.get("id")
                channel_name = channel_info.get("name")

                if channel_id:
                    add_bot_to_channel(channel_id, channel_name)

        return HttpResponse(status=200)

    else:
        return HttpResponse(status=405)


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

            try:

                channel = serializer.validated_data.get("channel")
                timestamp = serializer.validated_data.get("timestamp")

                delete_slack_message(str(channel), str(timestamp))

            except Exception as e:
                print(e)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

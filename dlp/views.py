import json
import os

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from slack_sdk.signature import SignatureVerifier


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
            pass
       
            
    else:
        return HttpResponse(status=405)

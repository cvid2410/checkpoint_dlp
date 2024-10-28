from django.urls import path

from . import views

urlpatterns = [
    path('slack/events', views.slack_event_webhooks_handler, name='slack_event_webhooks_handler'),
]

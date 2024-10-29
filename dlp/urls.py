from django.urls import path

from . import views

urlpatterns = [
    path(
        "slack/events",
        views.slack_event_webhooks_handler,
        name="slack_event_webhooks_handler",
    ),
    path("api/patterns/", views.PatternListAPIView.as_view(), name="get_patterns"),
    path(
        "api/caught_messages/",
        views.CaughtMessageCreateAPIView.as_view(),
        name="create_caught_message",
    ),
]

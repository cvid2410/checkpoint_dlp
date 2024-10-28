from django.contrib import admin

from .models import CaughtMessage, Pattern


@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ("name", "regex_pattern", "description", "created_at", "updated_at")
    search_fields = ("name", "regex_pattern")


@admin.register(CaughtMessage)
class CaughtMessageAdmin(admin.ModelAdmin):
    list_display = ("message_content", "pattern_matched", "created_at")
    search_fields = ("message_content",)
    list_filter = ("pattern_matched", "created_at")

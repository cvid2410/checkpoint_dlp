from rest_framework import serializers

from .models import CaughtMessage, Pattern


class PatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pattern
        fields = ["id", "name", "regex_pattern"]


class CaughtMessageSerializer(serializers.ModelSerializer):

    pattern_matched = serializers.PrimaryKeyRelatedField(queryset=Pattern.objects.all())

    class Meta:
        model = CaughtMessage
        fields = "__all__"

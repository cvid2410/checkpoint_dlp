from django.db import models


class BaseModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields and logs attribute setting errors.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Pattern(BaseModel):
    name = models.CharField(max_length=100)
    regex_pattern = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CaughtMessage(BaseModel):
    user_id = models.CharField(max_length=50)
    channel = models.CharField(max_length=255)
    timestamp = models.CharField(max_length=50)
    message_content = models.TextField(null=True, blank=True)
    pattern_matched = models.ForeignKey(Pattern, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_id = models.CharField(max_length=50, null=True, blank=True)
    source_type = models.CharField(max_length=20, choices=[('message', 'Message'), ('file', 'File')], default='message')

    def __str__(self):
        return f"Message caught at {self.created_at}"

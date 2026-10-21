from django.db import models


class ContactRateLimit(models.Model):
    # Only a keyed hash is stored, never the address or contact message.
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

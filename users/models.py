from django.db import models
from django.conf import settings


class GoogleProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_profile",
    )
    google_id = models.CharField(max_length=255, unique=True, db_index=True)
    picture = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Google Profile"
        verbose_name_plural = "Google Profiles"

    def __str__(self):
        return f"{self.user.username} ({self.google_id})"

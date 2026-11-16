from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    name = models.CharField(
        max_length=100,
        blank=True
    )

    bio = models.TextField(
        blank=True
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    contact_links = models.JSONField(
        default=list,
        blank=True
    )

    open_to_collaboration = models.BooleanField(
        default=False
    )

    open_to_mentoring = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name or self.user.username

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Direct negotiation thread between participants, optionally linked to a project.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name="Participants",
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name="Associated Project",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        user_names = ", ".join(self.participants.values_list('username', flat=True))
        if self.project:
            return f"Negotiation: {self.project.title} ({user_names})"
        return f"Chat: {user_names}"


class Message(models.Model):
    """
    Message inside a conversation thread.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Conversation",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name="Sender",
    )
    content = models.TextField(verbose_name="Message Content")
    is_read = models.BooleanField(default=False, verbose_name="Read Status")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

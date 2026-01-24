from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

class AuditLog(models.Model):
    """
    Centralized, immutable audit log for LendFlow.
    """
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs_actor',
        null=True,  # Allow system actions
        blank=True
    )
    
    # Generic relation to target object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    event_type = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    
    payload_before = models.JSONField(null=True, blank=True)
    payload_after = models.JSONField(null=True, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)  # IP, user agent, etc.
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"AuditLog {self.id}: {self.event_type} by {self.actor or 'System'}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Audit records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit records are immutable and cannot be deleted.")

class Blacklist(models.Model):
    """
    Formal record of blacklisted users with reasons and timestamps.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blacklist_records'
    )
    reason = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_blacklists'
    )

    class Meta:
        verbose_name_plural = "Blacklist"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        status = "ACTIVE" if self.is_active else "REVOKED"
        return f"Blacklist for {self.user.username} ({status})"

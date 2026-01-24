from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog, Blacklist
from .events import AuditEventType

class AuditService:
    @staticmethod
    def log_event(actor, target, event_type, description, payload_before=None, payload_after=None, metadata=None):
        """
        Standard utility for logging an audit event.
        """
        content_type = ContentType.objects.get_for_model(target)
        
        return AuditLog.objects.create(
            actor=actor,
            content_type=content_type,
            object_id=str(target.pk),
            event_type=event_type,
            description=description,
            payload_before=payload_before,
            payload_after=payload_after,
            metadata=metadata or {}
        )

class BlacklistService:
    @staticmethod
    def add_to_blacklist(user, reason, actor):
        """
        Formalizes blacklisting of a user. 
        Updates User model flag AND creates a detailed Blacklist record.
        """
        from django.db import transaction
        with transaction.atomic():
            # Create formal record
            blacklist_entry = Blacklist.objects.create(
                user=user,
                reason=reason,
                created_by=actor,
                is_active=True
            )
            
            # Sync to User model flag for performance
            user.is_blacklisted = True
            user.save()
            
            # Audit Log
            AuditService.log_event(
                actor=actor,
                target=user,
                event_type=AuditEventType.USER_BLACKLISTED,
                description=f"User {user.username} blacklisted. Reason: {reason}",
                metadata={"blacklist_id": blacklist_entry.id}
            )
            
            return blacklist_entry

    @staticmethod
    def remove_from_blacklist(user, reason, actor):
        """
        Whitelists a previously blacklisted user.
        """
        from django.db import transaction
        with transaction.atomic():
            # Deactivate all active blacklist records for this user
            Blacklist.objects.filter(user=user, is_active=True).update(
                is_active=False,
                revoked_at=timezone.now()
            )
            
            # Sync to User model flag
            user.is_blacklisted = False
            user.save()
            
            # Audit Log
            AuditService.log_event(
                actor=actor,
                target=user,
                event_type=AuditEventType.USER_WHITELISTED,
                description=f"User {user.username} whitelisted (removed from blacklist). Reason: {reason}"
            )

    @staticmethod
    def is_blacklisted(user):
        """
        Checks if the user has an active blacklist record.
        """
        return Blacklist.objects.filter(user=user, is_active=True).exists()

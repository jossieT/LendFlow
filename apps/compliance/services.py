from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
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

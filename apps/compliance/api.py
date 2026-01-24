import csv
import io
from decimal import Decimal
from django.db.models import Sum, F, Count
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from loans.models import Loan, LoanInstallment
from .models import AuditLog
from .services import AuditService
from .events import AuditEventType
from .serializers import (
    UserExposureSerializer, DefaultRateSerializer, 
    LatePaymentSerializer, AdminActionReportSerializer
)

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        return value

class ComplianceReportViewSet(viewsets.ViewSet):
    """
    ViewSet for generating compliance reports. Restricted to ADMIN users.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _check_admin_role(self, user):
        if getattr(user, 'role', '') != 'ADMIN':
            return False
        return True

    def _log_report_access(self, request, report_name):
        AuditService.log_event(
            actor=request.user,
            target=request.user, # Logging against the admin user
            event_type=AuditEventType.COMPLIANCE_REPORT_GENERATED,
            description=f"Compliance report generated: {report_name}",
            metadata={"report_name": report_name, "format": request.query_params.get('format', 'json')}
        )

    @action(detail=False, methods=['get'])
    def exposure(self, request):
        if not self._check_admin_role(request.user):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        data = Loan.objects.filter(
            status=Loan.Status.ACTIVE
        ).values('borrower', username=F('borrower__username')).annotate(
            total_exposure=Sum('principal')
        ).order_by('-total_exposure')

        if request.query_params.get('format') == 'csv':
            return self._stream_csv(
                header=['Borrower ID', 'Username', 'Total Exposure'],
                rows=[[d['borrower'], d['username'], d['total_exposure']] for d in data],
                filename='user_exposure_report.csv'
            )

        self._log_report_access(request, "User Exposure")
        serializer = UserExposureSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def default_metrics(self, request):
        if not self._check_admin_role(request.user):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        total_count = Loan.objects.count()
        default_count = Loan.objects.filter(status__in=[Loan.Status.DEFAULTED, Loan.Status.CLOSED], is_active=False).count()
        
        metrics = {
            "total_disbursed_count": total_count,
            "default_count": default_count,
            "default_rate": (default_count / total_count * 100) if total_count > 0 else 0
        }

        self._log_report_access(request, "Default Metrics")
        serializer = DefaultRateSerializer(metrics)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def late_payments(self, request):
        if not self._check_admin_role(request.user):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now().date()
        late_installments = LoanInstallment.objects.filter(
            status=LoanInstallment.Status.OVERDUE,
            due_date__lt=now
        ).annotate(
            days_overdue=Count(now - F('due_date')), # SQLite specific or complex in ORM, simplified below
            amount_overdue=F('principal_expected') + F('interest_expected') - F('principal_paid') - F('interest_paid')
        ).select_related('loan__borrower')

        # Complex date diff handling for cross-DB compatibility often needs extra steps
        data = []
        for inst in late_installments:
            data.append({
                "loan_id": inst.loan_id,
                "loan__borrower__username": inst.loan.borrower.username,
                "days_overdue": (now - inst.due_date).days,
                "amount_overdue": inst.amount_overdue
            })

        self._log_report_access(request, "Late Payments")
        serializer = LatePaymentSerializer(data, many=True)
        return Response(serializer.data)

    def _stream_csv(self, header, rows, filename):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        
        def iter_csv():
            yield writer.writerow(header)
            for row in rows:
                yield writer.writerow(row)

        response = StreamingHttpResponse(iter_csv(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

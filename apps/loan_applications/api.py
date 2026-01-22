from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LoanApplication
from .serializers import LoanApplicationSerializer
from .services import ApplicationService

class LoanApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'LOAN_OFFICER']:
            return LoanApplication.objects.all()
        return LoanApplication.objects.filter(borrower=user)

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        application = self.get_object()
        try:
            ApplicationService.transition_status(
                application, 
                LoanApplication.Status.SUBMITTED, 
                request.user
            )
            return Response({'status': 'submitted'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

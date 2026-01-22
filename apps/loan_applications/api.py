from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LoanApplication
from .serializers import LoanApplicationSerializer, TransitionSerializer, ApplicationDocumentSerializer
from .services import ApplicationService

class IsBorrowerOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.borrower == request.user

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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsBorrowerOwner])
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

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        # Admin/Officer only for these transitions
        user = request.user
        if not (user.is_staff or getattr(user, 'role', '') in ['ADMIN', 'LOAN_OFFICER']):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        application = self.get_object()
        serializer = TransitionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                ApplicationService.transition_status(
                    application, 
                    serializer.validated_data['to_status'], 
                    request.user,
                    reason=serializer.validated_data.get('reason', '')
                )
                return Response(LoanApplicationSerializer(application).data)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(application=application, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

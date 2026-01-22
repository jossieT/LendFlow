from rest_framework import viewsets, permissions
from .models import LoanProduct
from .serializers import LoanProductSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit products.
    Borrowers can only read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_staff or request.user.role == 'ADMIN')

class LoanProductViewSet(viewsets.ModelViewSet):
    queryset = LoanProduct.objects.filter(is_active=True)
    serializer_class = LoanProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        # Admins can see inactive products
        if self.request.user.is_staff or getattr(self.request.user, 'role', '') == 'ADMIN':
            return LoanProduct.objects.all()
        return LoanProduct.objects.filter(is_active=True)

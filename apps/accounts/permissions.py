from rest_framework import permissions
from .models import User

class IsLoanOfficer(permissions.BasePermission):
    """
    Allows access only to users with the LOAN_OFFICER role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.LOAN_OFFICER)

class IsBorrower(permissions.BasePermission):
    """
    Allows access only to users with the BORROWER role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.BORROWER)

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to administrators.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == User.Role.ADMIN or request.user.is_staff))

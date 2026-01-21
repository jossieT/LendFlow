from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import AuthViewSet, UserProfileViewSet, KYCViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'kyc', KYCViewSet, basename='kyc')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import LoanProductViewSet

router = DefaultRouter()
router.register(r'', LoanProductViewSet, basename='loan-product')

urlpatterns = [
    path('', include(router.urls)),
]

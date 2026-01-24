from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import PaymentViewSet
from .views import WebhookView

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/<str:provider>/', WebhookView.as_view(), name='gateway-webhook'),
]

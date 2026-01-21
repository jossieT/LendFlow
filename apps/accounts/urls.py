from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path('htmx-login/', views.htmx_login_fragment, name='htmx_login_fragment'),
]

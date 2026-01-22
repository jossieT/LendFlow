"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.register, name='register'),
    path('accounts/htmx-login/', accounts_views.htmx_login_fragment, name='htmx_login_fragment'),
    path('accounts/profile/', core_views.login_router, name='login_router'),
    path('api/accounts/', include('accounts.api_urls')),
    path('api/products/', include('loan_products.api_urls')),
    path('api/applications/', include('loan_applications.api_urls')),
    path('api/payments/', include('payments.api_urls')),
    path('', include('core.urls')), 
]

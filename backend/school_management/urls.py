"""
URL configuration for school_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from administration.auth_views import (
    CustomLoginView, 
    ForgotPasswordView, 
    ForgotPasswordDoneView,
    ResetPasswordView,
    ResetPasswordDoneView
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Django Admin (for system configuration only)
    path('admin/', admin.site.urls),
    
    # Frontend Application (main user interface)
    path('', include('frontend_urls')),
    path('communication/', include('communication.urls')),
    
    # Legacy module URLs (kept for compatibility)
    path('legacy/', include('administration.urls')),
    path('legacy/academics/', include('academics.urls')),
    path('legacy/finance/', include('finance.urls')),
    path('legacy/attendance/', include('attendance.urls')),
    
    # Authentication URLs
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('forgot-password/done/', ForgotPasswordDoneView.as_view(), name='forgot_password_done'),
    path('reset-password/<str:token>/', ResetPasswordView.as_view(), name='reset_password'),
    path('reset-password/done/', ResetPasswordDoneView.as_view(), name='reset_password_done'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

"""
Legacy URLs - kept for backward compatibility
All new features should use frontend_urls.py
"""
from django.urls import path
from django.shortcuts import redirect

app_name = 'administration'

# Redirect legacy URLs to new frontend
urlpatterns = [
    path('', lambda request: redirect('frontend:dashboard'), name='dashboard'),
]

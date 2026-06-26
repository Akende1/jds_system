from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model
from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import FormView, View
from django.urls import reverse_lazy
from django.utils import timezone
from .models import PasswordResetToken
from .forms import ForgotPasswordForm, ResetPasswordForm
from communication.email_utils import EmailSender
from django.contrib.auth.hashers import make_password

User = get_user_model()


class CustomLoginView(auth_views.LoginView):
    """Override LoginView to prevent student accounts from logging in."""

    def form_valid(self, form):
        user = form.get_user()
        if getattr(user, 'user_type', None) == 'student':
            form.add_error(None, 'Student portal logins are disabled. Parents access student data via their accounts.')
            return self.form_invalid(form)
        return super().form_valid(form)


class ForgotPasswordView(FormView):
    """Display forgot password form and send reset email"""
    template_name = 'registration/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('forgot_password_done')
    
    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            # Create password reset token
            reset_token = PasswordResetToken.create_token(user, expires_in_hours=24)
            
            # Send reset email
            reset_link = self.request.build_absolute_uri(
                reverse_lazy('reset_password', kwargs={'token': reset_token.token})
            )
            
            context = {
                'user': user,
                'reset_link': reset_link,
                'email': user.email,
                'expires_in_hours': 24,
            }
            
            EmailSender.send_email(
                subject='Password Reset Request - School Management System',
                to_emails=user.email,
                template_name='password_reset',
                context=context
            )
            
            messages.success(
                self.request,
                'If an account exists with this email, you will receive password reset instructions.'
            )
        except User.DoesNotExist:
            # Don't reveal whether email exists for security
            messages.success(
                self.request,
                'If an account exists with this email, you will receive password reset instructions.'
            )
        
        return super().form_valid(form)


class ForgotPasswordDoneView(FormView):
    """Display confirmation message after forgot password form submission"""
    template_name = 'registration/forgot_password_done.html'
    form_class = forms.Form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Password Reset Email Sent'
        return context


class ResetPasswordView(FormView):
    """Handle password reset using token"""
    template_name = 'registration/reset_password.html'
    form_class = ResetPasswordForm
    success_url = reverse_lazy('reset_password_done')
    
    def dispatch(self, request, *args, **kwargs):
        """Validate token before allowing access to form"""
        token = kwargs.get('token')
        try:
            self.reset_token = PasswordResetToken.objects.get(token=token)
            if not self.reset_token.is_valid():
                messages.error(
                    request,
                    'This password reset link has expired or has already been used. '
                    'Please request a new password reset.'
                )
                return redirect('forgot_password')
        except PasswordResetToken.DoesNotExist:
            messages.error(
                request,
                'Invalid password reset link. Please request a new password reset.'
            )
            return redirect('forgot_password')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Reset the user's password"""
        new_password = form.cleaned_data.get('new_password1')
        
        user = self.reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        self.reset_token.is_used = True
        self.reset_token.save()
        
        messages.success(
            self.request,
            'Your password has been successfully reset. You can now log in with your new password.'
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['token'] = self.reset_token.token
        context['title'] = 'Reset Your Password'
        return context


class ResetPasswordDoneView(FormView):
    """Display confirmation message after successful password reset"""
    template_name = 'registration/reset_password_done.html'
    form_class = forms.Form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Password Reset Complete'
        return context


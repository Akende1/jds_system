"""
Forms for authentication and account management
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class ForgotPasswordForm(forms.Form):
    """Form for requesting a password reset"""
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True,
        })
    )
    
    def clean_email(self):
        """Verify that the email exists in the system"""
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            # Only allow non-student users to reset password
            if user.user_type == 'student':
                raise ValidationError(
                    'Student accounts cannot reset passwords through this form. '
                    'Please contact the administration.'
                )
        except User.DoesNotExist:
            raise ValidationError(
                'No account found with this email address. '
                'Please check and try again.'
            )
        return email


class ResetPasswordForm(forms.Form):
    """Form for resetting password with token validation"""
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
        }),
        help_text='Password must be at least 8 characters long.'
    )
    new_password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
        })
    )
    
    def clean(self):
        """Validate that passwords match and meet requirements"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    'The passwords do not match. Please try again.'
                )
            if len(password1) < 8:
                raise ValidationError(
                    'Password must be at least 8 characters long.'
                )
        
        return cleaned_data

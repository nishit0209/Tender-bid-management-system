"""
Forms — Accounts App
Phase 2: Authentication & User Roles
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserRole

User = get_user_model()

# ─────────────────────────────────────────────
# Shared Widget CSS Classes (module-level)
# ─────────────────────────────────────────────
_DARK = (
    'w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg '
    'text-white placeholder-slate-400 focus:outline-none focus:ring-2 '
    'focus:ring-indigo-500 focus:border-transparent transition'
)
_LIGHT = (
    'w-full px-4 py-3 bg-white border border-gray-300 rounded-lg '
    'text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 '
    'focus:ring-indigo-500 focus:border-transparent transition'
)


# ─────────────────────────────────────────────
# Login Form
# ─────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    """Email/password login form with Tailwind widget attrs."""

    username = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': _DARK,
            'placeholder': 'you@company.com',
            'autocomplete': 'email',
            'id': 'id_email',
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': _DARK,
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'id': 'id_password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_('Remember me for 8 hours'),
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500',
            'id': 'id_remember_me',
        })
    )


# ─────────────────────────────────────────────
# Vendor Registration Form
# ─────────────────────────────────────────────
class VendorRegistrationForm(forms.ModelForm):
    """Registration form for new vendor users."""

    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': _DARK,
            'placeholder': 'Minimum 8 characters',
            'autocomplete': 'new-password',
            'id': 'id_password1',
        }),
        help_text=_('Must be at least 8 characters and not entirely numeric.'),
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': _DARK,
            'placeholder': 'Repeat your password',
            'autocomplete': 'new-password',
            'id': 'id_password2',
        }),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': _DARK,
                'placeholder': 'John',
                'id': 'id_first_name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': _DARK,
                'placeholder': 'Doe',
                'id': 'id_last_name',
            }),
            'email': forms.EmailInput(attrs={
                'class': _DARK,
                'placeholder': 'john@yourcompany.com',
                'id': 'id_email',
            }),
            'phone': forms.TextInput(attrs={
                'class': _DARK,
                'placeholder': '+91 98765 43210',
                'id': 'id_phone',
            }),
        }
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Business Email'),
            'phone': _('Phone Number'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('An account with this email already exists. Please login instead.')
            )
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Passwords do not match.'))
        return p2

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise forms.ValidationError(_('Password must be at least 8 characters long.'))
        if password and password.isdigit():
            raise forms.ValidationError(_('Password cannot be entirely numeric.'))
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.VENDOR
        user.is_active = True
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# Staff Registration Form (Admin use only)
# ─────────────────────────────────────────────
class StaffRegistrationForm(forms.ModelForm):
    """Admin-only form to create procurement officers and managers."""

    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': _LIGHT, 'placeholder': 'Set password'}),
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': _LIGHT, 'placeholder': 'Repeat password'}),
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'role', 'department', 'designation', 'employee_id',
        ]
        widgets = {
            'first_name':   forms.TextInput(attrs={'class': _LIGHT}),
            'last_name':    forms.TextInput(attrs={'class': _LIGHT}),
            'email':        forms.EmailInput(attrs={'class': _LIGHT}),
            'phone':        forms.TextInput(attrs={'class': _LIGHT}),
            'role':         forms.Select(attrs={'class': _LIGHT}),
            'department':   forms.TextInput(attrs={'class': _LIGHT}),
            'designation':  forms.TextInput(attrs={'class': _LIGHT}),
            'employee_id':  forms.TextInput(attrs={'class': _LIGHT}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Passwords do not match.'))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.is_verified = True
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
# Profile Edit Form
# ─────────────────────────────────────────────
class ProfileEditForm(forms.ModelForm):
    """Form for users to update their own profile."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone',
            'department', 'designation', 'profile_picture',
        ]
        widgets = {
            'first_name':   forms.TextInput(attrs={'class': _LIGHT, 'placeholder': 'First name'}),
            'last_name':    forms.TextInput(attrs={'class': _LIGHT, 'placeholder': 'Last name'}),
            'phone':        forms.TextInput(attrs={'class': _LIGHT, 'placeholder': '+91 98765 43210'}),
            'department':   forms.TextInput(attrs={'class': _LIGHT, 'placeholder': 'e.g. IT, Finance'}),
            'designation':  forms.TextInput(attrs={'class': _LIGHT, 'placeholder': 'e.g. Manager'}),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'id_profile_picture',
                'accept': 'image/*',
            }),
        }

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture and hasattr(picture, 'size'):
            if picture.size > 2 * 1024 * 1024:
                raise forms.ValidationError(_('Profile picture must be under 2MB.'))
        return picture


# ─────────────────────────────────────────────
# Custom Password Change Form
# ─────────────────────────────────────────────
class CustomPasswordChangeForm(PasswordChangeForm):
    """Tailwind-styled password change form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': _LIGHT})
        self.fields['old_password'].widget.attrs['placeholder'] = 'Current password'
        self.fields['new_password1'].widget.attrs['placeholder'] = 'New password (min 8 chars)'
        self.fields['new_password2'].widget.attrs['placeholder'] = 'Repeat new password'


# ─────────────────────────────────────────────
# Password Reset Forms
# ─────────────────────────────────────────────
class PasswordResetRequestForm(forms.Form):
    """Form to request a password reset via email."""

    email = forms.EmailField(
        label=_('Your Registered Email'),
        widget=forms.EmailInput(attrs={
            'class': _DARK,
            'placeholder': 'you@company.com',
            'id': 'id_reset_email',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        # Don't reveal whether email exists — just return it
        return email


class SetNewPasswordForm(SetPasswordForm):
    """Form for setting a new password from reset link."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': _DARK,
            'placeholder': 'New password',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': _DARK,
            'placeholder': 'Confirm new password',
        })

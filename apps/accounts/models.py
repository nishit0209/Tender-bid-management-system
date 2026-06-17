"""
CustomUser Model — Accounts App
Enterprise Tender & Bid Management System

Extends AbstractUser to add role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


# ─────────────────────────────────────────────
# Abstract Base Model (shared timestamps)
# ─────────────────────────────────────────────
class TimeStampedModel(models.Model):
    """Abstract base model that adds created_at and updated_at to every model."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ─────────────────────────────────────────────
# Role Choices
# ─────────────────────────────────────────────
class UserRole(models.TextChoices):
    ADMIN              = 'admin',              _('Administrator')
    PROCUREMENT_OFFICER = 'procurement_officer', _('Procurement Officer')
    MANAGER            = 'manager',            _('Manager')
    VENDOR             = 'vendor',             _('Vendor')


# ─────────────────────────────────────────────
# Custom User Manager
# ─────────────────────────────────────────────
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Manager that uses email as the unique identifier instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────
# CustomUser Model
# ─────────────────────────────────────────────
def user_profile_upload_path(instance, filename):
    """Upload profile pictures to users/<id>/profile/<filename>"""
    ext = filename.split('.')[-1]
    return f'users/{instance.id}/profile/avatar.{ext}'


class CustomUser(AbstractUser, TimeStampedModel):
    """
    Extended User model with role-based access control.
    Uses email as the primary login identifier.
    """

    # Override username to be optional (email is primary)
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
    )

    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    # Role-Based Access Control
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.VENDOR,
        db_index=True,
    )

    # Profile Information
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    profile_picture = models.ImageField(
        upload_to=user_profile_upload_path,
        blank=True,
        null=True,
    )

    # Verification
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # Login tracking
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)

    # Password reset token
    password_reset_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token_expiry = models.DateTimeField(blank=True, null=True)

    # Password management
    last_password_change = models.DateTimeField(blank=True, null=True, verbose_name=_('Last Password Change'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active', 'role']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email}) [{self.get_role_display()}]"

    # ── Role Check Properties ──────────────────
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_procurement_officer(self):
        return self.role == UserRole.PROCUREMENT_OFFICER

    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER

    @property
    def is_vendor_user(self):
        return self.role == UserRole.VENDOR

    @property
    def is_staff_user(self):
        """Returns True for Admin, Procurement Officer, or Manager."""
        return self.role in [UserRole.ADMIN, UserRole.PROCUREMENT_OFFICER, UserRole.MANAGER]

    # ── Display Helpers ────────────────────────
    @property
    def full_name(self):
        return self.get_full_name() or self.email

    @property
    def initials(self):
        name = self.get_full_name()
        if name:
            parts = name.split()
            return ''.join(p[0].upper() for p in parts[:2])
        return self.email[0].upper()

    def get_dashboard_url(self):
        """Returns the appropriate dashboard URL based on role."""
        from django.urls import reverse
        role_dashboard_map = {
            UserRole.ADMIN:              'dashboard:admin',
            UserRole.PROCUREMENT_OFFICER: 'dashboard:procurement',
            UserRole.MANAGER:             'dashboard:manager',
            UserRole.VENDOR:              'dashboard:vendor',
        }
        return reverse(role_dashboard_map.get(self.role, 'dashboard:index'))

    def save(self, *args, **kwargs):
        # Auto-set username from email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# System Log (Audit) Model
# ─────────────────────────────────────────────
class SystemLogAction(models.TextChoices):
    LOGIN = 'login', _('Login')
    LOGOUT = 'logout', _('Logout')
    FAILED_LOGIN = 'failed_login', _('Failed Login')


class SystemLog(TimeStampedModel):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='system_logs'
    )
    email = models.CharField(max_length=255, blank=True, null=True, help_text=_("Stored in case user gets deleted or for failed logins"))
    action = models.CharField(max_length=20, choices=SystemLogAction.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('System Log')
        verbose_name_plural = _('System Logs')
        ordering = ['-created_at']

    def __str__(self):
        actor = self.user.email if self.user else self.email
        return f"{self.get_action_display()} by {actor} at {self.created_at}"

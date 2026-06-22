"""
Views — Accounts App
Phase 2: Authentication & User Roles

Includes:
- Login / Logout
- Vendor Registration
- Profile Management
- Password Change / Reset
- Role-based dashboard routing
- RBAC decorators and mixins
"""

from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .models import UserRole
from .forms import (
    LoginForm, VendorRegistrationForm, StaffRegistrationForm,
    ProfileEditForm, CustomPasswordChangeForm,
    PasswordResetRequestForm, SetNewPasswordForm,
)

User = get_user_model()

# ─────────────────────────────────────────────
# RBAC Mixins (Role-Based Access Control)
# ─────────────────────────────────────────────

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only admins can access this view."""
    def test_func(self):
        return self.request.user.is_admin

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:index')


class ProcurementRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Procurement officers and admins can access this view."""
    def test_func(self):
        return self.request.user.role in [UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN]

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Procurement Officer privileges required.')
        return redirect('dashboard:index')


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Managers and admins can access this view."""
    def test_func(self):
        return self.request.user.role in [UserRole.MANAGER, UserRole.ADMIN]

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Manager privileges required.')
        return redirect('dashboard:index')


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Admin, Procurement Officer, or Manager required."""
    def test_func(self):
        return self.request.user.is_staff_user

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Staff privileges required.')
        return redirect('dashboard:index')


class VendorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only vendor users can access this view."""
    def test_func(self):
        return self.request.user.is_vendor_user

    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Vendor account required.')
        return redirect('dashboard:index')


# ─────────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────────
def role_required(*roles):
    """Decorator: restrict view to specified roles."""
    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:index')
        return wrapped_view
    return decorator


# ─────────────────────────────────────────────
# Authentication Views
# ─────────────────────────────────────────────
class LoginView(View):
    """Email + password login with remember-me support."""
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        email = request.POST.get('username', '')
        user_obj = None
        
        # Check lockout BEFORE form validation
        try:
            user_obj = User.objects.get(email=email)
            if user_obj.account_locked_until:
                if user_obj.account_locked_until > timezone.now():
                    lock_mins = int((user_obj.account_locked_until - timezone.now()).total_seconds() / 60)
                    messages.error(request, f'Account locked for {lock_mins} minutes due to multiple failed attempts. Use the Forgot Password link below if needed.')
                    return render(request, self.template_name, {'form': LoginForm(request.POST)})
                else:
                    # Lock expired, reset
                    user_obj.failed_login_attempts = 0
                    user_obj.account_locked_until = None
                    user_obj.save(update_fields=['failed_login_attempts', 'account_locked_until'])
        except User.DoesNotExist:
            pass

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Handle remember-me
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(28800)

            # Track login IP and reset attempts
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
                 or request.META.get('REMOTE_ADDR', '')
            user.last_login_ip = ip or None
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.save(update_fields=['last_login_ip', 'failed_login_attempts', 'account_locked_until'])

            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            next_url = request.GET.get('next', user.get_dashboard_url())
            return redirect(next_url)

        # Track failed attempts for existing user
        if user_obj:
            user_obj.failed_login_attempts += 1
            if user_obj.failed_login_attempts >= 5:
                user_obj.account_locked_until = timezone.now() + timezone.timedelta(minutes=10)
                user_obj.save(update_fields=['failed_login_attempts', 'account_locked_until'])
                messages.error(request, 'Account locked for 10 minutes due to 5 failed attempts. Use the Forgot Password link below.')
            else:
                user_obj.save(update_fields=['failed_login_attempts'])
                rem = 5 - user_obj.failed_login_attempts
                messages.error(request, f'Invalid email or password. {rem} attempts remaining.')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
            
        return render(request, self.template_name, {'form': form})


def login_view(request):
    return LoginView.as_view()(request)


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            messages.info(request, f'You have been logged out. Goodbye, {request.user.first_name or request.user.email}!')
            logout(request)
        return redirect('accounts:login')


def logout_view(request):
    return LogoutView.as_view()(request)


# ─────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────
class VendorRegisterView(View):
    """Public vendor self-registration."""
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        form = VendorRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = VendorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(
                request,
                'Account created successfully! Please complete your vendor profile to get started.'
            )
            return redirect('vendors:create')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'form': form})


def register_view(request):
    return VendorRegisterView.as_view()(request)


# ─────────────────────────────────────────────
# Profile Management
# ─────────────────────────────────────────────
class ProfileView(LoginRequiredMixin, View):
    """View and edit user profile."""
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = ProfileEditForm(instance=request.user)
        return render(request, self.template_name, {
            'form': form,
            'user_obj': request.user,
        })

    def post(self, request):
        form = ProfileEditForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form,
            'user_obj': request.user,
        })


def profile_view(request):
    return ProfileView.as_view()(request)


# ─────────────────────────────────────────────
# Password Management
# ─────────────────────────────────────────────
class ChangePasswordView(LoginRequiredMixin, View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        form = CustomPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            user.last_password_change = timezone.now()
            user.save(update_fields=['last_password_change'])
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:profile')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'form': form})


def change_password_view(request):
    return ChangePasswordView.as_view()(request)


class ForgotPasswordView(View):
    template_name = 'accounts/forgot_password.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=True)
                # Generate reset token
                import uuid
                user.password_reset_token = uuid.uuid4()
                user.password_reset_token_expiry = timezone.now() + timezone.timedelta(hours=2)
                user.save(update_fields=['password_reset_token', 'password_reset_token_expiry'])

                reset_link = request.build_absolute_uri(
                    f'/accounts/reset-password/{user.password_reset_token}/'
                )
                send_mail(
                    subject='Reset Your TenderBMS Password',
                    message=f'Click the link to reset your password:\n{reset_link}\n\nThis link expires in 2 hours.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except User.DoesNotExist:
                pass  # Don't reveal whether email exists

        if settings.DEBUG and 'reset_link' in locals():
            # In development, redirect directly to the reset link for convenience
            messages.success(request, 'Development Mode: Redirected directly to the reset link.')
            return redirect(reset_link)
        else:
            messages.success(
                request,
                'If that email is registered, you will receive a password reset link shortly.'
            )
        return redirect('accounts:login')


def forgot_password_view(request):
    return ForgotPasswordView.as_view()(request)


class ResetPasswordView(View):
    template_name = 'accounts/reset_password.html'

    def _get_user(self, token):
        try:
            import uuid
            user = User.objects.get(password_reset_token=uuid.UUID(str(token)))
            if user.password_reset_token_expiry and user.password_reset_token_expiry >= timezone.now():
                return user
        except (User.DoesNotExist, ValueError):
            pass
        return None

    def get(self, request, token):
        user = self._get_user(token)
        if not user:
            messages.error(request, 'This reset link is invalid or has expired.')
            return redirect('accounts:forgot_password')
        form = SetNewPasswordForm(user=user)
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        user = self._get_user(token)
        if not user:
            messages.error(request, 'This reset link is invalid or has expired.')
            return redirect('accounts:forgot_password')
        form = SetNewPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            import uuid
            user.password_reset_token = uuid.uuid4()
            user.password_reset_token_expiry = None
            user.last_password_change = timezone.now()
            user.save(update_fields=['password_reset_token', 'password_reset_token_expiry', 'last_password_change'])
            messages.success(request, 'Your password has been successfully reset. You can now login.')
            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form, 'token': token})


def reset_password_view(request, token):
    return ResetPasswordView.as_view()(request, token=token)


# ─────────────────────────────────────────────
# Dashboard Routing
# ─────────────────────────────────────────────
def index(request):
    """Public Landing Page. Shows features, links to Login/Signup."""
    return render(request, 'landing.html')

@login_required
def dashboard_router(request):
    """Route users to their role-specific dashboard."""
    return redirect(request.user.get_dashboard_url())


@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect(request.user.get_dashboard_url())
    from apps.vendors.models import Vendor, VendorStatus
    from apps.tenders.models import Tender, TenderStatus
    from apps.bids.models import Bid
    from apps.purchase_orders.models import PurchaseOrder, POStatus
    from apps.notifications.models import Notification

    context = {
        'page_title': 'Admin Dashboard',
        'total_vendors':      Vendor.objects.count(),
        'active_vendors':     Vendor.objects.approved().count(),
        'pending_vendors':    Vendor.objects.pending().count(),
        'open_tenders':       Tender.objects.open().count(),
        'total_tenders':      Tender.objects.count(),
        'total_bids':         Bid.objects.count(),
        'pending_pos':        PurchaseOrder.objects.pending().count(),
        'total_pos':          PurchaseOrder.objects.count(),
        'recent_vendors':     Vendor.objects.order_by('-created_at')[:5],
        'recent_tenders':     Tender.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
def procurement_dashboard(request):
    if not request.user.role in [UserRole.PROCUREMENT_OFFICER, UserRole.ADMIN]:
        return redirect(request.user.get_dashboard_url())
    from apps.vendors.models import Vendor, VendorStatus
    from apps.tenders.models import Tender, TenderStatus
    from apps.bids.models import Bid

    context = {
        'page_title': 'Procurement Dashboard',
        'pending_vendor_verifications': Vendor.objects.pending().count(),
        'verified_vendors':             Vendor.objects.verified().count(),
        'active_tenders':               Tender.objects.open().count(),
        'draft_tenders':                Tender.objects.draft().count(),
        'pending_approval_tenders':     Tender.objects.pending_approval().count(),
        'bids_under_review':            Bid.objects.under_review().count(),
        'recent_vendors':               Vendor.objects.pending().order_by('-created_at')[:5],
        'recent_tenders':               Tender.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/procurement.html', context)


@login_required
def manager_dashboard(request):
    if not request.user.role in [UserRole.MANAGER, UserRole.ADMIN]:
        return redirect(request.user.get_dashboard_url())
    from apps.vendors.models import Vendor, VendorStatus
    from apps.tenders.models import Tender, TenderStatus
    from apps.evaluations.models import Evaluation, EvaluationStatus
    from apps.purchase_orders.models import PurchaseOrder, POStatus

    context = {
        'page_title': 'Manager Dashboard',
        'vendors_awaiting_approval':   Vendor.objects.verified().count(),
        'tenders_awaiting_approval':   Tender.objects.pending_approval().count(),
        'evaluations_for_approval':    Evaluation.objects.pending_approval().count(),
        'pos_awaiting_approval':       PurchaseOrder.objects.pending().count(),
        'recent_vendors':              Vendor.objects.verified().order_by('-created_at')[:5],
        'recent_tenders':              Tender.objects.pending_approval().order_by('-created_at')[:5],
        'recent_evaluations':          Evaluation.objects.pending_approval().order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/manager.html', context)


@login_required
def vendor_dashboard(request):
    if not request.user.is_vendor_user:
        return redirect(request.user.get_dashboard_url())
    from apps.tenders.models import Tender, TenderStatus
    from apps.bids.models import Bid

    vendor = None
    try:
        vendor = request.user.vendor_profile
    except Exception:
        vendor = None

    if vendor is not None:
        my_bids = list(Bid.objects.by_vendor(vendor).order_by('-submitted_at')[:5])
        my_bids_count = Bid.objects.by_vendor(vendor).count()
    else:
        my_bids = []
        my_bids_count = 0

    context = {
        'page_title': 'Vendor Dashboard',
        'vendor': vendor,
        'has_profile': vendor is not None,
        'open_tenders': Tender.objects.active().count(),
        'my_bids': my_bids,
        'my_bids_count': my_bids_count,
        'active_tenders': list(Tender.objects.active().order_by('-closing_date')[:5]),
    }
    return render(request, 'dashboard/vendor.html', context)


# ─────────────────────────────────────────────
# Admin: User Management & System Logs
# ─────────────────────────────────────────────
@login_required
def system_logs_view(request):
    """Admin-only: View system logs (login/logout)."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:index')
    
    from .models import SystemLog
    
    logs_list = SystemLog.objects.select_related('user').all().order_by('-created_at')
    
    # Filter
    action = request.GET.get('action')
    q = request.GET.get('q', '').strip()
    
    if action:
        logs_list = logs_list.filter(action=action)
    if q:
        logs_list = logs_list.filter(
            Q(email__icontains=q) | 
            Q(user__email__icontains=q) | 
            Q(ip_address__icontains=q)
        )

    paginator = Paginator(logs_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'System Logs',
        'logs': page_obj,
        'q': q,
        'action': action,
    }
    return render(request, 'accounts/system_logs.html', context)


@login_required
def user_management_list(request):
    """Admin-only: List all users with search, filter, and actions."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied. Administrator privileges required.')
        return redirect('dashboard:index')

    users = User.objects.all().order_by('-date_joined')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        users = users.filter(
            models.Q(first_name__icontains=q) |
            models.Q(last_name__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(phone__icontains=q)
        )

    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    # Stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    role_counts = {
        'admin': User.objects.filter(role=UserRole.ADMIN).count(),
        'procurement': User.objects.filter(role=UserRole.PROCUREMENT_OFFICER).count(),
        'manager': User.objects.filter(role=UserRole.MANAGER).count(),
        'vendor': User.objects.filter(role=UserRole.VENDOR).count(),
    }

    context = {
        'page_title': 'User Management',
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'role_counts': role_counts,
        'q': q,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': UserRole.choices,
    }
    return render(request, 'accounts/user_management.html', context)


@login_required
def user_edit(request, pk):
    """Admin-only: Edit a user's role, status, and basic details."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # Prevent admin from deactivating themselves
        if user_obj == request.user and request.POST.get('is_active') != 'on':
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('accounts:user_edit', pk=pk)

        user_obj.first_name = request.POST.get('first_name', '').strip()
        user_obj.last_name = request.POST.get('last_name', '').strip()
        user_obj.phone = request.POST.get('phone', '').strip() or None
        user_obj.department = request.POST.get('department', '').strip() or None
        user_obj.designation = request.POST.get('designation', '').strip() or None

        new_role = request.POST.get('role', user_obj.role)
        if new_role in dict(UserRole.choices):
            # Prevent admin from demoting themselves
            if user_obj == request.user and new_role != UserRole.ADMIN:
                messages.error(request, 'You cannot change your own admin role.')
                return redirect('accounts:user_edit', pk=pk)
            user_obj.role = new_role

        user_obj.is_active = request.POST.get('is_active') == 'on'
        user_obj.is_verified = request.POST.get('is_verified') == 'on'
        user_obj.phone_verified = request.POST.get('phone_verified') == 'on'

        # Admin Password Reset Logic
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            # Restriction: In production (DEBUG=False), admins cannot change Vendor passwords
            if not settings.DEBUG and user_obj.role == UserRole.VENDOR:
                messages.error(request, 'In live environments, you cannot change a Vendor password.')
            else:
                user_obj.set_password(new_password)
                user_obj.last_password_change = timezone.now()
                messages.info(request, f'Password for {user_obj.email} was successfully reset.')

        user_obj.save()
        messages.success(request, f'User "{user_obj.email}" updated successfully.')
        return redirect('accounts:user_management')

    context = {
        'page_title': f'Edit User: {user_obj.email}',
        'user_obj': user_obj,
        'roles': UserRole.choices,
    }
    return render(request, 'accounts/user_edit.html', context)


@login_required
def user_toggle_active(request, pk):
    """Admin-only: Toggle user active/inactive (suspend/unsuspend)."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    if request.method != 'POST':
        return redirect('accounts:user_management')

    user_obj = get_object_or_404(User, pk=pk)

    if user_obj == request.user:
        messages.error(request, 'You cannot suspend your own account.')
        return redirect('accounts:user_management')

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])

    action = 'activated' if user_obj.is_active else 'suspended'
    messages.success(request, f'User "{user_obj.email}" has been {action}.')
    return redirect('accounts:user_management')


@login_required
def user_delete(request, pk):
    """Admin-only: Delete a user account."""
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:index')

    if request.method != 'POST':
        return redirect('accounts:user_management')

    user_obj = get_object_or_404(User, pk=pk)

    if user_obj == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_management')

    if user_obj.is_superuser:
        messages.error(request, 'Cannot delete a superuser account.')
        return redirect('accounts:user_management')

    from django.db.models.deletion import ProtectedError

    email = user_obj.email
    try:
        user_obj.delete()
        messages.success(request, f'User "{email}" has been permanently deleted.')
    except ProtectedError:
        messages.error(
            request, 
            f'Cannot delete user "{email}" because they have a Vendor profile or other linked records. '
            'Please delete their Vendor profile first, or simply Suspend their account instead.'
        )
        
    return redirect('accounts:user_management')


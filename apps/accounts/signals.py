from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone
from .models import SystemLog, SystemLogAction, UserRole

# Allauth signals
# pyrefly: ignore [missing-import]
from allauth.account.signals import user_signed_up

def get_client_ip(request):
    """Utility to get client IP address from request."""    
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful logins."""
    SystemLog.objects.create(
        user=user,
        email=user.email,
        action=SystemLogAction.LOGIN,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )
    # Also update last_login_ip
    user.last_login_ip = get_client_ip(request)
    user.failed_login_attempts = 0
    user.save(update_fields=['last_login_ip', 'failed_login_attempts'])

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log logouts."""
    if user:
        SystemLog.objects.create(
            user=user,
            email=user.email,
            action=SystemLogAction.LOGOUT,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    email = credentials.get('email', '') or credentials.get('username', '')
    SystemLog.objects.create(
        email=email,
        action=SystemLogAction.FAILED_LOGIN,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )

@receiver(user_signed_up)
def allauth_user_signed_up(request, user, **kwargs):
    """
    Handle Google / third-party signups.
    Assign Vendor role, create Vendor profile if necessary, and send Notification.
    """
    from apps.vendors.models import Vendor
    from apps.notifications.models import Notification
    from .models import CustomUser

    # 1. Ensure user is a Vendor
    user.role = UserRole.VENDOR
    user.is_verified = True  # We trust Google email
    user.email_verified = True
    user.save(update_fields=['role', 'is_verified', 'email_verified'])

    # 2. Create Vendor profile (if doesn't exist)
    company_name = user.get_full_name() or user.email.split('@')[0]
    vendor, created = Vendor.objects.get_or_create(
        user=user,
        defaults={
            'company_name': f"{company_name}'s Company",
            'contact_email': user.email,
        }
    )

    # 3. Create Notifications for Staff
    if created:
        staff_users = CustomUser.objects.filter(role__in=[UserRole.ADMIN, UserRole.MANAGER, UserRole.PROCUREMENT_OFFICER], is_active=True)
        notifications = []
        for staff in staff_users:
            notifications.append(
                Notification(
                    recipient=staff,
                    title='New Vendor Registration (Google)',
                    message=f'Vendor {vendor.company_name} ({user.email}) has registered via Google and is pending review.',
                    link=f'/vendors/{vendor.id}/',
                )
            )
        Notification.objects.bulk_create(notifications)

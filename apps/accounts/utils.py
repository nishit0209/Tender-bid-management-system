from .models import SystemLog, SystemLogAction

def log_activity(user, action, description=None, request=None):
    """
    Helper function to log system activities.
    """
    ip = None
    user_agent = None
    if request:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    SystemLog.objects.create(
        user=user,
        email=user.email if user else None,
        action=action,
        description=description,
        ip_address=ip,
        user_agent=user_agent
    )

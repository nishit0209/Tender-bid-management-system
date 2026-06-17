"""
Context Processor — Notifications App
Injects unread notification count into every template context.
"""


def notifications_processor(request):
    """
    Makes `unread_notifications_count` and `recent_notifications`
    available in all templates for authenticated users.
    """
    context = {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }

    if request.user.is_authenticated:
        from .models import Notification
        try:
            unread_qs = Notification.objects.unread_for_user(request.user)
            context['unread_notifications_count'] = unread_qs.count()
            context['recent_notifications'] = (
                Notification.objects.recent_for_user(request.user, limit=5)
            )
        except Exception:
            pass  # Graceful degradation if DB not ready

    return context

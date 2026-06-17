"""
Notifications App — Views
Enterprise Tender & Bid Management System
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from .models import Notification


@login_required
def notification_list(request):
    """List all notifications for the current user."""
    notifications = Notification.objects.for_user(request.user)
    return render(request, 'notifications/list.html', {
        'page_title': 'Notifications',
        'recent_notifications': notifications,
    })


@login_required
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    Notification.objects.mark_all_read(request.user)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')

@login_required
def read_and_redirect(request, pk):
    from django.shortcuts import get_object_or_404
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.mark_as_read()
    if notif.action_url:
        return redirect(notif.action_url)
    return redirect('notifications:list')

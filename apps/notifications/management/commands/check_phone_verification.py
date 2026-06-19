from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import Notification, NotificationType, NotificationPriority, create_notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks for users with missing or unverified phone numbers and sends them a notification.'

    def handle(self, *args, **options):
        # Find all active users whose phone is not verified or is empty
        # Exclude superusers to avoid spamming the admin
        unverified_users = User.objects.filter(
            is_active=True,
            is_superuser=False
        ).exclude(phone_verified=True)

        sent_count = 0

        # Define how often we should remind them (e.g., every 7 days)
        reminder_interval = timedelta(days=7)
        now = timezone.now()

        for user in unverified_users:
            # Check if we already sent them a phone verification notification recently
            recent_notification = Notification.objects.filter(
                recipient=user,
                notification_type=NotificationType.SYSTEM_ALERT,
                title__icontains='Mobile Number',
                created_at__gte=now - reminder_interval
            ).exists()

            if not recent_notification:
                # Send the notification
                create_notification(
                    recipient=user,
                    notification_type=NotificationType.SYSTEM_ALERT,
                    title='Mobile Number Verification Required',
                    message='Please enter and verify your mobile number to participate in bid tenders. Update it in your Profile.',
                    priority=NotificationPriority.HIGH,
                    action_url='/accounts/profile/',  # URL to the profile edit page
                )
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f'Sent notification to {user.email}'))

        self.stdout.write(self.style.SUCCESS(f'Finished running checks. Total notifications sent: {sent_count}'))

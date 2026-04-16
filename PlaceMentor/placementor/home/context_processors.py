from .models import Notification, StudentProfile


def notifications_processor(request):
    """
    Global context processor that injects unread notifications count
    into every template that extends base.html, preventing VariableDoesNotExist
    errors on pages like about, contact, etc.
    """
    notifications = []

    if request.user.is_authenticated:
        try:
            profile = StudentProfile.objects.get(user=request.user)
            notifications = Notification.objects.filter(
                student=profile, is_read=False
            ).order_by('-created_at')[:10]
        except StudentProfile.DoesNotExist:
            pass

    return {'notifications': notifications}

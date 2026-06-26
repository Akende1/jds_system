from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import PortalNotification


@login_required
def notifications_view(request):
	"""List portal notifications and allow marking them as read."""
	notifications_qs = PortalNotification.objects.filter(user=request.user).order_by('-created_at')
	if request.method == 'POST':
		notification_id = request.POST.get('notification_id')
		notification = get_object_or_404(PortalNotification, pk=notification_id, user=request.user)
		notification.is_read = True
		notification.read_at = notification.read_at or notification.created_at
		notification.save(update_fields=['is_read', 'read_at'])
		return redirect('frontend:notifications')

	unread_count = notifications_qs.filter(is_read=False).count()
	notifications = notifications_qs[:50]
	return render(request, 'frontend/notifications.html', {
		'notifications': notifications,
		'unread_count': unread_count,
	})

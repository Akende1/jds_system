"""Frontend views for sync status and conflict resolution."""

from django.apps import apps
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from administration.decorators import role_required

from .models import DeviceRegistration, PendingSync, SyncConflict, SyncLog


def _apply_record_data(model_class, instance, data):
	for field_name, value in data.items():
		if field_name == 'id':
			continue
		try:
			model_field = model_class._meta.get_field(field_name)
		except Exception:
			continue

		if model_field.is_relation and value not in (None, ''):
			related_model = model_field.remote_field.model
			related_instance = related_model.objects.filter(pk=value).first()
			if related_instance is not None:
				setattr(instance, field_name, related_instance)
		else:
			setattr(instance, field_name, value)

	instance.save()
	return instance


def resolve_sync_conflict(conflict, resolution, notes='', resolved_by=None):
	model_label = conflict.model_name
	app_label, model_name = model_label.split('.', 1)
	model_class = apps.get_model(app_label, model_name)
	record = model_class.objects.filter(pk=conflict.record_id).first()

	if resolution == 'use_local':
		data = conflict.local_data or {}
	elif resolution == 'use_remote':
		data = conflict.remote_data or {}
	elif resolution == 'merge':
		data = dict(conflict.local_data or {})
		data.update(conflict.remote_data or {})
	else:
		data = None

	if data is not None:
		if record is None:
			record = model_class(pk=conflict.record_id)
		_apply_record_data(model_class, record, data)

	conflict.resolution = resolution
	conflict.resolution_notes = notes
	conflict.resolved_by = resolved_by
	conflict.resolved_at = timezone.now()
	conflict.save(update_fields=['resolution', 'resolution_notes', 'resolved_by', 'resolved_at'])
	return conflict


@role_required('manager', 'admin', 'head_teacher')
def sync_dashboard(request):
	"""Overview of sync activity, pending queue, and conflicts."""
	if request.method == 'POST' and request.POST.get('action') == 'resolve_conflict':
		conflict = get_object_or_404(SyncConflict, pk=request.POST.get('conflict_id'))
		resolve_sync_conflict(
			conflict=conflict,
			resolution=request.POST.get('resolution', 'pending'),
			notes=(request.POST.get('resolution_notes') or '').strip(),
			resolved_by=request.user,
		)
		messages.success(request, 'Conflict resolution saved.')
		return redirect('frontend:sync_dashboard')

	context = {
		'sync_logs': SyncLog.objects.select_related('initiated_by').order_by('-started_at')[:20],
		'pending_syncs': PendingSync.objects.select_related('user').filter(is_synced=False).order_by('-created_at')[:20],
		'conflicts': SyncConflict.objects.select_related('resolved_by').order_by('-detected_at')[:20],
		'devices': DeviceRegistration.objects.select_related('registered_by').order_by('-last_sync_at')[:20],
		'pending_count': PendingSync.objects.filter(is_synced=False).count(),
		'conflict_count': SyncConflict.objects.filter(resolution='pending').count(),
		'failed_count': SyncLog.objects.filter(status='failed').count(),
	}
	return render(request, 'frontend/sync/dashboard.html', context)


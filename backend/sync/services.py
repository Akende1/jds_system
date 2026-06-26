"""Reusable sync helpers for commands and views."""

from django.apps import apps
from django.utils import timezone

from administration.models import User

from .models import PendingSync, SyncConflict, SyncLog


def create_sync_log(sync_type, device_id, user=None, status='completed', pushed=0, pulled=0, failed=0, details=None, error_message=''):
    return SyncLog.objects.create(
        sync_type=sync_type,
        status=status,
        started_at=timezone.now(),
        completed_at=timezone.now() if status in {'completed', 'failed'} else None,
        records_pushed=pushed,
        records_pulled=pulled,
        records_failed=failed,
        initiated_by=user,
        device_id=device_id,
        details=details or {},
        error_message=error_message,
    )


def run_push_sync(device_id='local', user=None):
    pending_queryset = PendingSync.objects.filter(is_synced=False)
    if device_id:
        pending_queryset = pending_queryset.filter(device_id=device_id)

    pushed_count = 0
    for pending in pending_queryset.order_by('created_at'):
        pending.is_synced = True
        pending.synced_at = timezone.now()
        pending.sync_attempts += 1
        pending.last_error = ''
        pending.save(update_fields=['is_synced', 'synced_at', 'sync_attempts', 'last_error'])
        pushed_count += 1

    return create_sync_log(
        'push',
        device_id=device_id,
        user=user,
        pushed=pushed_count,
        details={'pending_processed': pushed_count},
    )


def run_pull_sync(device_id='local', user=None):
    unresolved_conflicts = SyncConflict.objects.filter(resolution='pending')
    if device_id:
        unresolved_conflicts = unresolved_conflicts.filter(device_id=device_id)

    conflict_count = unresolved_conflicts.count()
    return create_sync_log(
        'pull',
        device_id=device_id,
        user=user,
        pulled=0,
        failed=conflict_count,
        details={
            'message': 'Remote pull source is not connected yet. Use the conflict queue for manual reconciliation.',
            'open_conflicts': conflict_count,
        },
        status='completed',
    )


def run_full_sync(device_id='local', user=None):
    push_log = run_push_sync(device_id=device_id, user=user)
    pull_log = run_pull_sync(device_id=device_id, user=user)
    return {
        'push_log': push_log,
        'pull_log': pull_log,
    }


def apply_conflict_resolution(conflict, resolution, resolved_by=None, notes=''):
    app_label, model_name = conflict.model_name.split('.', 1)
    model_class = apps.get_model(app_label, model_name)

    if resolution == 'use_local':
        payload = dict(conflict.local_data or {})
    elif resolution == 'use_remote':
        payload = dict(conflict.remote_data or {})
    elif resolution == 'merge':
        payload = dict(conflict.local_data or {})
        payload.update(conflict.remote_data or {})
    else:
        payload = None

    if payload is not None:
        instance = model_class.objects.filter(pk=conflict.record_id).first() or model_class(pk=conflict.record_id)
        for field_name, value in payload.items():
            if field_name == 'id':
                continue
            try:
                model_field = model_class._meta.get_field(field_name)
            except Exception:
                continue

            if model_field.is_relation and value not in (None, ''):
                related_instance = model_field.remote_field.model.objects.filter(pk=value).first()
                if related_instance is not None:
                    setattr(instance, field_name, related_instance)
            else:
                setattr(instance, field_name, value)
        instance.save()

    conflict.resolution = resolution
    conflict.resolved_by = resolved_by
    conflict.resolution_notes = notes
    conflict.resolved_at = timezone.now()
    conflict.save(update_fields=['resolution', 'resolved_by', 'resolution_notes', 'resolved_at'])
    return conflict
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
import django
django.setup()
from administration.models import User
from pathlib import Path
p = Path('user_snapshot.txt')
lines = []
for u in User.objects.all().order_by('username'):
    lines.append(f'{u.username}\t{u.user_type}\tactive={u.is_active}\tstaff={u.is_staff}\tsuper={u.is_superuser}')
lines.append(f'COUNT={User.objects.count()}')
p.write_text('\n'.join(lines), encoding='utf-8')

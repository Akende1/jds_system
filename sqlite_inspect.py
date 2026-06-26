import sqlite3
import json
from pathlib import Path

db_path = Path('backend/db.sqlite3')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get user information
cur.execute('''
SELECT 
    id, username, email, user_type, is_active, is_staff, is_superuser,
    first_name, last_name
FROM administration_user
ORDER BY username
''')

users = [dict(row) for row in cur.fetchall()]

# Write to JSON for easy inspection
output = {
    'total_count': len(users),
    'users': users,
    'db_path': str(db_path.resolve())
}

with open('_users_snapshot.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

conn.close()
print('OK')

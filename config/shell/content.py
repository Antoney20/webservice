import uuid
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('SELECT rowid FROM "content" WHERE id IS NULL OR id = ""')
    rows = cursor.fetchall()
    print(f"Found {len(rows)} rows to fix...")
    
    for (rowid,) in rows:
        cursor.execute(
            'UPDATE "content" SET id = %s WHERE rowid = %s',
            [str(uuid.uuid4()), rowid]
        )

print("Done")
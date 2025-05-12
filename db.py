# db.py
import sqlite3
import time

DB_PATH = "arrosage.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            start_time INTEGER,
            duration INTEGER,
            status TEXT
        )
        ''')
        conn.commit()

def add_task(task_id, start_time, duration, status):
    with get_connection() as conn:
        conn.execute('''
        INSERT INTO tasks (id, start_time, duration, status)
        VALUES (?, ?, ?, ?)
        ''', (task_id, int(start_time), duration, status))
        conn.commit()

def get_tasks_by_status(status):
    with get_connection() as conn:
        cursor = conn.execute('''
            SELECT * FROM tasks
            WHERE status = ?
            ORDER BY start_time DESC
        ''', (status,))
        return [
            {
                "id": row[0],
                "start_time": row[1],
                "duration": row[2],
                "status": row[3]
            }
            for row in cursor.fetchall()
        ]

def update_status(task_id, new_status):
    with get_connection() as conn:
        conn.execute('''
        UPDATE tasks SET status = ?
        WHERE id = ?
        ''', (new_status, task_id))
        conn.commit()

def get_task(task_id):
    with get_connection() as conn:
        cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "start_time": row[1],
                "duration": row[2],
                "status": row[3]
            }
    return None

def get_all_tasks():
    with get_connection() as conn:
        cursor = conn.execute('SELECT * FROM tasks ORDER BY start_time DESC')
        return [
            {
                "id": row[0],
                "start_time": row[1],
                "duration": row[2],
                "status": row[3]
            }
            for row in cursor.fetchall()
        ]

def get_tasks_summary_by_day():
    with get_connection() as conn:
        cursor = conn.execute('''
            SELECT (start_time / 86400) * 86400 as day, SUM(duration)
            FROM tasks
            WHERE status = 'terminé'
            GROUP BY day
        ''')
        return {int(row[0]): int(row[1]) for row in cursor.fetchall()}

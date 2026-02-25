import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('POSTGRES_DB', 'tododb'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'password')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized!")

@app.route('/create/<title>')
def create_task(title):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO tasks (title) VALUES (%s)', (title,))
        conn.commit()
        cur.close()
        conn.close()
        return "created"
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/done/<int:task_id>')
def mark_done(task_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE tasks SET done = TRUE WHERE id = %s', (task_id,))
        conn.commit()
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return f"Task {task_id} not found", 404
            
        cur.close()
        conn.close()
        return "updated"
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/pending')
def pending_tasks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, title FROM tasks WHERE done = FALSE ORDER BY id')
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        
        if not tasks:
            return "No pending tasks"
        
        return "\n".join([f"{task[0]} {task[1]}" for task in tasks])
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/stats')
def get_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT COUNT(*) FROM tasks')
        total = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM tasks WHERE done = TRUE')
        done = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM tasks WHERE done = FALSE')
        pending = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return f"total: {total} done: {done} pending: {pending}"
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/tasks')
def all_tasks():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, title, done FROM tasks ORDER BY id')
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        
        if not tasks:
            return "No tasks yet"
        
        result = []
        for task in tasks:
            status = "✓" if task[2] else "✗"
            result.append(f"{task[0]}. {task[1]} [{status}]")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
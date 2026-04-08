import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT,
            priority TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    sort_mode = request.args.get('sort', 'default')
    conn = get_db_connection()
    
    if sort_mode == 'smart':
        # Sort by Priority (High > Medium > Low) then by Due Date (Nearest first)
        query = """
            SELECT * FROM tasks 
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                END ASC, 
                due_date ASC
        """
    else:
        # Default view: Status (Pending first) then newest added
        query = "SELECT * FROM tasks ORDER BY status DESC, id DESC"
        
    tasks = conn.execute(query).fetchall()
    
    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Completed'])
    progress = int((completed / total) * 100) if total > 0 else 0
    
    conn.close()
    return render_template('index.html', tasks=tasks, progress=progress, current_sort=sort_mode)

@app.route('/add', methods=['POST'])
def add():
    task = request.form.get('task')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority')
    if task:
        conn = get_db_connection()
        conn.execute("INSERT INTO tasks (task, status, due_date, priority) VALUES (?, ?, ?, ?)",
                    (task, 'Pending', due_date, priority))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    if request.method == 'POST':
        task = request.form.get('task')
        due_date = request.form.get('due_date')
        priority = request.form.get('priority')
        conn.execute("UPDATE tasks SET task=?, due_date=?, priority=? WHERE id=?",
                    (task, due_date, priority, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit.html', task=task)

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    conn = get_db_connection()
    task = conn.execute("SELECT status FROM tasks WHERE id=?", (id,)).fetchone()
    new_status = 'Pending' if task['status'] == 'Completed' else 'Completed'
    conn.execute("UPDATE tasks SET status=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

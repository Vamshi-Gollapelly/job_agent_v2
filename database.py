import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("JOB_AGENT_DB", "jobs.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        company     TEXT,
        location    TEXT,
        source      TEXT,
        url         TEXT UNIQUE,
        description TEXT,
        salary      TEXT,
        job_type    TEXT,
        fit_score   INTEGER DEFAULT 0,
        fit_reason  TEXT,
        key_requirements TEXT,
        matching_skills  TEXT,
        missing_skills   TEXT,
        recommendation   TEXT,
        date_found  TEXT,
        date_posted TEXT,
        status      TEXT DEFAULT 'new',
        notes       TEXT,
        is_hidden   INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS generated_docs (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id        INTEGER UNIQUE,
        tailored_resume TEXT,
        cover_letter  TEXT,
        generated_at  TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )''')

    conn.commit()
    conn.close()
    print("Database ready.")

def save_job(title, company, location, source, url, description, salary="", job_type="", date_posted=""):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT OR IGNORE INTO jobs
            (title, company, location, source, url, description, salary, job_type, date_found, date_posted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (title, company, location, source, url, description, salary, job_type,
             datetime.now().strftime("%Y-%m-%d %H:%M"), date_posted))
        conn.commit()
        job_id = c.lastrowid
        return job_id if job_id else None
    except Exception as e:
        print(f"  DB save error: {e}")
        return None
    finally:
        conn.close()

def update_analysis(job_id, score, reason, key_reqs, matching, missing, recommendation):
    conn = get_db()
    conn.execute('''UPDATE jobs SET
        fit_score=?, fit_reason=?, key_requirements=?,
        matching_skills=?, missing_skills=?, recommendation=?
        WHERE id=?''',
        (score, reason, key_reqs, matching, missing, recommendation, job_id))
    conn.commit()
    conn.close()

def save_docs(job_id, tailored_resume, cover_letter):
    conn = get_db()
    conn.execute('''INSERT OR REPLACE INTO generated_docs
        (job_id, tailored_resume, cover_letter, generated_at)
        VALUES (?, ?, ?, ?)''',
        (job_id, tailored_resume, cover_letter, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_jobs(min_score=0, source=None, status=None):
    conn = get_db()
    q = 'SELECT * FROM jobs WHERE is_hidden=0 AND fit_score>=?'
    p = [min_score]
    if source:
        q += ' AND source=?'; p.append(source)
    if status:
        q += ' AND status=?'; p.append(status)
    q += ' ORDER BY fit_score DESC, date_found DESC'
    rows = [dict(r) for r in conn.execute(q, p).fetchall()]
    conn.close()
    return rows

def get_job(job_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_docs(job_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM generated_docs WHERE job_id=?', (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_status(job_id, status, notes=""):
    conn = get_db()
    conn.execute('UPDATE jobs SET status=?, notes=? WHERE id=?', (status, notes, job_id))
    conn.commit()
    conn.close()

def hide_job(job_id):
    conn = get_db()
    conn.execute('UPDATE jobs SET is_hidden=1 WHERE id=?', (job_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_db()
    def count(q): return conn.execute(q).fetchone()[0]
    stats = {
        'total':     count("SELECT COUNT(*) FROM jobs WHERE is_hidden=0"),
        'high_fit':  count("SELECT COUNT(*) FROM jobs WHERE fit_score>=70 AND is_hidden=0"),
        'applied':   count("SELECT COUNT(*) FROM jobs WHERE status='applied'"),
        'interview': count("SELECT COUNT(*) FROM jobs WHERE status='interview'"),
        'new':       count("SELECT COUNT(*) FROM jobs WHERE status='new' AND fit_score>0"),
    }
    conn.close()
    return stats

if __name__ == "__main__":
    init_db()

# ── Settings ──────────────────────────────────────────────
def init_settings():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT)''')
    defaults = [
        ('keywords', '["software developer intern","software engineer intern","java intern","android developer intern","backend developer intern","IT intern Melbourne","technology internship","graduate intern software","penultimate intern","summer intern software"]'),
        ('job_type', 'internship'),
        ('primary_location', 'Melbourne VIC'),
        ('include_remote', 'yes'),
        ('min_score', '45'),
        ('min_doc_score', '55'),
        ('ai_model', 'gpt-4o-mini'),
        ('sources', '{"seek":true,"indeed":true,"gradconnection":true}'),
    ]
    for k, v in defaults:
        conn.execute('INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)', (k, v))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)', (key, str(value)))
    conn.commit()
    conn.close()

def clear_all_jobs():
    conn = get_db()
    conn.execute('DELETE FROM jobs')
    conn.execute('DELETE FROM generated_docs')
    conn.commit()
    conn.close()

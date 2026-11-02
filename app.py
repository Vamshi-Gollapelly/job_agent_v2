import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import (init_db, init_settings, get_jobs, get_job, get_docs,
                      update_status, hide_job, get_stats,
                      get_setting, set_setting, clear_all_jobs)
from scheduler import start_scheduler
from config import FLASK_SECRET_KEY
import threading

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

@app.route('/')
def dashboard():
    min_score = int(request.args.get('min_score', get_setting('min_score', 0)))
    source = request.args.get('source') or None
    status_filter = request.args.get('status') or None
    jobs = get_jobs(min_score=min_score, source=source, status=status_filter)
    stats = get_stats()
    return render_template('dashboard.html', jobs=jobs, stats=stats,
                           min_score=min_score, source=source or '',
                           status_filter=status_filter or '')

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = get_job(job_id)
    if not job:
        return "Job not found", 404
    docs = get_docs(job_id)
    return render_template('job_detail.html', job=job, docs=docs)

@app.route('/settings')
def settings():
    keywords = json.loads(get_setting('keywords', '[]'))
    return render_template('settings.html',
        keywords=keywords,
        job_type=get_setting('job_type', 'internship'),
        primary_location=get_setting('primary_location', 'Melbourne VIC'),
        include_remote=get_setting('include_remote', 'yes'),
        min_score=get_setting('min_score', '45'),
        min_doc_score=get_setting('min_doc_score', '55'),
        ai_model=get_setting('ai_model', 'gpt-4o-mini'),
        sources=json.loads(get_setting('sources', '{"seek":true,"indeed":true,"gradconnection":true}'))
    )

@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            set_setting(key, json.dumps(value))
        else:
            set_setting(key, value)
    return jsonify({'status': 'saved'})

@app.route('/update_status', methods=['POST'])
def update_job_status():
    job_id = int(request.form['job_id'])
    update_status(job_id, request.form['status'], request.form.get('notes', ''))
    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/hide/<int:job_id>', methods=['POST'])
def hide(job_id):
    hide_job(job_id)
    return redirect(url_for('dashboard'))

@app.route('/clear_jobs', methods=['POST'])
def clear_jobs():
    clear_all_jobs()
    return jsonify({'status': 'cleared'})

@app.route('/run_now', methods=['POST'])
def run_now():
    def run():
        from runner import run_all
        run_all()
    threading.Thread(target=run, daemon=True).start()
    return jsonify({'status': 'started'})

@app.route('/stats')
def stats():
    return jsonify(get_stats())

if __name__ == '__main__':
    init_db()
    init_settings()
    start_scheduler()
    print("\nJob Agent v2 running at http://127.0.0.1:5000\n")
    app.run(debug=False, port=5000, use_reloader=False)

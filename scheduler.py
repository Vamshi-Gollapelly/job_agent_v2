from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

scheduler = BackgroundScheduler()

def start_scheduler():
    from runner import run_all
    scheduler.add_job(
        func=run_all,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_job_scrape',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started — runs daily at 8:00 AM")
    atexit.register(lambda: scheduler.shutdown(wait=False))

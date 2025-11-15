# app/tasks/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.retriever.retriever import get_index
import atexit
import time

def start_scheduler():
    sched = BackgroundScheduler()
    # rebuild index nightly at 03:00 AM server time
    sched.add_job(lambda: get_index().build_from_db(), 'cron', hour=3, minute=0)
    sched.start()
    # ensure scheduler will shut down on process exit
    atexit.register(lambda: sched.shutdown(wait=False))
    return sched

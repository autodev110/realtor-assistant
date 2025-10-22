from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from apps.workers.tasks import ingest_all_providers, run_daily_digests

scheduler = BlockingScheduler()

scheduler.add_job(ingest_all_providers, IntervalTrigger(minutes=30), id="ingest")
scheduler.add_job(run_daily_digests, CronTrigger(hour=8, minute=0), id="daily_digests")

if __name__ == "__main__":
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

from __future__ import annotations

from prefect.client.schemas.schedules import CronSchedule

schedules1 = [
    [True, CronSchedule(cron='0 1 * * *', timezone='America/Chicago', day_or=True)],
    [False, CronSchedule(cron='0 2 * * *', timezone='America/Chicago', day_or=True)],
]

schedules2 = [
    [False, CronSchedule(cron='0 2 * * *', timezone='America/Chicago', day_or=True)],
    [True, CronSchedule(cron='0 1 * * *', timezone='America/Chicago', day_or=True)],
]

for s1 in schedules1:
    if s1 not in schedules2:
        print("not there", s1)
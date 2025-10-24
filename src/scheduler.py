from datetime import datetime, timedelta

from .timezone import BRASILIA_TZ, UTC_TZ


# Para mudar o horário padrão de publicação, altere estas constantes
DEFAULT_HOUR = 18   
DEFAULT_MINUTE = 0 


def build_publish_schedule(videos, start_date):
    schedule = []
    for i, video in enumerate(videos):
        publish_date = start_date + timedelta(days=i)
        aware_dt = datetime(
            publish_date.year,
            publish_date.month,
            publish_date.day,
            DEFAULT_HOUR,
            DEFAULT_MINUTE,
            0,
            tzinfo=BRASILIA_TZ,
        )
        dt_utc = aware_dt.astimezone(UTC_TZ)
        schedule.append({
            "id": video["id"],
            "title": video["title"],
            "publishAt": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return schedule


def apply_publish_schedule(youtube, schedule):
    for item in schedule:
        youtube.videos().update(
            part="status",
            body={
                "id": item["id"],
                "status": {"privacyStatus": "private", "publishAt": item["publishAt"]},
            },
        ).execute()

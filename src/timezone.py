from datetime import datetime
from zoneinfo import ZoneInfo


BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = ZoneInfo("UTC")


def utc_to_brasilia_datetime(publish_iso: str) -> datetime:
    dt_utc = datetime.strptime(publish_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC_TZ)
    return dt_utc.astimezone(BRASILIA_TZ)


def format_brasilia_date(publish_iso: str) -> str:
    return utc_to_brasilia_datetime(publish_iso).strftime("%d/%m/%Y")


def format_brasilia_time(publish_iso: str) -> str:
    return utc_to_brasilia_datetime(publish_iso).strftime("%H:%M")

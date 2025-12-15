from datetime import datetime
from zoneinfo import ZoneInfo


BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = ZoneInfo("UTC")


def parse_publish_at_utc(publish_iso: str):
    # Converte publishAt em string ISO para datetime em UTC seguro.
    if not publish_iso:
        return None
    cleaned = publish_iso.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(UTC_TZ)


def utc_to_brasilia_datetime(publish_iso: str) -> datetime:
    # Converte publishAt UTC para datetime no fuso de Brasília.
    dt_utc = parse_publish_at_utc(publish_iso)
    if dt_utc is None:
        raise ValueError("Invalid publishAt format")
    return dt_utc.astimezone(BRASILIA_TZ)


def format_brasilia_date(publish_iso: str) -> str:
    # Formata a data em Brasília no padrão dd/mm/aaaa.
    return utc_to_brasilia_datetime(publish_iso).strftime("%d/%m/%Y")


def format_brasilia_time(publish_iso: str) -> str:
    # Formata a hora em Brasília no padrão HH:MM.
    return utc_to_brasilia_datetime(publish_iso).strftime("%H:%M")

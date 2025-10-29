"""Utilitários de fuso horário (Brasília e UTC).

Fornece funções para converter o "publishAt" (UTC) para o fuso de Brasília
e helpers de formatação de data e hora para impressão no terminal.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = ZoneInfo("UTC")


def utc_to_brasilia_datetime(publish_iso: str) -> datetime:
    """Converte uma string ISO UTC (YYYY-MM-DDTHH:MM:SSZ) para datetime em Brasília."""
    dt_utc = datetime.strptime(publish_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC_TZ)
    return dt_utc.astimezone(BRASILIA_TZ)


def format_brasilia_date(publish_iso: str) -> str:
    """Formata a data no padrão DD/MM/YYYY no fuso de Brasília."""
    return utc_to_brasilia_datetime(publish_iso).strftime("%d/%m/%Y")


def format_brasilia_time(publish_iso: str) -> str:
    """Formata a hora no padrão HH:MM (24h) no fuso de Brasília."""
    return utc_to_brasilia_datetime(publish_iso).strftime("%H:%M")

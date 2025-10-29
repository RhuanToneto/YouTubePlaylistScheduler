"""Montagem e aplicação do agendamento de publicação.

Converte datas no fuso de Brasília para UTC (requisito da API) e
atualiza os vídeos para manter privado com "publishAt" definido.
"""

from datetime import datetime, timedelta

from .timezone import BRASILIA_TZ, UTC_TZ


# Para mudar o horário padrão de publicação, altere estas constantes
DEFAULT_HOUR = 18    # Horas
DEFAULT_MINUTE = 0   # Minutos


def build_publish_schedule(videos, start_date):
    """Gera o agendamento diário a partir de uma data inicial.

    Cada vídeo recebe um dia sequencial, no horário padrão definido
    em horário de Brasília, convertido para UTC no formato ISO 8601.

    Parâmetros:
        videos (list[dict]): itens com chaves "id" e "title".
        start_date (datetime.date): primeira data de publicação.

    Retorna:
        list[dict]: itens com "id", "title" e "publishAt" (string ISO UTC).
    """
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
        # A API exige "publishAt" em UTC
        dt_utc = aware_dt.astimezone(UTC_TZ)
        schedule.append({
            "id": video["id"],
            "title": video["title"],
            "publishAt": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return schedule


def apply_publish_schedule(youtube, schedule):
    """Aplica o agendamento na API atualizando o status de cada vídeo.

    Define o vídeo como "private" com a data/hora de publicação em
    "publishAt" (UTC), o que efetiva o agendamento no YouTube.
    """
    for item in schedule:
        youtube.videos().update(
            part="status",
            body={
                "id": item["id"],
                "status": {"privacyStatus": "private", "publishAt": item["publishAt"]},
            },
        ).execute()

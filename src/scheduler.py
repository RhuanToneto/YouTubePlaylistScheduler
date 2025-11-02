"""Montagem e aplicação do agendamento de publicação.

Converte datas no fuso de Brasília para UTC (requisito da API),
suporta pular dias já ocupados por agendamentos existentes e
atualiza os vídeos para manter privado com "publishAt" definido.
"""

from datetime import datetime, timedelta

from .timezone import BRASILIA_TZ, UTC_TZ


# Para mudar o horário padrão de publicação, altere estas constantes
DEFAULT_HOUR = 18    # Horas
DEFAULT_MINUTE = 0   # Minutos


def build_publish_schedule(videos, start_date, occupied_dates=None):
    """Gera o agendamento diário a partir de uma data inicial.

    Aloca um vídeo por dia, às ``DEFAULT_HOUR:DEFAULT_MINUTE`` no fuso de
    Brasília, convertendo para UTC no formato ISO 8601. Se ``occupied_dates``
    for informado, dias presentes nesse conjunto são pulados para evitar
    colisões com agendamentos já existentes.

    Parâmetros:
        videos (list[dict]): itens com chaves "id" e "title".
        start_date (datetime.date): primeira data de publicação.
        occupied_dates (set[datetime.date] | None): datas em Brasília já
            ocupadas por outros agendamentos (futuros).

    Retorna:
        list[dict]: itens com "id", "title" e "publishAt" (string ISO UTC).
    """
    schedule = []
    used_dates = set()
    date_cursor = start_date
    for video in videos:
        while True:
            if occupied_dates and date_cursor in occupied_dates:
                date_cursor = date_cursor + timedelta(days=1)
                continue
            if date_cursor in used_dates:
                date_cursor = date_cursor + timedelta(days=1)
                continue
            break
        publish_date = date_cursor
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
        used_dates.add(publish_date)
        date_cursor = date_cursor + timedelta(days=1)
    return schedule


def get_occupied_brasilia_dates(youtube, limit=1000):
    """Retorna as datas (Brasília) já ocupadas por vídeos agendados do canal.

    Varre a playlist de uploads do canal (``mine=True``) e inspeciona até
    ``limit`` vídeos mais recentes. Considera ocupadas as datas de vídeos com
    ``privacyStatus == "private"`` e ``publishAt`` no futuro. O retorno contém
    objetos ``datetime.date`` no fuso de Brasília.

    Parâmetros:
        youtube: cliente autenticado da YouTube Data API.
        limit (int): quantidade máxima de uploads a inspecionar (padrão 1000).

    Retorna:
        set[datetime.date]: conjunto de datas ocupadas no fuso de Brasília.
    """
    occupied = set()
    ch = youtube.channels().list(part="contentDetails", mine=True).execute()
    items = ch.get("items", [])
    if not items:
        return occupied
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = []
    token = None
    while True:
        req = youtube.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=token)
        resp = req.execute()
        for it in resp.get("items", []):
            vid = it["contentDetails"].get("videoId")
            if vid:
                ids.append(vid)
                if len(ids) >= limit:
                    break
        if len(ids) >= limit:
            break
        token = resp.get("nextPageToken")
        if not token:
            break
    now_utc = datetime.now(UTC_TZ)
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        vresp = youtube.videos().list(part="status", id=",".join(chunk)).execute()
        for it in vresp.get("items", []):
            st = it.get("status", {})
            priv = st.get("privacyStatus")
            pub_at = st.get("publishAt")
            if not pub_at:
                continue
            if priv != "private":
                continue
            try:
                dt_utc = datetime.strptime(pub_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC_TZ)
            except Exception:
                continue
            if dt_utc <= now_utc:
                continue
            dt_br = dt_utc.astimezone(BRASILIA_TZ)
            occupied.add(dt_br.date())
    return occupied


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

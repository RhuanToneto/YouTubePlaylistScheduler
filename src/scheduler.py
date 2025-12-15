from datetime import datetime, timedelta

from .timezone import BRASILIA_TZ, UTC_TZ, parse_publish_at_utc


DEFAULT_HOUR = 18
DEFAULT_MINUTE = 0


def build_publish_schedule(videos, start_date, occupied_dates=None):
    # Gera cronograma sequencial, evitando datas já ocupadas e duplicadas.
    schedule = []
    used_dates = set()
    date_cursor = start_date
    for video in videos:
        # Avança até encontrar uma data livre que não conflite com agendamentos existentes.
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
    # Coleta datas futuras com vídeos privados já agendados no canal.
    occupied = set()
    now_utc = datetime.now(UTC_TZ)
    token = None
    scanned = 0
    ids = []
    # Pagina uploads do canal até atingir o limite configurado.
    while True:
        resp = youtube.search().list(part="id", forMine=True, type="video", order="date", maxResults=50, pageToken=token).execute()
        for it in resp.get("items", []):
            vid = it.get("id", {}).get("videoId")
            if not vid:
                continue
            ids.append(vid)
            scanned += 1
            if scanned >= limit:
                break
        if scanned >= limit:
            break
        token = resp.get("nextPageToken")
        if not token:
            break
    # Analisa status/publicação em blocos de 50 para identificar agendamentos futuros.
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
            dt_utc = parse_publish_at_utc(pub_at)
            if dt_utc is None:
                continue
            if dt_utc <= now_utc:
                continue
            dt_br = dt_utc.astimezone(BRASILIA_TZ)
            occupied.add(dt_br.date())
    return occupied


def apply_publish_schedule(youtube, schedule):
    # Atualiza publishAt dos vídeos mantendo status privado.
    for item in schedule:
        youtube.videos().update(
            part="status",
            body={
                "id": item["id"],
                "status": {"privacyStatus": "private", "publishAt": item["publishAt"]},
            },
        ).execute()

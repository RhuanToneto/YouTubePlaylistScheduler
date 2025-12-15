from __future__ import annotations

from datetime import date, datetime, timedelta
import os
import random
import sys
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import auth, scheduler, timezone


def collect_channel_video_ids(service, limit: int):
    # Coleta IDs dos uploads do canal em lotes de 50 até alcançar o limite.
    ids: List[str] = []
    token = None
    scanned = 0
    # Pagina resultados de busca priorizando vídeos mais recentes.
    while True:
        resp = service.search().list(part="id", forMine=True, type="video", order="date", maxResults=50, pageToken=token).execute()
        for item in resp.get("items", []):
            vid = item.get("id", {}).get("videoId")
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
    return ids


def fetch_video_statuses(service, video_ids: List[str]):
    # Recupera snippet e status dos vídeos em blocos de 50 IDs.
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        resp = service.videos().list(part="snippet,status", id=",".join(chunk)).execute()
        for it in resp.get("items", []):
            st = it.get("status", {})
            priv = st.get("privacyStatus")
            pub_at = st.get("publishAt")
            title = it.get("snippet", {}).get("title")
            out.append({"id": it.get("id"), "title": title, "privacyStatus": priv, "publishAt": pub_at})
    return out


def build_channel_occupied_map(service, limit=1000):
    # Mapeia datas futuras ocupadas por vídeos privados agendados no canal.
    occupied_by_date: Dict[date, List[str]] = {}
    now_utc = datetime.now(timezone.UTC_TZ)
    ids = collect_channel_video_ids(service, limit)
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        vresp = service.videos().list(part="status", id=",".join(chunk)).execute()
        for it in vresp.get("items", []):
            st = it.get("status", {})
            priv = st.get("privacyStatus")
            pub_at = st.get("publishAt")
            if not pub_at:
                continue
            if priv != "private":
                continue
            dt_utc = timezone.parse_publish_at_utc(pub_at)
            if dt_utc is None:
                continue
            if dt_utc <= now_utc:
                continue
            dt_br = dt_utc.astimezone(timezone.BRASILIA_TZ)
            occupied_by_date.setdefault(dt_br.date(), []).append(it.get("id"))
    return occupied_by_date


def get_scheduled_videos(service, limit=1000, occupied=None):
    # Retorna vídeos privados agendados futuros com datas em Brasília.
    if occupied is None:
        occupied = build_channel_occupied_map(service, limit=limit)
    all_ids = [vid for vids in occupied.values() for vid in vids]
    if not all_ids:
        return []
    statuses = fetch_video_statuses(service, all_ids)
    now_utc = datetime.now(timezone.UTC_TZ)
    out = []
    for s in statuses:
        pub_at = s.get("publishAt")
        if not pub_at:
            continue
        if s.get("privacyStatus") != "private":
            continue
        dt_utc = timezone.parse_publish_at_utc(pub_at)
        if dt_utc is None:
            continue
        if dt_utc <= now_utc:
            continue
        dt_br = dt_utc.astimezone(timezone.BRASILIA_TZ)
        out.append({"id": s["id"], "title": s.get("title"), "publishAt": pub_at, "dt_br": dt_br})
    return out


def generate_deranged_assignments(scheduled: List[dict]):
    # Embaralha datas de publicação preservando horários via deslocamento circular.
    orig_dates = [v["dt_br"].date() for v in scheduled]
    if len(scheduled) <= 1:
        print("Quantidade insuficiente de vídeos para embaralhar.")
        sys.exit(0)
    start_date = min(orig_dates)
    target_dates = [start_date + timedelta(days=i) for i in range(len(scheduled))]
    offset = random.randrange(len(target_dates))
    new_dates = [target_dates[(i + offset) % len(target_dates)] for i in range(len(target_dates))]
    updates = []
    for vid, nd in zip(scheduled, new_dates):
        t = vid["dt_br"].time()
        new_br = datetime(nd.year, nd.month, nd.day, t.hour, t.minute, t.second, tzinfo=timezone.BRASILIA_TZ)
        new_utc = new_br.astimezone(timezone.UTC_TZ)
        updates.append({"id": vid["id"], "title": vid.get("title"), "publishAt": new_utc.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return updates


def save_preview_file(updates: List[dict], orig_map: Dict[str, datetime], output_path: str, total_found: int):
    # Gera arquivo de pré-visualização com antes/depois dos agendamentos.
    lines = []
    from datetime import datetime as dt
    now_local = dt.now().astimezone(timezone.BRASILIA_TZ)
    lines.append(f"HORA: {now_local.strftime('%H:%M:%S')}")
    lines.append(f"DATA: {now_local.strftime('%d/%m/%Y')}")
    lines.append("")
    lines.append(f"Total de Vídeos: {total_found}")
    min_p = None
    max_p = None
    try:
        new_dates = [timezone.utc_to_brasilia_datetime(u["publishAt"]).date() for u in updates]
        if new_dates:
            min_p = min(new_dates).strftime("%d/%m/%Y")
            max_p = max(new_dates).strftime("%d/%m/%Y")
    except Exception:
        pass
    lines.append("")
    if min_p and max_p:
        lines.append(f"Período: {min_p} - {max_p}")
    lines.append("")
    lines.append("Prévia de Embaralhamento:")
    lines.append("")
    sorted_updates = sorted(updates, key=lambda u: timezone.utc_to_brasilia_datetime(u["publishAt"]))
    for i, u in enumerate(sorted_updates, 1):
        new_br = timezone.utc_to_brasilia_datetime(u["publishAt"]) 
        old_br = orig_map.get(u['id'])
        old_str = old_br.strftime("%d/%m/%Y %H:%M") if old_br else "(unknown)"
        new_str = new_br.strftime("%d/%m/%Y %H:%M")
        title = u.get('title') or ''
        lines.append(f"{str(i).rjust(2)}) {u['id']} | {old_str} -> {new_str} | {title}")
    content = "\n".join(lines) + "\n"
    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except Exception:
        pass


def verify_applied_schedule(service, updates: List[dict]):
    # Confirma se publishAt e privacyStatus foram aplicados conforme esperado.
    statuses = fetch_video_statuses(service, [u["id"] for u in updates])
    status_map = {s["id"]: s for s in statuses}
    failures = []
    for exp in updates:
        got = status_map.get(exp["id"])
        if not got:
            failures.append((exp["id"], "não retornou na API"))
            continue
        if got.get("privacyStatus") != "private":
            failures.append((exp["id"], "privacyStatus diferente"))
            continue
        exp_dt = timezone.parse_publish_at_utc(exp["publishAt"])
        got_dt = timezone.parse_publish_at_utc(got.get("publishAt"))
        if not exp_dt or not got_dt:
            failures.append((exp["id"], "publishAt inválido"))
            continue
        if exp_dt != got_dt:
            failures.append((exp["id"], "publishAt divergente"))
    if failures:
        print("Falha ao confirmar aplicação em alguns vídeos:")
        for vid, reason in failures:
            print(f"- {vid}: {reason}")
        sys.exit(1)
    print("Verificação concluída: agendamento aplicado para todos os vídeos.")


def main():
    # Controla o fluxo de embaralhar, confirmar e aplicar novos agendamentos.
    SCAN_LIMIT = 1000
    service = auth.get_authenticated_service()
    occupied = build_channel_occupied_map(service, limit=SCAN_LIMIT)
    scheduled_videos = get_scheduled_videos(service, limit=SCAN_LIMIT, occupied=occupied)
    if not scheduled_videos:
        print("Nenhum vídeo agendado encontrado no canal para varredura.")
        sys.exit(0)
    total_found = len(scheduled_videos)
    random.shuffle(scheduled_videos)
    orig_map = {v['id']: v['dt_br'] for v in scheduled_videos}
    preview_file = os.path.join(os.path.dirname(__file__), "preview.txt")
    apply_now = False
    # Gera novas combinações até que o usuário aprove um embaralhamento.
    while True:
        updates = generate_deranged_assignments(scheduled_videos)
        if not updates:
            print("Nenhuma alteração necessária após o embaralhamento.")
            sys.exit(0)
        save_preview_file(updates, orig_map, preview_file, total_found)
        print(f"\nPreview salvo em: {preview_file}")
        while True:
            resp = input("Confirmar agendamento? [S] para Sim, [R] para Refazer, [N] para Não: ").strip().upper()
            if not resp:
                continue
            if resp in ("S", "SIM"):
                apply_now = True
                break
            if resp in ("R", "REF", "REFAZER"):
                break
            if resp in ("N", "NAO", "NÃO"):
                print("Cancelado pelo usuário.")
                sys.exit(0)
            print("Opção inválida. Digite S, R ou N.")
        if apply_now:
            break

    final = input("Digite 'CONFIRMAR' para aplicar as alterações (ou qualquer outra tecla para cancelar): ").strip().upper()
    if final != "CONFIRMAR":
        print("Cancelado pelo usuário.")
        sys.exit(0)
    scheduler.apply_publish_schedule(service, updates)
    verify_applied_schedule(service, updates)
    print("Concluído com sucesso.")


if __name__ == "__main__":
    main()

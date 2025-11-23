from __future__ import annotations

from datetime import datetime, date
import os
import random
import sys
from typing import Dict, List

# Adiciona o diretório pai ao sys.path para permitir importações locais de `src` quando executado como script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import auth, scheduler, timezone


# Busca metadados (snippet e status) para uma lista de vídeos em lotes de até 50 IDs
def fetch_video_statuses(service, video_ids: List[str]):
    out = []
    # Itera em blocos de tamanho até 50 para respeitar os limites da API
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


# Constrói um mapa de datas (Brasília) -> lista de IDs de vídeos privados agendados no futuro
def build_channel_occupied_map(service, limit=1000):
    occupied_by_date: Dict[date, List[str]] = {}
    # Obtém detalhes do canal para descobrir a playlist de uploads do canal
    ch = service.channels().list(part="contentDetails", mine=True).execute()
    items = ch.get("items", [])
    if not items:
        return occupied_by_date
    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = []
    token = None
    # Pagina os itens da playlist de uploads até atingir o limite ou até o final
    while True:
        req = service.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=50, pageToken=token)
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
    now_utc = datetime.now(timezone.UTC_TZ)
    # Para cada lote de até 50 IDs, consulta o status e coleta apenas vídeos privados com publishAt futuro
    for i in range(0, len(ids), 50):
        chunk = ids[i:i+50]
        vresp = service.videos().list(part="status", id=",".join(chunk)).execute()
        for it in vresp.get("items", []):
            st = it.get("status", {})
            priv = st.get("privacyStatus")
            pub_at = st.get("publishAt")
            # Ignora vídeos sem publishAt definido ou que não estejam privados
            if not pub_at:
                continue
            if priv != "private":
                continue
            # Converte publishAt em UTC para datetime
            try:
                dt_utc = datetime.strptime(pub_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.UTC_TZ)
            except Exception:
                continue
            # Ignora publicações já ocorridas (ou que estejam no passado em UTC)
            if dt_utc <= now_utc:
                continue
            # Converte para horário de Brasília e agrupa por data
            dt_br = dt_utc.astimezone(timezone.BRASILIA_TZ)
            occupied_by_date.setdefault(dt_br.date(), []).append(it.get("id"))
    return occupied_by_date


# Retorna a lista detalhada de vídeos agendados (id, título, publishAt e datetime em Brasília)
def get_scheduled_videos(service, limit=1000, occupied=None):
    if occupied is None:
        occupied = build_channel_occupied_map(service, limit=limit)
    # Colapsa o mapa de ocupação em uma lista de IDs para consulta em batch
    all_ids = [vid for vids in occupied.values() for vid in vids]
    if not all_ids:
        return []
    statuses = fetch_video_statuses(service, all_ids)
    now_utc = datetime.now(timezone.UTC_TZ)
    out = []
    # Filtra e converte entradas retornadas pelo serviço, preservando somente agendamentos futuros privados
    for s in statuses:
        pub_at = s.get("publishAt")
        if not pub_at or s.get("privacyStatus") != "private":
            continue
        # Faz parsing da data UTC
        try:
            dt_utc = datetime.strptime(pub_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.UTC_TZ)
        except Exception:
            continue
        # Verifica se a data de publicação está no futuro
        if dt_utc <= now_utc:
            continue
        dt_br = dt_utc.astimezone(timezone.BRASILIA_TZ)
        out.append({"id": s["id"], "title": s.get("title"), "publishAt": pub_at, "dt_br": dt_br})
    return out


# Gera uma nova atribuição (derangement) de datas garantindo que nenhum vídeo mantenha sua data original
def generate_deranged_assignments(scheduled: List[dict]):
    # Extrai a lista de datas (somente dia) a partir do datetime em Brasília de cada vídeo
    unique_days = [v["dt_br"].date() for v in scheduled]
    # Valida que não há dois vídeos programados para a mesma data
    if len(set(unique_days)) != len(scheduled):
        print("Datas duplicadas detectadas entre vídeos.")
        sys.exit(1)
    # Verifica que há pelo menos dois vídeos para embaralhar; caso contrário nada a fazer
    if len(scheduled) <= 1:
        print("Quantidade insuficiente de vídeos para embaralhar.")
        sys.exit(0)
    orig_dates = unique_days[:]
    new_dates = orig_dates[:]
    # Faz shuffle repetido até obter uma permutação em que NENHUMA data seja igual à original (derangement)
    while True:
        random.shuffle(new_dates)
        if all(new_dates[i] != orig_dates[i] for i in range(len(orig_dates))):
            break
    updates = []
    # Para cada vídeo, constrói o novo publishAt preservando a hora original e convertendo para UTC
    for vid, nd in zip(scheduled, new_dates):
        t = vid["dt_br"].time()
        new_br = datetime(nd.year, nd.month, nd.day, t.hour, t.minute, t.second, tzinfo=timezone.BRASILIA_TZ)
        new_utc = new_br.astimezone(timezone.UTC_TZ)
        updates.append({"id": vid["id"], "title": vid.get("title"), "publishAt": new_utc.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return updates


# Gera e persiste um arquivo de preview com o resumo das alterações propostas para revisão
def save_preview_file(updates: List[dict], orig_map: Dict[str, datetime], output_path: str, total_found: int):
    lines = []
    from datetime import datetime as dt
    now_local = dt.now().astimezone(timezone.BRASILIA_TZ)
    lines.append(f"HORA: {now_local.strftime('%H:%M:%S')}")
    lines.append(f"DATA: {now_local.strftime('%d/%m/%Y')}")
    lines.append("")
    lines.append(f"Total de Vídeos: {total_found}")
    # Determina período mínimo e máximo a partir do mapa original
    min_p = None
    max_p = None
    try:
        dates = [d for d in orig_map.values() if d is not None]
        if dates:
            min_p = min(dates).date().strftime("%d/%m/%Y")
            max_p = max(dates).date().strftime("%d/%m/%Y")
    except Exception:
        pass
    lines.append("")
    if min_p and max_p:
        lines.append(f"Período: {min_p} - {max_p}")
    lines.append("")
    lines.append("Prévia de Embaralhamento:")
    lines.append("")
    # Ordena as alterações por data/horário em Brasília para exibir a prévia de forma cronológica
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


# Fluxo principal do utilitário: autentica, gera embaralhamento, salva preview e aplica se confirmado
def main():
    SCAN_LIMIT = 1000
    # Autentica e obtém o cliente para chamadas na API do YouTube
    service = auth.get_authenticated_service()
    # Mapeia datas já ocupadas no canal para evitar colisões (usado apenas para coletar vídeos agendados)
    occupied = build_channel_occupied_map(service, limit=SCAN_LIMIT)
    scheduled_videos = get_scheduled_videos(service, limit=SCAN_LIMIT, occupied=occupied)
    # Caso não existam vídeos agendados, encerra o utilitário sem erro
    if not scheduled_videos:
        print("Nenhum vídeo agendado encontrado no canal para varredura.")
        sys.exit(0)
    total_found = len(scheduled_videos)
    random.shuffle(scheduled_videos)
    orig_map = {v['id']: v['dt_br'] for v in scheduled_videos}
    preview_file = os.path.join(os.path.dirname(__file__), "preview.txt")
    apply_now = False
    # Loop principal para permitir reembaralhar até o usuário concordar com o preview
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


    # Confirmação final obrigatória para aplicar as alterações no YouTube (proteção contra execuções involuntárias)
    final = input("Digite 'CONFIRMAR' para aplicar as alterações (ou qualquer outra tecla para cancelar): ").strip().upper()
    if final != "CONFIRMAR":
        print("Cancelado pelo usuário.")
        sys.exit(0)
    scheduler.apply_publish_schedule(service, updates)
    print("Concluído com sucesso.")


if __name__ == "__main__":
    main()

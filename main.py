"""Agendador de publicação para vídeos privados em uma playlist do YouTube.

Fluxo principal:
1) Autentica com a API do YouTube;
2) Solicita o ID da playlist e carrega seus vídeos;
3) Filtra os vídeos privados;
4) Verifica dias já ocupados por agendamentos do canal (até 1000 uploads recentes) e exibe um resumo quando houver;
5) Monta um agendamento diário a partir de amanhã (horário de Brasília), pulando dias ocupados;
6) Pede confirmação e aplica o agendamento via API;
7) Exibe um resumo ao final.
"""

import sys

from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

from src.auth import get_authenticated_service
from src.cli import confirm_schedule, print_summary, print_video_counts, print_occupied_overview
from src.playlist import filter_private_videos_batched, get_playlist_videos
from src.scheduler import apply_publish_schedule, build_publish_schedule, get_occupied_brasilia_dates
from src.timezone import BRASILIA_TZ


def main():
    """Executa o fluxo de coleta, filtro, verificação de dias ocupados e agendamento.

    Observações:
    - O início do agendamento é o dia seguinte à execução, 18:00 de Brasília
      (ajustável em ``src/scheduler.py``);
    - Em caso de erro 400/404 ao buscar a playlist, solicita o ID novamente;
    - Antes de propor o cronograma, verifica dias já ocupados pelos 1000 uploads
      mais recentes do canal, exibe um pequeno resumo dos dias ocupados (se houver)
      e evita colisões ao montar as datas.
    """
    try:
        youtube = get_authenticated_service()
        while True:
            playlist_id = input("\nInforme o ID da playlist privada: ").strip()
            if not playlist_id:
                print("Nenhum ID fornecido, tente novamente.")
                continue
            try:
                videos = get_playlist_videos(youtube, playlist_id)
                break
            except HttpError as e:
                status = getattr(e, "resp", None).status if getattr(e, "resp", None) else None
                if status in (400, 404):
                    print("Playlist não encontrada, verifique o ID e tente novamente.")
                continue
        private_videos = filter_private_videos_batched(youtube, videos)
        print_video_counts(len(videos), len(private_videos))
        if not private_videos:
            print("\nNenhum vídeo privado encontrado na playlist.\n")
            return
        start_date = datetime.now(BRASILIA_TZ).date() + timedelta(days=1)
        occupied = get_occupied_brasilia_dates(youtube, limit=1000)
        print_occupied_overview(occupied, start_date)
        schedule = build_publish_schedule(private_videos, start_date, occupied_dates=occupied)
        if not confirm_schedule(schedule):
            print("")
            print("Agendamento cancelado pelo usuário.\n")
            return
        apply_publish_schedule(youtube, schedule)
        print_summary(schedule)
    except KeyboardInterrupt:
        print("")
        print("\nInterrompido pelo usuário.\n")
        return
    finally:
        if sys.stdin and sys.stdin.isatty():
            input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()

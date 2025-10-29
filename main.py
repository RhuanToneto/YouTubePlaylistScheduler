"""Agendador de publicação para vídeos privados em uma playlist do YouTube.

Fluxo principal:
1) Autentica com a API do YouTube;
2) Solicita o ID da playlist e carrega seus vídeos;
3) Filtra os vídeos privados;
4) Monta um agendamento diário a partir de amanhã (horário de Brasília);
5) Pede confirmação e aplica o agendamento via API;
6) Exibe um resumo ao final.
"""

import sys

from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

from src.auth import get_authenticated_service
from src.cli import confirm_schedule, print_summary, print_video_counts
from src.playlist import filter_private_videos_batched, get_playlist_videos
from src.scheduler import apply_publish_schedule, build_publish_schedule
from src.timezone import BRASILIA_TZ


def main():
    """Executa o fluxo de coleta, filtro, agendamento e aplicação.

    Observações:
    - O início do agendamento é o dia seguinte à execução, 18:00 de Brasília
      (ajustável em src/scheduler.py);
    - Em caso de erro 400/404 ao buscar a playlist, solicita o ID novamente.
    """
    try:
        # 1) Autenticação
        youtube = get_authenticated_service()
        while True:
            # 2) Leitura do ID da playlist e busca dos vídeos
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
        # 3) Filtra vídeos privados
        private_videos = filter_private_videos_batched(youtube, videos)
        print_video_counts(len(videos), len(private_videos))
        if not private_videos:
            print("\nNenhum vídeo privado encontrado na playlist.\n")
            return
        # 4) Monta o agendamento a partir de amanhã, em horário de Brasília
        start_date = datetime.now(BRASILIA_TZ).date() + timedelta(days=1)
        schedule = build_publish_schedule(private_videos, start_date)
        # 5) Confirmação do usuário antes de aplicar
        if not confirm_schedule(schedule):
            print("")
            print("Agendamento cancelado pelo usuário.\n")
            return
        # 6) Aplica e exibe resumo
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

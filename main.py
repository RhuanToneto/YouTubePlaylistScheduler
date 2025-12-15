import sys

from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

from src.auth import get_authenticated_service
from src.cli import confirm_schedule, print_summary, print_video_counts, print_occupied_overview
from src.playlist import filter_private_videos_batched, get_playlist_videos
from src.scheduler import apply_publish_schedule, build_publish_schedule, get_occupied_brasilia_dates
from src.timezone import BRASILIA_TZ


def main():
    # Coordena autenticação, coleta de playlist e agendamento dos vídeos privados.
    try:
        youtube = get_authenticated_service()
        # Solicita repetidamente um ID de playlist válido antes de prosseguir.
        while True:
            playlist_id = input("\nInforme o ID da playlist privada: ").strip()
            if not playlist_id:
                print("Nenhum ID fornecido, tente novamente.")
                continue
            try:
                videos = get_playlist_videos(youtube, playlist_id)
                break
            except HttpError as e:
                resp = getattr(e, "resp", None)
                status = getattr(resp, "status", None)
                if status in (400, 404):
                    print("Playlist não encontrada, verifique o ID e tente novamente.")
                continue
        # Filtra apenas vídeos privados para agendamento.
        private_videos = filter_private_videos_batched(youtube, videos)
        print_video_counts(len(videos), len(private_videos))
        if not private_videos:
            print("\nNenhum vídeo privado encontrado na playlist.\n")
            return
        # Define início do cronograma para o dia seguinte no fuso de Brasília.
        start_date = datetime.now(BRASILIA_TZ).date() + timedelta(days=1)
        # Identifica datas já ocupadas por agendamentos existentes.
        occupied = get_occupied_brasilia_dates(youtube, limit=1000)
        print_occupied_overview(occupied, start_date)
        # Monta cronograma diário respeitando ocupações e horário padrão.
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

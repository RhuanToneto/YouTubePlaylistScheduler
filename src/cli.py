from datetime import timedelta

from .timezone import format_brasilia_date, format_brasilia_time


def print_video_counts(total_found, total_private):
    # Exibe contagem total de vídeos e quantos estão privados.
    print("\n[VÍDEOS]")
    print(f"Total: {total_found}")
    print(f"Privados: {total_private}")


def print_occupied_overview(occupied_dates, start_date):
    # Resume dias já ocupados e destaca o próximo dia livre.
    if not occupied_dates:
        return
    next_free = start_date
    # Avança até encontrar a primeira data sem ocupação.
    while next_free in occupied_dates:
        next_free = next_free + timedelta(days=1)
    print("\n[DIAS OCUPADOS DETECTADOS]")
    print(f"Total: {len(occupied_dates)}")
    ordered = sorted(occupied_dates)
    formatted = ", ".join(d.strftime('%d/%m/%Y') for d in ordered)
    print(f"Dias ocupados: {formatted}")
    print(f"Próximo dia livre: {next_free.strftime('%d/%m/%Y')}")


def confirm_schedule(schedule):
    # Solicita confirmação do cronograma proposto ao usuário.
    print("\n[AGENDAMENTO PROPOSTO]")
    for i, item in enumerate(schedule, 1):
        date_part = format_brasilia_date(item.get("publishAt"))
        time_part = format_brasilia_time(item.get("publishAt"))
        vid = item.get("id")
        title = item.get("title", "")
        print(f" {str(i).rjust(2)}) {date_part} - {time_part} - ID: {vid}")
        print(f"  {title}")
        print("")
    options_yes = {"S", "SIM"}
    options_no = {"N", "NAO", "NÃO"}
    opts_display = "[S] para Sim ou [N] para Não"
    while True:
        resp = input(f"Confirmar agendamento? {opts_display}: ").strip().upper()
        if not resp:
            print("Resposta vazia. Digite S ou N.\n")
            continue
        if resp in options_yes:
            return True
        if resp in options_no:
            return False
        print("Opção inválida. Digite S ou N.\n")


def print_summary(schedule):
    # Resume quantidade de vídeos agendados e período coberto.
    print("\n[RESUMO]")
    total = len(schedule)
    first_date = format_brasilia_date(schedule[0].get("publishAt"))
    first_time = format_brasilia_time(schedule[0].get("publishAt"))
    last_date = format_brasilia_date(schedule[-1].get("publishAt"))
    dates = set()
    for item in schedule:
        d = format_brasilia_date(item.get("publishAt"))
        dates.add(d)
    days_with_videos = len(dates)
    horario_info = f"Horário de publicação para todos os dias: {first_time}"
    print(f"Agendados: {total} vídeos em {days_with_videos} dias")
    print(f"Período: {first_date} a {last_date}")
    print(horario_info)
    print("")

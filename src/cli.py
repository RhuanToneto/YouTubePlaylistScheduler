from .timezone import format_brasilia_date, format_brasilia_time


def print_video_counts(total_found, total_private):
    print("\n[VÍDEOS]")
    print(f"Total: {total_found}")
    print(f"Privados: {total_private}")


def confirm_schedule(schedule):
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

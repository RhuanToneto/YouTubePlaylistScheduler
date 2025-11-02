"""Utilitários de interação no terminal (entrada e saída).

Responsável por exibir contagens, listar o agendamento proposto,
mostrar um resumo de dias ocupados (quando houver) e solicitar
confirmação do usuário de forma simples e direta.
"""

from datetime import timedelta

from .timezone import format_brasilia_date, format_brasilia_time


def print_video_counts(total_found, total_private):
    """Mostra quantos vídeos foram encontrados e quantos estão privados."""
    print("\n[VÍDEOS]")
    print(f"Total: {total_found}")
    print(f"Privados: {total_private}")


def print_occupied_overview(occupied_dates, start_date):
    """Exibe um resumo dos dias ocupados e o próximo dia livre.

    Mostra o total de dias futuros já ocupados por agendamentos do canal,
    lista as datas ocupadas de forma ordenada e informa o próximo dia
    livre a partir de ``start_date``. Não imprime nada caso não existam
    dias ocupados.

    Parâmetros:
        occupied_dates (set[datetime.date]): conjunto de datas ocupadas (Brasília).
        start_date (datetime.date): data inicial de referência para localizar o próximo dia livre.

    Retorna:
        None
    """
    if not occupied_dates:
        return
    next_free = start_date
    while next_free in occupied_dates:
        next_free = next_free + timedelta(days=1)
    print("\n[DIAS OCUPADOS DETECTADOS]")
    print(f"Total: {len(occupied_dates)}")
    ordered = sorted(occupied_dates)
    formatted = ", ".join(d.strftime('%d/%m/%Y') for d in ordered)
    print(f"Dias ocupados: {formatted}")
    print(f"Próximo dia livre: {next_free.strftime('%d/%m/%Y')}")


def confirm_schedule(schedule):
    """Exibe o agendamento proposto e pede confirmação ao usuário.

    Parâmetros:
        schedule (list[dict]): itens com id, título e publishAt (ISO UTC).

    Retorna:
        bool: True para confirmar, False para cancelar.
    """
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
        # Normaliza a entrada e aceita variações simples de SIM/NÃO
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
    """Mostra um resumo final do agendamento aplicado.

    Destaca quantidade total, período coberto e horário de publicação.
    """
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

"""Autenticação com a API do YouTube.

Este módulo gerencia o fluxo de OAuth 2.0 usando um arquivo de credenciais
("client_secret.json") e persiste o token de acesso em "token.json".

Em alto nível:
- Verifica a existência do client secret;
- Carrega/atualiza o token salvo (se existir);
- Abre o fluxo local de autenticação quando necessário;
- Retorna um cliente autenticado do YouTube Data API.

Observação: os escopos permitem definir e atualizar status de vídeos.
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


# Escopo mínimo para manipular status e agendamentos de vídeos
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# Pastas e arquivos esperados
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDS_DIR = os.path.join(BASE_DIR, "credentials")
CLIENT_SECRET_FILE = os.path.join(CREDS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CREDS_DIR, "token.json")


def get_authenticated_service():
    """Cria e retorna um cliente autenticado da YouTube Data API.

    Fluxo:
    1) Garante que o arquivo "client_secret.json" exista;
    2) Tenta carregar o token salvo ("token.json");
    3) Se o token estiver inválido/expirado, tenta o refresh;
    4) Se necessário, inicia o fluxo local de autenticação no navegador;
    5) Persiste o token obtido para uso futuro.

    Retorna:
        googleapiclient.discovery.Resource: cliente para chamadas da API do YouTube.
    """
    creds = None
    if not os.path.exists(CLIENT_SECRET_FILE):
        print("\nArquivo de credenciais não encontrado.")
        print("Coloque o arquivo 'client_secret.json' na pasta abaixo:")
        print(f"{os.path.dirname(CLIENT_SECRET_FILE)}\n")
        sys.exit(1)
    if os.path.exists(TOKEN_FILE):
        try:
            # Carrega o token previamente salvo
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                # Tenta renovar o token silenciosamente
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            try:
                # Abre o fluxo local de autenticação (irá abrir o navegador)
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception:
                print("")
                print("Falha ao reautenticar automaticamente.")
                print("Como corrigir:")
                print("  1) Confirme se o arquivo 'client_secret.json' existe.")
                print("  2) Exclua o arquivo 'token.json' existente e tente novamente.")
                print("  3) Se persistir, gere um novo 'client_secret.json' e substitua o existente.")
                sys.exit(1)
        try:
            # Salva/atualiza o token para reutilização futura
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception:
            print("Falha ao salvar o token no disco:")
            sys.exit(1)
    # Constrói o cliente autenticado da API do YouTube
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

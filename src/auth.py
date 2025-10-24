import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CREDS_DIR = os.path.join(BASE_DIR, "credentials")
CLIENT_SECRET_FILE = os.path.join(CREDS_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CREDS_DIR, "token.json")


def get_authenticated_service():
    creds = None
    if not os.path.exists(CLIENT_SECRET_FILE):
        print("\nArquivo de credenciais não encontrado.")
        print("Coloque o arquivo 'client_secret.json' na pasta abaixo:")
        print(f"{os.path.dirname(CLIENT_SECRET_FILE)}\n")
        sys.exit(1)
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds or not creds.valid:
            try:
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
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception:
            print("Falha ao salvar o token no disco:")
            sys.exit(1)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube

# Agendador de Playlist do YouTube

Este projeto é uma aplicação em Python (CLI) para automatizar o agendamento de vídeos privados de uma playlist do YouTube. O fluxo principal autentica via OAuth 2.0, lê os vídeos de uma playlist, filtra apenas os vídeos com status de privacidade "Privado" e propõe um cronograma de publicação a partir do dia seguinte: um vídeo por dia, às 18:00 (horário de Brasília), caso deseje outro horário, altere `DEFAULT_HOUR` e `DEFAULT_MINUTE` em `src/scheduler.py`. 

Antes de propor o cronograma, o sistema verifica os dias já ocupados por vídeos do canal com publicação agendada, inspecionando os 1000 uploads mais recentes. Dias ocupados são pulados automaticamente e os novos vídeos são colocados nos próximos dias livres, evitando colisões de dois vídeos no mesmo dia.

A ordem de agendamento segue exatamente a ordenação atual da playlist no YouTube (do primeiro ao último). Após sua confirmação no terminal, os vídeos têm a data de publicação agendada por meio da YouTube Data API v3. Todo o processo é feito pela linha de comando, guiando você da autenticação à confirmação do agendamento.

## Requisitos

- [Python 3.10+](https://www.python.org/downloads/)  (Recomendado)

# Configuração inicial

Baixe o arquivo .zip ou clone este repositório.

## Passo 1 — Criar um projeto

Abra o Console do Google Cloud: https://console.cloud.google.com/

1. Na barra superior do Console, clique em `Select a project`.
2. Clique em `New Project`:
	- `Project name: (Preencha)`
	- `Project ID: (Gerado automaticamente; opcional editar)`
	- `Location: No organization`
3. Clique em `Create`.

Aguarde a criação do projeto e confirme que ele está selecionado no topo do Console.

## Passo 2 — Habilitar a API do YouTube

1. Acesse `APIs & Services`.
2. Entre em `Enabled APIs & Services`.
3. Clique em `+ Enabled APIs & Services`.
4. Em `Search for APIs & Services`, procure por `YouTube Data API v3`.
5. Abra a página da API e clique em `Enable`.

## Passo 3 — Configurar o OAuth Consent Screen

1. Em `APIs & Services`, abra `OAuth Consent Screen`.
2. Na seção `Google Auth Platform` > `Overview`, clique em `Get started`.
3. `App Information`:
	- `App Name: (Preencha)`
	- `User Support Email: (E-mail da sua conta Google Cloud)`
	- Clique em `Next`.
4. `Audience`:
	- Selecione `External`.
	- Clique em `Next`.
5. `Contact Information`:
	- `Email addresses: (E-mail da sua conta Google Cloud)`
	- Clique em `Next`.
6. Clique em `Finish`.
7. Quando solicitado, marque `I agree to the Google API Services: User Data Policy.` e clique em `Continue`.
8. Confirme/avance com `Create` quando aparecer.

## Passo 4 — Criar credenciais OAuth 2.0 (Desktop app)

1. Vá em `APIs & Services` > `Credentials`.
2. Clique em `+ Create credentials` e selecione `OAuth client ID`.
3. Em `Application type`, selecione `Desktop app`.
4. Defina `Name: (Preencha)` e clique em `Create`.
5. Na janela `OAuth client created`, clique em `Download JSON` e depois em `OK`.

### Onde colocar o arquivo JSON

1. Renomeie o arquivo baixado para `client_secret.json`.
2. Mova o arquivo para a pasta: `/credentials/`.

Este script espera exatamente esse caminho e nome de arquivo (ver `src/auth.py`). Na primeira execução autenticada, o arquivo `/credentials/token.json` será criado automaticamente.

Nunca compartilhe `client_secret.json` ou `token.json` publicamente. Esses arquivos devem permanecer apenas no seu ambiente local.

## Passo 5 — Adicionar usuários de teste

1. Vá em `APIs & Services` > `OAuth Consent Screen` > `Audience` > `Test users`.
2. Clique em `+ Add users`.
3. Em `Add users`, preencha `Email: (E-mail da sua conta Google Cloud)`.
4. Clique em `Save`.

## Passo 6 — Primeira execução e autenticação

Com o `client_secret.json` no local correto:

1. Instale as dependências.
2. Execute `main.py`. A primeira execução abrirá o navegador para você escolher a conta e conceder acesso. Após concluir, o arquivo `/credentials/token.json` será salvo automaticamente.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Em seguida, siga as instruções exibidas no terminal.

Se o `client_secret.json` não estiver no caminho esperado, será exibido uma mensagem informando onde colocar o arquivo.

## Monitoramento de cotas

1. Acesse `APIs & Services` > `Library`.
2. Pesquise e abra `YouTube Data API v3`.
3. Clique em `Manage`.
4. Abra `Quotas & System Limits` para ver limites e uso.

- A YouTube Data API possui alocação diária de `10,000` unidades. O reset ocorre às 00:00 no horário do Pacífico (PT) — aproximadamente `04:00` (PDT) ou `05:00` (PST) em Brasília (BRT).

## Referências oficiais

- YouTube Data API: https://developers.google.com/youtube/v3/getting-started
- OAuth 2.0: https://developers.google.com/youtube/v3/guides/auth/installed-apps
- Quota usage: https://developers.google.com/youtube/v3/getting-started#quota
- Quota costs for API requests: https://developers.google.com/youtube/v3/determine_quota_cost

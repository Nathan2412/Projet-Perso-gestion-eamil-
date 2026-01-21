"""
Gestion des emails Gmail
"""

import os
import pickle
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_SCOPES, START_DATE_GMAIL


def get_gmail_service(token_file):
    """Connexion à l'API Gmail"""
    creds = None
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def get_gmail_message_content(service, msg_id):
    """Récupère le contenu complet d'un email Gmail"""
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

    headers = message.get('payload', {}).get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Inconnu')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

    body = ""
    payload = message.get('payload', {})

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    return {
        'subject': subject,
        'sender': sender,
        'date': date,
        'body': body,
        'id': msg_id
    }


def fetch_gmail_emails(account):
    """Récupère les emails d'un compte Gmail"""
    token_file = account["token_file"]
    account_name = account["name"]

    print(f"\n🔄 Connexion au compte Gmail [{account_name}]...")

    try:
        service = get_gmail_service(token_file)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', account_name)

        query = f"after:{START_DATE_GMAIL}"
        results = service.users().messages().list(userId='me', q=query, maxResults=200).execute()
        messages = results.get('messages', [])

        print(f"   ✅ Connecté à {email_address} - {len(messages)} emails trouvés")

        emails = []
        for msg in messages:
            email_data = get_gmail_message_content(service, msg['id'])
            email_data['account'] = account_name
            email_data['email_address'] = email_address
            emails.append(email_data)

        return emails

    except Exception as e:
        print(f"   ❌ Erreur Gmail [{account_name}]: {e}")
        return []

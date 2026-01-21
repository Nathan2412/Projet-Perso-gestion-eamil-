"""
Gestion des emails Outlook
"""

import os
import msal
import requests

from config import OUTLOOK_SCOPES, START_DATE_OUTLOOK


def get_outlook_token(token_file):
    """Obtient un token d'accès pour Microsoft Graph API"""
    CLIENT_ID = "VOTRE_CLIENT_ID"  # Depuis Azure Portal
    TENANT_ID = "common"

    cache = msal.SerializableTokenCache()
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        token_cache=cache
    )

    accounts = app.get_accounts()
    result = None

    if accounts:
        result = app.acquire_token_silent(OUTLOOK_SCOPES, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=OUTLOOK_SCOPES)
        print(flow['message'])
        result = app.acquire_token_by_device_flow(flow)

    if cache.has_state_changed:
        with open(token_file, 'w') as f:
            f.write(cache.serialize())

    return result.get('access_token')


def fetch_outlook_emails(account):
    """Récupère les emails d'un compte Outlook"""
    token_file = account["token_file"]
    account_name = account["name"]

    print(f"\n🔄 Connexion au compte Outlook [{account_name}]...")

    try:
        token = get_outlook_token(token_file)
        if not token:
            print(f"   ❌ Impossible d'obtenir le token Outlook")
            return []

        headers = {'Authorization': f'Bearer {token}'}
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {START_DATE_OUTLOOK}&$top=200"

        response = requests.get(url, headers=headers)
        data = response.json()

        emails = []
        for msg in data.get('value', []):
            emails.append({
                'subject': msg.get('subject', ''),
                'sender': msg.get('from', {}).get('emailAddress', {}).get('address', 'Inconnu'),
                'date': msg.get('receivedDateTime', ''),
                'body': msg.get('body', {}).get('content', ''),
                'id': msg.get('id', ''),
                'account': account_name,
                'email_address': 'Outlook'
            })

        print(f"   ✅ Connecté à Outlook - {len(emails)} emails trouvés")
        return emails

    except Exception as e:
        print(f"   ❌ Erreur Outlook [{account_name}]: {e}")
        return []

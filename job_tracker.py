"""
Job Tracker - Suivi automatique des emails liés à la recherche d'emploi
Supporte Gmail et Outlook
"""

import os
import sys
import pickle
import re
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import msal
import requests

# Forcer l'encodage UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Scopes pour Gmail
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Scopes pour Outlook
OUTLOOK_SCOPES = ['https://graph.microsoft.com/Mail.Read']

# Date de début de recherche
START_DATE = "2026/01/01"

# Liste des comptes à surveiller
ACCOUNTS = [
    # Comptes Gmail
    {"type": "gmail", "name": "Pro", "token_file": "token_pro.pickle"},
    {"type": "gmail", "name": "Perso", "token_file": "token_perso.pickle"},
    # Comptes Outlook - décommenter et configurer si besoin
    # {"type": "outlook", "name": "Outlook Pro", "token_file": "token_outlook.json"},
]

# ============================================================================
# FILTRES ANTI-SPAM / PROMOTIONS
# ============================================================================

# Expéditeurs à ignorer (promotions, newsletters non-emploi)
BLOCKED_SENDERS = [
    "michaelkors",
    "zara.com",
    "hm.com",
    "newsletter@",
    "promo@",
    "marketing@",
    "info@linkedin.com",
    "sony",
    "openclassrooms",
    "columbia.edu",
    "brevosend.com",
    "accounts.google.com",  # Notifications compte Google
    "etmail.sony",
]

# Mots-clés indiquant une promotion commerciale (à ignorer)
PROMO_KEYWORDS = [
    "promotion", "soldes", "réduction", "-50%", "-30%", "code promo",
    "livraison gratuite", "vente flash", "black friday", "cyber monday",
    "meilleur de la promotion", "articles sélectionnés", "shopping",
    "panier", "commande", "achat", "boutique", "enregistrez votre produit",
    "webinar", "campaign", "dons", "soutien", "formation gratuite"
]

# ============================================================================
# CATÉGORIES D'EMAILS
# ============================================================================

CATEGORIES = {
    "✅ ACCEPTÉ / SÉLECTIONNÉ": {
        "keywords": ["choisi pour le poste", "retenu pour le poste", "sélectionné pour le poste", 
                     "félicitations pour votre", "nous avons le plaisir de vous informer", 
                     "heureux de vous annoncer", "votre profil a été retenu", 
                     "convoqué pour", "invitation à rejoindre notre équipe",
                     "proposition d'embauche", "offre d'emploi acceptée", 
                     "votre candidature a été retenue"],
        "priority": 1
    },
    "❌ REFUSÉ / NON RETENU": {
        "keywords": ["candidature refusée", "non retenu", "pas retenu", "malheureusement", 
                     "ne pouvons pas donner suite", "n'a pas été retenue", "sans suite favorable", 
                     "au regret", "pas donné suite", "décliné votre candidature", 
                     "réponse négative", "défavorable", "pas été sélectionné", 
                     "ne correspondant pas au profil"],
        "priority": 2
    },
    "📝 TEST / ÉVALUATION": {
        "keywords": ["test technique", "évaluation technique", "assessment center", 
                     "exercice technique", "cas pratique", "test de personnalité", 
                     "mise en situation", "test en ligne"],
        "priority": 3
    },
    "📞 ENTRETIEN": {
        "keywords": ["convocation entretien", "invitation entretien", "entretien téléphonique",
                     "entretien visio", "rendez-vous recrutement", "interview", 
                     "rencontrer notre équipe"],
        "priority": 4
    },
    "📧 CANDIDATURE": {
        "keywords": ["votre candidature", "candidature bien reçue", "candidature enregistrée",
                     "accusé de réception", "votre CV a bien été"],
        "priority": 5
    },
    "💼 OFFRES D'EMPLOI": {
        "keywords": ["offre d'emploi", "opportunité professionnelle", "recrute un", 
                     "poste à pourvoir", "nous recherchons", "nouvelle offre", 
                     "postulez maintenant", "emplois pour", "job alert"],
        "priority": 6
    },
}

# ============================================================================
# FONCTIONS GMAIL
# ============================================================================

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
    
    # Extraire le corps du message
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
        
        query = f"after:{START_DATE}"
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

# ============================================================================
# FONCTIONS OUTLOOK
# ============================================================================

def get_outlook_token(token_file):
    """Obtient un token d'accès pour Microsoft Graph API"""
    # Configuration Azure AD - À remplir avec vos propres valeurs
    CLIENT_ID = "VOTRE_CLIENT_ID"  # Depuis Azure Portal
    TENANT_ID = "common"  # ou votre tenant ID spécifique
    
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
        
        # Formater la date pour Microsoft Graph
        date_filter = START_DATE.replace('/', '-')
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {date_filter}&$top=200"
        
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

# ============================================================================
# FONCTIONS DE FILTRAGE ET ANALYSE
# ============================================================================

def is_promotional_email(email):
    """Vérifie si un email est une promotion commerciale"""
    sender_lower = email['sender'].lower()
    subject_lower = email['subject'].lower()
    body_lower = email.get('body', '').lower()[:500]  # Premiers 500 caractères
    
    # Vérifier les expéditeurs bloqués
    for blocked in BLOCKED_SENDERS:
        if blocked.lower() in sender_lower:
            return True
    
    # Vérifier les mots-clés de promotion
    text_to_check = subject_lower + " " + body_lower
    promo_count = sum(1 for kw in PROMO_KEYWORDS if kw.lower() in text_to_check)
    
    # Si plus de 2 mots-clés de promo, c'est probablement une pub
    return promo_count >= 2

def extract_links_from_email(body):
    """Extrait les liens d'un email"""
    # Pattern pour les URLs
    url_pattern = r'https?://[^\s<>"\']+(?:\([^\s<>"\']*\)|[^\s<>"\'\)\]])+'
    links = re.findall(url_pattern, body)
    
    # Filtrer les liens pertinents (offres d'emploi)
    job_links = []
    job_domains = ['linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'welcometothejungle.com',
                   'hellowork.com', 'apec.fr', 'cadremploi.fr', 'monster.fr', 'talent.io',
                   'jobs2web.com', 'workday.com', 'greenhouse.io', 'lever.co', 'smartrecruiters.com']
    
    for link in links:
        link_lower = link.lower()
        # Vérifier si c'est un lien d'offre d'emploi
        if any(domain in link_lower for domain in job_domains):
            job_links.append(link)
        elif '/job' in link_lower or '/career' in link_lower or '/emploi' in link_lower:
            job_links.append(link)
    
    return list(set(job_links))  # Supprimer les doublons

def categorize_email(email):
    """Catégorise un email selon son contenu"""
    subject_lower = email['subject'].lower()
    body_lower = email.get('body', '').lower()[:1000]
    text_to_check = subject_lower + " " + body_lower
    
    for category, config in CATEGORIES.items():
        for keyword in config['keywords']:
            if keyword.lower() in text_to_check:
                return category
    
    return None

def create_email_summary(email):
    """Crée un résumé d'un email d'offre d'emploi"""
    body = email.get('body', '')
    
    # Extraire les informations clés
    summary = {
        'compte': email['account'],
        'de': email['sender'],
        'objet': email['subject'],
        'date': email['date'],
        'liens': extract_links_from_email(body)
    }
    
    # Essayer d'extraire le nom de l'entreprise
    company_patterns = [
        r'(?:chez|at|@)\s+([A-Z][A-Za-z\s&]+?)(?:\s+recrute|\s+recherche|\.|\,)',
        r'([A-Z][A-Za-z\s&]+?)\s+recrute',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, email['subject'] + ' ' + body[:500])
        if match:
            summary['entreprise'] = match.group(1).strip()
            break
    
    return summary

# ============================================================================
# GÉNÉRATION DU RAPPORT HTML
# ============================================================================

def generate_html_report(categorized_emails, output_file="rapport_emploi.html"):
    """Génère un rapport HTML avec liens cliquables"""
    
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Job Tracker - Rapport de suivi</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        h1 { text-align: center; margin-bottom: 30px; color: #00d4ff; }
        .stats { display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
        .stat-card { background: #16213e; padding: 20px; border-radius: 10px; text-align: center; min-width: 150px; }
        .stat-card h3 { font-size: 2em; color: #00d4ff; }
        .stat-card p { color: #888; }
        .category { background: #16213e; margin-bottom: 20px; border-radius: 10px; overflow: hidden; }
        .category-header { background: #0f3460; padding: 15px 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
        .category-header:hover { background: #1a4a7a; }
        .category-header h2 { font-size: 1.2em; }
        .category-header .count { background: #00d4ff; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
        .email-list { padding: 0 20px 20px; }
        .email-item { background: #1a1a2e; margin-top: 15px; padding: 15px; border-radius: 8px; border-left: 4px solid #00d4ff; }
        .email-item.accepted { border-left-color: #00ff88; }
        .email-item.refused { border-left-color: #ff4757; }
        .email-item.interview { border-left-color: #ffa502; }
        .email-item.test { border-left-color: #a55eea; }
        .email-meta { display: flex; gap: 15px; margin-bottom: 10px; font-size: 0.85em; color: #888; flex-wrap: wrap; }
        .email-meta span { background: #2a2a4a; padding: 3px 8px; border-radius: 4px; }
        .email-subject { font-weight: bold; margin-bottom: 10px; }
        .email-sender { color: #00d4ff; margin-bottom: 10px; }
        .email-links { margin-top: 10px; }
        .email-links a { display: inline-block; background: #00d4ff; color: #000; padding: 8px 15px; border-radius: 5px; text-decoration: none; margin-right: 10px; margin-top: 5px; font-weight: bold; }
        .email-links a:hover { background: #00a8cc; }
        .no-emails { color: #666; padding: 20px; text-align: center; }
        .generated { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>📊 Job Tracker - Suivi de vos candidatures</h1>
    
    <div class="stats">
"""
    
    # Statistiques
    total = sum(len(emails) for emails in categorized_emails.values())
    html += f'<div class="stat-card"><h3>{total}</h3><p>Total emails</p></div>'
    
    for category, emails in categorized_emails.items():
        if emails:
            emoji = category.split()[0]
            name = ' '.join(category.split()[1:])
            html += f'<div class="stat-card"><h3>{len(emails)}</h3><p>{emoji} {name}</p></div>'
    
    html += "</div>"
    
    # Catégories et emails
    category_classes = {
        "✅ ACCEPTÉ": "accepted",
        "❌ REFUSÉ": "refused", 
        "📞 ENTRETIEN": "interview",
        "📝 TEST": "test"
    }
    
    for category, emails in categorized_emails.items():
        css_class = ""
        for key, cls in category_classes.items():
            if key in category:
                css_class = cls
                break
        
        html += f"""
    <div class="category">
        <div class="category-header">
            <h2>{category}</h2>
            <span class="count">{len(emails)}</span>
        </div>
        <div class="email-list">
"""
        
        if emails:
            for email in emails:
                html += f"""
            <div class="email-item {css_class}">
                <div class="email-meta">
                    <span>📬 {email.get('compte', 'N/A')}</span>
                    <span>📅 {email.get('date', 'N/A')[:16] if email.get('date') else 'N/A'}</span>
                </div>
                <div class="email-sender">📧 De: {email.get('de', 'Inconnu')}</div>
                <div class="email-subject">📝 {email.get('objet', 'Sans objet')}</div>
"""
                
                links = email.get('liens', [])
                if links:
                    html += '<div class="email-links">'
                    for i, link in enumerate(links[:3]):  # Max 3 liens
                        html += f'<a href="{link}" target="_blank">🔗 Voir l\'offre {i+1}</a>'
                    html += '</div>'
                
                html += "</div>"
        else:
            html += '<p class="no-emails">Aucun email dans cette catégorie</p>'
        
        html += """
        </div>
    </div>
"""
    
    html += f"""
    <p class="generated">Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n📄 Rapport HTML généré: {output_file}")
    return output_file

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    print("=" * 80)
    print("🔍 JOB TRACKER - Suivi automatique de vos emails emploi")
    print("=" * 80)
    
    all_emails = []
    
    # Récupérer les emails de tous les comptes
    for account in ACCOUNTS:
        if account['type'] == 'gmail':
            emails = fetch_gmail_emails(account)
        elif account['type'] == 'outlook':
            emails = fetch_outlook_emails(account)
        else:
            print(f"   ⚠️ Type de compte non supporté: {account['type']}")
            continue
        
        all_emails.extend(emails)
    
    print(f"\n📬 Total: {len(all_emails)} emails récupérés")
    
    # Filtrer et catégoriser
    categorized = {cat: [] for cat in CATEGORIES.keys()}
    ignored_count = 0
    
    for email in all_emails:
        # Ignorer les promotions
        if is_promotional_email(email):
            ignored_count += 1
            continue
        
        # Catégoriser
        category = categorize_email(email)
        if category:
            summary = create_email_summary(email)
            categorized[category].append(summary)
    
    print(f"🚫 {ignored_count} emails promotionnels ignorés")
    
    # Affichage console
    print("\n" + "=" * 80)
    print("📊 RÉCAPITULATIF DE VOS EMAILS EMPLOI")
    print("=" * 80)
    
    for category, emails in categorized.items():
        if emails:
            print(f"\n{category} ({len(emails)} email(s))")
            print("-" * 70)
            for i, email in enumerate(emails, 1):
                print(f"  {i}. [{email['compte']}]")
                print(f"     📧 De: {email['de']}")
                print(f"     📝 Objet: {email['objet']}")
                if email.get('liens'):
                    print(f"     🔗 Liens: {len(email['liens'])} lien(s) trouvé(s)")
                print()
    
    # Résumé
    print("=" * 80)
    print("📈 RÉSUMÉ:")
    for category, emails in categorized.items():
        if emails:
            print(f"   {category}: {len(emails)}")
    print("=" * 80)
    
    # Générer le rapport HTML
    generate_html_report(categorized)
    
    # Sauvegarder les données en JSON
    with open('job_tracker_data.json', 'w', encoding='utf-8') as f:
        json.dump(categorized, f, ensure_ascii=False, indent=2)
    print("💾 Données sauvegardées dans job_tracker_data.json")

if __name__ == "__main__":
    main()

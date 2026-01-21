"""
Configuration du Job Tracker
"""

from datetime import datetime, timedelta

# Scopes pour Gmail
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Scopes pour Outlook
OUTLOOK_SCOPES = ['https://graph.microsoft.com/Mail.Read']


def get_target_date():
    """
    Calcule la date cible pour l'analyse des emails.
    - Si aujourd'hui est lundi (weekday=0) : retourne vendredi dernier (J-4)
    - Sinon : retourne J-2
    
    Returns:
        tuple: (date_gmail: str "YYYY/MM/DD", date_outlook: str "YYYY-MM-DD")
    """
    today = datetime.now()
    
    # Lundi = 0, Mardi = 1, ..., Dimanche = 6
    if today.weekday() == 0:  # Lundi
        days_back = 4  # Retour au vendredi précédent
    else:
        days_back = 2  # J-2
    
    target_date = today - timedelta(days=days_back)
    
    # Format pour Gmail (YYYY/MM/DD)
    date_gmail = target_date.strftime("%Y/%m/%d")
    # Format pour Outlook (YYYY-MM-DD)
    date_outlook = target_date.strftime("%Y-%m-%d")
    
    return date_gmail, date_outlook


def get_date_info():
    """
    Retourne les informations de date pour affichage.
    
    Returns:
        dict: Informations sur les dates (aujourd'hui, cible, jours)
    """
    today = datetime.now()
    date_gmail, date_outlook = get_target_date()
    
    if today.weekday() == 0:
        days_back = 4
        day_name = "lundi"
        target_day = "vendredi"
    else:
        days_back = 2
        day_name = today.strftime("%A").lower()
        target_date = today - timedelta(days=days_back)
        target_day = target_date.strftime("%A").lower()
    
    return {
        'today': today.strftime("%d/%m/%Y"),
        'today_weekday': day_name,
        'target_date': date_gmail.replace('/', '-'),
        'target_weekday': target_day,
        'days_back': days_back
    }


# Date de début de recherche (calculée dynamiquement)
START_DATE_GMAIL, START_DATE_OUTLOOK = get_target_date()

# Liste des comptes à surveiller
ACCOUNTS = [
    {"type": "gmail", "name": "Pro", "token_file": "token_pro.pickle"},
    {"type": "gmail", "name": "Perso", "token_file": "token_perso.pickle"},
    # {"type": "outlook", "name": "Outlook Pro", "token_file": "token_outlook.json"},
]

# ============================================================================
# FILTRES ANTI-SPAM / PROMOTIONS
# ============================================================================

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
    "accounts.google.com",
    "etmail.sony",
    "noreply@glassdoor.com",
    "notification@emails.hellowork.com",
    "alerte@emails.hellowork.com",
    "notify-noreply@google.com",
    "jobnotification@",
    "noreply55.jobs2web.com",
    "noreply12.jobs2web.com",
    "ekez.fa.sender@workflow.mail",
]

PROMO_KEYWORDS = [
    "promotion", "soldes", "réduction", "-50%", "-30%", "code promo",
    "livraison gratuite", "vente flash", "black friday", "cyber monday",
    "meilleur de la promotion", "articles sélectionnés", "shopping",
    "panier", "commande", "achat", "boutique", "enregistrez votre produit",
    "webinar", "campaign", "dons", "soutien", "formation gratuite",
    "alerte offre d'emploi", "job alert", "nouvelle offre d'emploi",
    "offre pour", "emplois pour", "postulez maintenant",
    "un poste comme", "autres emplois", "vous attendent",
    "jobs posted", "new jobs", "job notification",
]

# ============================================================================
# CATÉGORIES D'EMAILS
# ============================================================================

CATEGORIES = {
    "✅ ACCEPTÉ / SÉLECTIONNÉ": {
        "keywords": [
            "choisi pour le poste", "retenu pour le poste", "sélectionné pour le poste",
            "félicitations pour votre", "nous avons le plaisir de vous informer",
            "heureux de vous annoncer", "votre profil a été retenu",
            "convoqué pour", "invitation à rejoindre notre équipe",
            "proposition d'embauche", "offre d'emploi acceptée",
            "votre candidature a été retenue"
        ],
        "priority": 1
    },
    "❌ REFUSÉ / NON RETENU": {
        "keywords": [
            "candidature refusée", "non retenu", "pas retenu", "malheureusement",
            "ne pouvons pas donner suite", "n'a pas été retenue", "sans suite favorable",
            "au regret", "pas donné suite", "décliné votre candidature",
            "réponse négative", "défavorable", "pas été sélectionné",
            "ne correspondant pas au profil"
        ],
        "priority": 2
    },
    "📝 TEST / ÉVALUATION": {
        "keywords": [
            "test technique", "évaluation technique", "assessment center",
            "exercice technique", "cas pratique", "test de personnalité",
            "mise en situation", "test en ligne"
        ],
        "priority": 3
    },
    "📞 ENTRETIEN": {
        "keywords": [
            "convocation entretien", "invitation entretien", "entretien téléphonique",
            "entretien visio", "rendez-vous recrutement", "interview",
            "rencontrer notre équipe"
        ],
        "priority": 4
    },
    "📧 CANDIDATURE": {
        "keywords": [
            "votre candidature", "candidature bien reçue", "candidature enregistrée",
            "accusé de réception", "votre CV a bien été"
        ],
        "priority": 5
    },
    "💼 OFFRES D'EMPLOI": {
        "keywords": [
            "offre d'emploi", "opportunité professionnelle", "recrute un",
            "poste à pourvoir", "nous recherchons", "nouvelle offre",
            "postulez maintenant", "emplois pour", "job alert"
        ],
        "priority": 6
    },
}

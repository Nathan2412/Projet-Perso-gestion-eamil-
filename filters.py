"""
Fonctions de filtrage et analyse des emails
"""

import re
from config import BLOCKED_SENDERS, PROMO_KEYWORDS, CATEGORIES


def is_promotional_email(email):
    """Vérifie si un email est une promotion commerciale ou newsletter automatique"""
    sender_lower = email['sender'].lower()
    subject_lower = email['subject'].lower()
    body_lower = email.get('body', '').lower()[:500]

    # Vérifier les expéditeurs bloqués
    for blocked in BLOCKED_SENDERS:
        if blocked.lower() in sender_lower:
            return True

    # Vérifier les mots-clés de promotion
    text_to_check = subject_lower + " " + body_lower
    promo_count = sum(1 for kw in PROMO_KEYWORDS if kw.lower() in text_to_check)

    if promo_count >= 2:
        return True

    # Détecter les alertes emploi automatiques
    newsletter_patterns = [
        r"alerte.*emploi",
        r"job.*alert",
        r"\d+\s+autres?\s+emplois?",
        r"\d+\s+nouveaux?\s+emplois?",
        r"postulez maintenant.*et\s+\d+",
        r"pour\s+\w+\s+vous\s+attendent",
        r"nouvelle[s]?\s+offre[s]?\s+d'emploi\s+rien\s+que\s+pour\s+vous",
        r"jobs?\s+posted\s+from",
        r"new\s+jobs?\s+from",
    ]

    for pattern in newsletter_patterns:
        if re.search(pattern, text_to_check):
            return True

    return False


def extract_links_from_email(body):
    """Extrait les liens d'un email"""
    url_pattern = r'https?://[^\s<>"\']+(?:\([^\s<>"\']*\)|[^\s<>"\'\)\]])+'
    links = re.findall(url_pattern, body)

    job_domains = [
        'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'welcometothejungle.com',
        'hellowork.com', 'apec.fr', 'cadremploi.fr', 'monster.fr', 'talent.io',
        'jobs2web.com', 'workday.com', 'greenhouse.io', 'lever.co', 'smartrecruiters.com'
    ]

    job_links = []
    for link in links:
        link_lower = link.lower()
        if any(domain in link_lower for domain in job_domains):
            job_links.append(link)
        elif '/job' in link_lower or '/career' in link_lower or '/emploi' in link_lower:
            job_links.append(link)

    return list(set(job_links))


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
    """Crée un résumé d'un email"""
    body = email.get('body', '')

    summary = {
        'compte': email['account'],
        'de': email['sender'],
        'objet': email['subject'],
        'date': email['date'],
        'liens': extract_links_from_email(body)
    }

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


def clean_email_body(body):
    """Nettoie le contenu HTML d'un email pour le rendre lisible"""
    if not body:
        return "(Aucun contenu disponible)"

    # Supprimer les blocs style, script, head
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<head[^>]*>.*?</head>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)

    # Supprimer les attributs style inline
    clean = re.sub(r'\s+style="[^"]*"', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+class="[^"]*"', '', clean, flags=re.IGNORECASE)

    # Remplacer les balises par des retours à la ligne
    clean = re.sub(r'<br\s*/?>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</p>', '\n\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</div>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</tr>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</li>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<li[^>]*>', '  • ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<h[1-6][^>]*>', '\n\n▶ ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</h[1-6]>', '\n', clean, flags=re.IGNORECASE)

    # Supprimer les autres balises HTML
    clean = re.sub(r'<[^>]+>', ' ', clean)

    # Décoder les entités HTML
    html_entities = {
        '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&quot;': '"', '&#39;': "'", '&apos;': "'",
        '&euro;': '€', '&copy;': '©', '&reg;': '®',
        '&#160;': ' ', '&#8217;': "'", '&#8220;': '"', '&#8221;': '"',
        '&rsquo;': "'", '&lsquo;': "'", '&rdquo;': '"', '&ldquo;': '"',
        '&ndash;': '–', '&mdash;': '—', '&bull;': '•',
    }
    for entity, char in html_entities.items():
        clean = clean.replace(entity, char)

    clean = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))) if int(m.group(1)) < 65536 else '', clean)

    # Nettoyer les espaces
    clean = re.sub(r'[ \t]+', ' ', clean)
    clean = re.sub(r'\n[ \t]+', '\n', clean)
    clean = re.sub(r'[ \t]+\n', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)

    # Supprimer les footers
    footer_patterns = [
        r'Commercial Register.*$',
        r'Managing Directors?:.*$',
        r'District Court.*$',
        r'@media\s*\([^)]+\)\s*\{[^}]+\}',
        r'\{[^}]*font-size[^}]*\}',
    ]
    for pattern in footer_patterns:
        clean = re.sub(pattern, '', clean, flags=re.IGNORECASE | re.DOTALL)

    clean = clean.strip()

    if len(clean) > 3000:
        clean = clean[:3000] + "\n\n[... contenu tronqué ...]"

    return clean if clean else "(Contenu vide après nettoyage)"

"""
Job Tracker - Script principal
Suivi automatique des emails liés à la recherche d'emploi
"""

import sys
import json

# Encodage UTF-8 pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Imports des modules
from config import ACCOUNTS, CATEGORIES, get_date_info
from gmail_handler import fetch_gmail_emails
from outlook_handler import fetch_outlook_emails
from filters import is_promotional_email, categorize_email, create_email_summary, clean_email_body, extract_links_from_email
from report import generate_html_report


def display_date_info():
    """Affiche les informations sur la période d'analyse"""
    info = get_date_info()
    print(f"📅 Aujourd'hui: {info['today']} ({info['today_weekday']})")
    print(f"🔍 Analyse des emails depuis: {info['target_date']} ({info['target_weekday']})")
    print(f"   → Période: J-{info['days_back']} jours")
    if info['days_back'] == 4:
        print("   ℹ️  Lundi détecté: retour au vendredi précédent")


def display_email_detail(email):
    """Affiche le détail complet d'un email"""
    print("\n" + "=" * 80)
    print("📧 DÉTAIL DE L'EMAIL")
    print("=" * 80)
    print(f"📌 Compte: [{email.get('account', 'Inconnu')}]")
    print(f"📧 De: {email.get('sender', 'Inconnu')}")
    print(f"📝 Objet: {email.get('subject', 'Sans objet')}")
    print(f"📅 Date: {email.get('date', 'Inconnue')}")
    print("-" * 80)
    print("📄 CONTENU:")
    print("-" * 80)

    body = email.get('body', '')
    clean_body = clean_email_body(body)
    print(clean_body)

    # Afficher les liens
    links = extract_links_from_email(body)
    if links:
        print("\n" + "-" * 80)
        print("🔗 LIENS TROUVÉS:")
        for i, link in enumerate(links[:10], 1):
            print(f"  {i}. {link}")

    print("=" * 80)


def main():
    print("=" * 80)
    print("🔍 JOB TRACKER - Suivi automatique de vos emails emploi")
    print("=" * 80)
    
    # Afficher les informations de date
    display_date_info()
    print("-" * 80)

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
    emails_index = []
    global_num = 0

    for email in all_emails:
        if is_promotional_email(email):
            ignored_count += 1
            continue

        category = categorize_email(email)
        if category:
            global_num += 1
            summary = create_email_summary(email)
            summary['num'] = global_num
            categorized[category].append(summary)
            emails_index.append((global_num, email, summary, category))

    print(f"🚫 {ignored_count} emails promotionnels ignorés")

    # Affichage console
    print("\n" + "=" * 80)
    print("📊 RÉCAPITULATIF DE VOS EMAILS EMPLOI")
    print("=" * 80)

    for category, emails in categorized.items():
        if emails:
            print(f"\n{category} ({len(emails)} email(s))")
            print("-" * 70)
            for email in emails:
                print(f"  #{email['num']}. [{email['compte']}]")
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

    # Sauvegarder les données
    with open('job_tracker_data.json', 'w', encoding='utf-8') as f:
        json.dump(categorized, f, ensure_ascii=False, indent=2)
    print("💾 Données sauvegardées dans job_tracker_data.json")

    # Mode interactif
    if emails_index:
        print("\n" + "=" * 80)
        print("🔎 MODE DÉTAIL - Tapez le numéro d'un email pour voir son contenu")
        print("   (ou 'q' pour quitter)")
        print("=" * 80)

        while True:
            try:
                user_input = input("\n📌 Numéro de l'email (ou 'q' pour quitter): ").strip()

                if user_input.lower() in ['q', 'quit', 'exit', '']:
                    print("👋 Au revoir!")
                    break

                try:
                    num = int(user_input)
                    found = False
                    for idx_num, email_full, summary, cat in emails_index:
                        if idx_num == num:
                            display_email_detail(email_full)
                            found = True
                            break

                    if not found:
                        print(f"❌ Email #{num} non trouvé. Numéros valides: 1 à {len(emails_index)}")

                except ValueError:
                    print("❌ Veuillez entrer un numéro valide ou 'q' pour quitter.")

            except (KeyboardInterrupt, EOFError):
                print("\n👋 Au revoir!")
                break


if __name__ == "__main__":
    main()

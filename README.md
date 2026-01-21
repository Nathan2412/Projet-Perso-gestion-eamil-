# 📧 Job Tracker - Suivi automatique des emails d'emploi

Un outil Python pour suivre automatiquement vos emails liés à la recherche d'emploi depuis plusieurs comptes (Gmail et Outlook).

## ✨ Fonctionnalités

### ✅ Implémenté

- **Multi-comptes** : Supporte plusieurs comptes Gmail et Outlook simultanément
- **Catégorisation automatique** des emails :
  - ✅ Accepté / Sélectionné
  - ❌ Refusé / Non retenu
  - 📝 Test / Évaluation
  - 📞 Entretien
  - 📧 Candidature
  - 💼 Offres d'emploi
- **Filtrage des promotions** : Ignore automatiquement les emails promotionnels (Michael Kors, Zara, etc.)
- **Extraction des liens** : Récupère les liens vers les offres d'emploi
- **Rapport HTML** : Génère un beau rapport avec liens cliquables
- **Export JSON** : Sauvegarde les données pour analyse ultérieure
- **Affichage de l'expéditeur** : Voir qui a envoyé chaque email
- **Analyse par période dynamique** : Filtrage intelligent basé sur la date (J-2 ou J-4 le lundi)

## 📅 Système de date dynamique

Le script analyse les emails selon une logique de date intelligente :

| Jour actuel | Période analysée | Explication |
|-------------|------------------|-------------|
| **Lundi**   | J-4 (vendredi)   | Retourne au vendredi précédent pour ne pas manquer les emails du week-end |
| **Mardi à Dimanche** | J-2 | Analyse les 2 derniers jours |

### Exemple :
- Si on est **Lundi 20 janvier**, le script analyse depuis le **Vendredi 16 janvier**
- Si on est **Mercredi 22 janvier**, le script analyse depuis le **Lundi 20 janvier**

### 🔜 À venir

- [ ] Résumé automatique des offres d'emploi avec IA
- [ ] Notifications en temps réel
- [ ] Interface web
- [ ] Statistiques et graphiques

## 📋 Prérequis

- Python 3.10+
- Compte Google Cloud (pour Gmail)
- Compte Azure AD (pour Outlook, optionnel)

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd C:\Users\natha\Downloads\job_tracker
```

### 2. Installer les dépendances

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client msal requests
```

### 3. Configuration Gmail

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un projet ou sélectionnez-en un existant
3. Activez l'API Gmail
4. Créez des identifiants OAuth 2.0 (Application de bureau)
5. Téléchargez le fichier JSON et renommez-le `credentials.json`
6. Placez-le dans le dossier `job_tracker`

### 4. Configuration Outlook (Optionnel)

1. Allez sur [Azure Portal](https://portal.azure.com/)
2. Inscrivez une nouvelle application
3. Notez le Client ID
4. Modifiez `CLIENT_ID` dans `job_tracker.py`
5. Décommentez la ligne Outlook dans `ACCOUNTS`

## 💻 Utilisation

```bash
python job_tracker.py
```

La première exécution ouvrira une fenêtre de navigateur pour vous connecter à chaque compte.

## 📁 Structure des fichiers

```
job_tracker/
├── job_tracker.py          # Script principal
├── config.py               # Configuration (comptes, filtres, catégories, dates)
├── gmail_handler.py        # Gestion des emails Gmail
├── outlook_handler.py      # Gestion des emails Outlook
├── filters.py              # Filtres anti-spam et catégorisation
├── report.py               # Génération du rapport HTML
├── lancer_job_tracker.bat  # Lanceur Windows
├── credentials.json        # Identifiants Google (à créer)
├── token_pro.pickle        # Token Gmail compte Pro (généré automatiquement)
├── token_perso.pickle      # Token Gmail compte Perso (généré automatiquement)
├── token_outlook.json      # Token Outlook (généré automatiquement)
├── job_tracker_report.html # Rapport HTML généré
├── job_tracker_data.json   # Données exportées
└── README.md               # Ce fichier
```

## ⚙️ Configuration

### Ajouter un compte Gmail

Modifiez la liste `ACCOUNTS` dans `job_tracker.py` :

```python
ACCOUNTS = [
    {"type": "gmail", "name": "Pro", "token_file": "token_pro.pickle"},
    {"type": "gmail", "name": "Perso", "token_file": "token_perso.pickle"},
    {"type": "gmail", "name": "Autre", "token_file": "token_autre.pickle"},  # Nouveau compte
]
```

### Ajouter un compte Outlook

```python
ACCOUNTS = [
    # ... comptes Gmail ...
    {"type": "outlook", "name": "Outlook Pro", "token_file": "token_outlook.json"},
]
```

### Modifier les filtres anti-spam

Ajoutez des expéditeurs à bloquer dans `BLOCKED_SENDERS` :

```python
BLOCKED_SENDERS = [
    "michaelkors",
    "zara.com",
    "votre-spam@exemple.com",  # Ajouter ici
]
```

### Modifier les mots-clés de catégories

Modifiez le dictionnaire `CATEGORIES` pour personnaliser la détection.

## 📊 Rapport HTML

Le rapport généré (`rapport_emploi.html`) inclut :

- 📈 Statistiques par catégorie
- 📧 Liste des emails avec expéditeur et objet
- 🔗 Liens cliquables vers les offres d'emploi
- 🎨 Interface moderne et responsive

Ouvrez-le dans votre navigateur pour une meilleure visualisation.

## 🔒 Sécurité

⚠️ **Important** :
- Ne partagez jamais vos fichiers `credentials.json`, `*.pickle` ou `*.json` contenant des tokens
- Ces fichiers sont ajoutés au `.gitignore` par défaut
- Utilisez des mots de passe d'application pour Gmail si l'authentification échoue

## 🐛 Problèmes courants

### "Invalid credentials" avec Gmail

1. Vérifiez que l'IMAP est activé dans Gmail
2. Ajoutez votre email comme testeur dans Google Cloud Console
3. Supprimez le fichier `token_*.pickle` et relancez

### Les promotions apparaissent toujours

Ajoutez l'expéditeur dans `BLOCKED_SENDERS` ou les mots-clés dans `PROMO_KEYWORDS`.

### Pas de liens extraits

Le script cherche les liens des plateformes d'emploi connues. Ajoutez les domaines manquants dans `job_domains` de la fonction `extract_links_from_email()`.

## 📝 Changelog

### v2.1.0 (21/01/2026)
- ✨ Système de date dynamique (J-2, ou J-4 le lundi)
- ✨ Affichage de la période d'analyse au lancement
- 🔧 Code modularisé en plusieurs fichiers (config, handlers, filters, report)
- 📚 Documentation mise à jour

### v2.0.0 (17/01/2026)
- ✨ Support multi-comptes Gmail + Outlook
- ✨ Filtrage des emails promotionnels
- ✨ Extraction des liens d'offres d'emploi
- ✨ Génération de rapport HTML
- ✨ Export JSON des données
- 🐛 Correction des faux positifs "sélectionné"

### v1.0.0 (15/01/2026)
- 🎉 Version initiale
- Lecture des emails Gmail
- Catégorisation basique

## 📄 Licence

Usage personnel uniquement.

## 👤 Auteur

Nathan Tubiana

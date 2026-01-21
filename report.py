"""
Génération du rapport HTML
"""

from datetime import datetime


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
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #1a1a2e; 
            color: #eee; 
            padding: 20px; 
        }
        h1 { text-align: center; margin-bottom: 30px; color: #00d4ff; }
        
        .stats { 
            display: flex; 
            justify-content: center; 
            gap: 20px; 
            margin-bottom: 30px; 
            flex-wrap: wrap; 
        }
        .stat-card { 
            background: #16213e; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center; 
            min-width: 150px; 
        }
        .stat-card h3 { font-size: 2em; color: #00d4ff; }
        .stat-card p { color: #888; }
        
        .category { 
            background: #16213e; 
            margin-bottom: 20px; 
            border-radius: 10px; 
            overflow: hidden; 
        }
        .category-header { 
            background: #0f3460; 
            padding: 15px 20px; 
            cursor: pointer; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
        }
        .category-header:hover { background: #1a4a7a; }
        .category-header h2 { font-size: 1.2em; }
        .category-header .count { 
            background: #00d4ff; 
            color: #000; 
            padding: 5px 15px; 
            border-radius: 20px; 
            font-weight: bold; 
        }
        
        .email-list { padding: 0 20px 20px; }
        .email-item { 
            background: #1a1a2e; 
            margin-top: 15px; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 4px solid #00d4ff; 
        }
        .email-item.accepted { border-left-color: #00ff88; }
        .email-item.refused { border-left-color: #ff4757; }
        .email-item.interview { border-left-color: #ffa502; }
        .email-item.test { border-left-color: #a55eea; }
        
        .email-meta { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 10px; 
            font-size: 0.85em; 
            color: #888; 
            flex-wrap: wrap; 
        }
        .email-meta span { 
            background: #2a2a4a; 
            padding: 3px 8px; 
            border-radius: 4px; 
        }
        .email-subject { font-weight: bold; margin-bottom: 10px; }
        .email-sender { color: #00d4ff; margin-bottom: 10px; }
        
        .email-links { margin-top: 10px; }
        .email-links a { 
            display: inline-block; 
            background: #00d4ff; 
            color: #000; 
            padding: 8px 15px; 
            border-radius: 5px; 
            text-decoration: none; 
            margin-right: 10px; 
            margin-top: 5px; 
            font-weight: bold; 
        }
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
                    for i, link in enumerate(links[:3]):
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

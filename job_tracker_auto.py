"""
Job Tracker - Script d'automatisation avec notifications Windows
Ce script est lancé automatiquement tous les jours à 10h
"""

import subprocess
import sys
import os
from datetime import datetime

# Chemin du projet
PROJECT_PATH = r"C:\Users\natha\OneDrive\Projet perso\job_tracker"

def install_winotify():
    """Installe winotify si pas présent"""
    try:
        import winotify
    except ImportError:
        print("📦 Installation de winotify pour les notifications...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "winotify", "-q"])

def send_notification(title, message):
    """Envoie une notification Windows"""
    try:
        from winotify import Notification, audio
        
        toast = Notification(
            app_id="Job Tracker",
            title=title,
            msg=message,
            duration="long"
        )
        
        # Bouton pour ouvrir le rapport
        rapport_path = os.path.join(PROJECT_PATH, "rapport_emploi.html")
        toast.add_actions(label="📊 Voir le rapport", launch=rapport_path)
        
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return True
    except Exception as e:
        print(f"❌ Erreur notification: {e}")
        return False

def run_job_tracker():
    """Lance le job tracker principal"""
    os.chdir(PROJECT_PATH)
    
    # Importer et exécuter le script principal
    job_tracker_path = os.path.join(PROJECT_PATH, "job_tracker.py")
    
    result = subprocess.run(
        [sys.executable, job_tracker_path],
        capture_output=True,
        text=True,
        cwd=PROJECT_PATH,
        encoding='utf-8',
        errors='ignore'
    )
    
    # Afficher aussi les erreurs
    if result.stderr:
        print("ERREURS:", result.stderr)
    
    return result.stdout, result.returncode

def parse_results(output):
    """Parse les résultats du job tracker"""
    results = {
        "candidatures": 0,
        "offres": 0,
        "entretiens": 0,
        "acceptes": 0,
        "refuses": 0
    }
    
    lines = output.split('\n')
    for line in lines:
        if "CANDIDATURE:" in line:
            try:
                results["candidatures"] = int(line.split(":")[-1].strip())
            except:
                pass
        elif "OFFRES D'EMPLOI:" in line:
            try:
                results["offres"] = int(line.split(":")[-1].strip())
            except:
                pass
        elif "ENTRETIEN:" in line:
            try:
                results["entretiens"] = int(line.split(":")[-1].strip())
            except:
                pass
        elif "ACCEPTÉ" in line and ":" in line:
            try:
                results["acceptes"] = int(line.split(":")[-1].strip())
            except:
                pass
        elif "REFUSÉ" in line and ":" in line:
            try:
                results["refuses"] = int(line.split(":")[-1].strip())
            except:
                pass
    
    return results

def main():
    print("=" * 60)
    print("🔔 JOB TRACKER - Exécution automatique")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)
    
    # Installer winotify si nécessaire
    install_winotify()
    
    # Lancer le job tracker
    print("\n🚀 Lancement du Job Tracker...")
    output, return_code = run_job_tracker()
    
    print(output)
    
    if return_code == 0:
        # Parser les résultats
        results = parse_results(output)
        
        # Créer le message de notification
        title = "📊 Job Tracker - Rapport du " + datetime.now().strftime('%d/%m')
        
        messages = []
        
        if results["acceptes"] > 0:
            messages.append(f"🎉 {results['acceptes']} ACCEPTÉ(S) !")
        
        if results["entretiens"] > 0:
            messages.append(f"📞 {results['entretiens']} entretien(s)")
        
        if results["refuses"] > 0:
            messages.append(f"❌ {results['refuses']} refus")
        
        messages.append(f"📧 {results['candidatures']} candidatures")
        messages.append(f"💼 {results['offres']} offres d'emploi")
        
        message = "\n".join(messages)
        
        # Envoyer la notification
        print("\n🔔 Envoi de la notification...")
        send_notification(title, message)
        
        print("\n✅ Exécution terminée avec succès !")
    else:
        # Notification d'erreur
        send_notification(
            "❌ Job Tracker - Erreur",
            "Une erreur s'est produite lors de l'exécution.\nVérifiez les logs."
        )
        print("\n❌ Erreur lors de l'exécution")

if __name__ == "__main__":
    main()

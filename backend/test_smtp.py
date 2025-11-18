#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration SMTP
Usage: python test_smtp.py
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_smtp_connection():
    """Test la connexion SMTP avec la configuration actuelle"""
    
    # Configuration depuis .env
    smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("EMAILS_FROM_EMAIL")
    
    print("🔧 Configuration SMTP détectée:")
    print(f"   Host: {smtp_host}")
    print(f"   Port: {smtp_port}")
    print(f"   User: {smtp_user}")
    print(f"   From: {from_email}")
    print(f"   Password: {'*' * len(smtp_password) if smtp_password else 'NON DÉFINI'}")
    print()
    
    if not smtp_user or not smtp_password:
        print("❌ ERREUR: SMTP_USER ou SMTP_PASSWORD non défini dans le fichier .env")
        return False
    
    try:
        print("🔄 Test de connexion SMTP...")
        
        # Créer la connexion SMTP
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Activer le debug pour voir les détails
        
        print("🔄 Activation de STARTTLS...")
        server.starttls()
        
        print("🔄 Tentative d'authentification...")
        server.login(smtp_user, smtp_password)
        
        print("✅ Connexion SMTP réussie !")
        
        # Test d'envoi d'email (optionnel)
        test_email = input("Voulez-vous envoyer un email de test ? (o/N): ").lower().strip()
        if test_email == 'o':
            to_email = input("Adresse email de destination: ").strip()
            if to_email:
                send_test_email(server, from_email, to_email)
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_code = str(e)
        print(f"❌ ERREUR D'AUTHENTIFICATION: {error_code}")
        
        if "5.7.139" in error_code or "basic authentication is disabled" in error_code.lower():
            print()
            print("🔧 SOLUTION REQUISE - Mot de passe d'application:")
            print("1. Connectez-vous à votre compte Microsoft/Outlook")
            print("2. Allez dans Sécurité > Options de sécurité avancées")
            print("3. Activez l'authentification à deux facteurs (2FA)")
            print("4. Générez un 'mot de passe d'application' pour SMTP")
            print("5. Remplacez SMTP_PASSWORD dans .env par ce nouveau mot de passe")
            print()
            print("📖 Consultez SMTP_OUTLOOK_SETUP.md pour plus de détails")
        
        return False
        
    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        return False

def send_test_email(server, from_email, to_email):
    """Envoie un email de test"""
    try:
        print(f"📧 Envoi d'un email de test à {to_email}...")
        
        # Créer le message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Test SMTP - SendBulletin"
        
        body = """
        <h2>Test SMTP réussi !</h2>
        <p>Ce message confirme que votre configuration SMTP fonctionne correctement.</p>
        <p><strong>Serveur:</strong> SendBulletin</p>
        <p><strong>Date:</strong> {}</p>
        """.format(str(os.popen('date /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip()))
        
        msg.attach(MIMEText(body, 'html'))
        
        # Envoyer
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        
        print("✅ Email de test envoyé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email de test: {str(e)}")

if __name__ == "__main__":
    print("🧪 Test de configuration SMTP - SendBulletin")
    print("=" * 50)
    
    success = test_smtp_connection()
    
    print()
    print("=" * 50)
    if success:
        print("✅ Configuration SMTP validée !")
        print("Vous pouvez maintenant utiliser l'application SendBulletin.")
    else:
        print("❌ Configuration SMTP échouée.")
        print("Consultez SMTP_OUTLOOK_SETUP.md pour résoudre le problème.")
#!/usr/bin/env python3
"""
Test rapide et non interactif de la connexion SMTP avec les variables du fichier .env
"""

import os
import sys
import smtplib
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()

    host = os.getenv("SMTP_HOST", "smtp.office365.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not user or not password:
        print("❌ SMTP_USER ou SMTP_PASSWORD manquant dans .env")
        return 2

    print("🔧 Test SMTP (non interactif)")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   User: {user}")

    try:
        server = smtplib.SMTP(host, port, timeout=20)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        print("✅ Authentification SMTP réussie")
        server.quit()
        return 0
    except smtplib.SMTPAuthenticationError as e:
        msg = str(e)
        print(f"❌ ERREUR D'AUTHENTIFICATION: {msg}")
        if "5.7.139" in msg or "basic authentication is disabled" in msg.lower():
            print("➡️ Outlook/Hotmail nécessite un mot de passe d'application (2FA activée)")
        return 1
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""
Test direct de l'endpoint email-recent-activity-detailed
"""
import sys
from app.db.session import SessionLocal
from app.db.base import Base  # Import all models
from app.modules.emails import models
from datetime import datetime, timedelta

def test_activity_logic():
    print("=" * 60)
    print("TEST DE LA LOGIQUE DE L'ACTIVITÉ RÉCENTE")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Récupérer les 5 derniers emails
        emails = (
            db.query(models.Email)
            .order_by(models.Email.created_at.desc())
            .limit(5)
            .all()
        )
        
        print(f"\n📧 Emails trouvés: {len(emails)}")
        
        result = []
        for i, email in enumerate(emails, 1):
            print(f"\n{i}. Email ID: {email.id}")
            print(f"   Destinataire: {email.recipient_email}")
            print(f"   Statut: {email.status}")
            print(f"   Créé le: {email.created_at}")
            print(f"   Sujet: {email.subject}")
            
            # Calculer le temps écoulé
            if email.created_at:
                now = datetime.utcnow()
                created_at = email.created_at
                time_diff = now - created_at
                
                if time_diff < timedelta(minutes=1):
                    time_ago = "Il y a quelques secondes"
                elif time_diff < timedelta(hours=1):
                    minutes = int(time_diff.total_seconds() / 60)
                    time_ago = f"Il y a {minutes} min"
                elif time_diff < timedelta(days=1):
                    hours = int(time_diff.total_seconds() / 3600)
                    time_ago = f"Il y a {hours}h"
                else:
                    days = time_diff.days
                    time_ago = f"Il y a {days}j"
            else:
                time_ago = "Date inconnue"
            
            # Extraire le nom du destinataire de l'email (partie avant @)
            recipient_name = email.recipient_email.split('@')[0].replace('.', ' ').title() if email.recipient_email else "Inconnu"
            
            # Extraire le mois du bulletin du sujet si possible
            bulletin_month = "Bulletin de salaire"
            if email.subject and "bulletin" in email.subject.lower():
                bulletin_month = email.subject
            
            activity = {
                "id": str(email.id),
                "employee": recipient_name,
                "email": email.recipient_email or "",
                "status": "success" if email.status == "sent" else ("failed" if email.status == "failed" else "pending"),
                "date": time_ago,
                "bulletinMonth": bulletin_month,
                "created_at": email.created_at.isoformat() if email.created_at else None
            }
            
            result.append(activity)
            print(f"   ✅ Activité créée: {activity}")
        
        print(f"\n✅ Total activités créées: {len(result)}")
        
        # Afficher le résultat JSON
        import json
        print("\n📋 Résultat JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_activity_logic()


"""
Test pour vérifier que les bulletins sont bien enregistrés dans la base de données
"""
from app.db.session import SessionLocal
from app.db.base import Base  # Import all models
from app.modules.emails.models import Email
from sqlalchemy import func

def check_emails_before_and_after():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("VÉRIFICATION DES EMAILS DANS LA BASE DE DONNÉES")
        print("=" * 60)
        
        # Compter les emails avant
        total_before = db.query(Email).count()
        print(f"\n📊 Total d'emails AVANT: {total_before}")
        
        # Statistiques par statut
        print("\n📈 Statistiques par statut:")
        statuses = db.query(
            Email.status,
            func.count(Email.id).label('count')
        ).group_by(Email.status).all()
        
        for status, count in statuses:
            print(f"  - {status}: {count}")
        
        # Derniers emails
        print("\n📬 5 derniers emails:")
        recent_emails = db.query(Email).order_by(Email.created_at.desc()).limit(5).all()
        for email in recent_emails:
            print(f"\n  📧 ID: {email.id}")
            print(f"     À: {email.recipient_email}")
            print(f"     Sujet: {email.subject}")
            print(f"     Statut: {email.status}")
            print(f"     Date création: {email.created_at}")
            print(f"     Date envoi: {email.sent_at}")
            print(f"     Tenant ID: {email.tenant_id}")
        
        print("\n" + "=" * 60)
        print("💡 INSTRUCTIONS:")
        print("1. Envoyez des bulletins depuis l'interface client")
        print("2. Relancez ce script pour voir les nouveaux emails")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_emails_before_and_after()


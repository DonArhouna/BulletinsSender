from app.db.session import SessionLocal
from app.modules.emails.models import Email
from app.modules.users.models import User
from app.modules.sends.models import Send
from datetime import datetime, timedelta
import random

def main():
    db = SessionLocal()
    try:
        print("=== CRÉATION DE DONNÉES DE TEST ===")
        
        # Récupérer les utilisateurs existants
        users = db.query(User).all()
        if not users:
            print("Aucun utilisateur trouvé")
            return
            
        # Récupérer le tenant_id (tous les users ont maintenant le même tenant_id)
        tenant_id = users[0].tenant_id
        print(f"Tenant ID utilisé: {tenant_id}")
        
        # Créer des emails de test pour les 30 derniers jours
        test_emails = []
        statuses = ["sent", "failed", "pending"]
        weights = [0.8, 0.15, 0.05]  # 80% sent, 15% failed, 5% pending
        
        # Générer des emails pour les 30 derniers jours
        for i in range(50):  # 50 emails de test
            # Date aléatoire dans les 30 derniers jours
            days_ago = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # Utilisateur aléatoire comme expéditeur
            sender_user = random.choice(users)
            
            # Email de destinataire fictif
            recipient_emails = [
                "employe1@entreprise.com", "employe2@entreprise.com", "employe3@entreprise.com",
                "marie.dupont@entreprise.com", "jean.martin@entreprise.com", "sophie.bernard@entreprise.com",
                "pierre.durand@entreprise.com", "claire.moreau@entreprise.com", "antoine.petit@entreprise.com",
                "isabelle.roux@entreprise.com"
            ]
            recipient_email = random.choice(recipient_emails)
            
            # Statut aléatoire avec pondération
            status = random.choices(statuses, weights=weights)[0]
            
            email = Email(
                subject=f"Bulletin de salaire - {created_at.strftime('%B %Y')}",
                body="Veuillez trouver ci-joint votre bulletin de salaire.",
                recipient_email=recipient_email,
                sender_email=sender_user.email,
                status=status,
                tenant_id=tenant_id,
                created_at=created_at,
                updated_at=created_at
            )
            test_emails.append(email)
        
        # Ajouter tous les emails à la base
        db.add_all(test_emails)
        db.commit()
        
        print(f"✅ Créé {len(test_emails)} emails de test")
        
        # Vérifier les statistiques
        total = db.query(Email).count()
        sent = db.query(Email).filter(Email.status == "sent").count()
        failed = db.query(Email).filter(Email.status == "failed").count()
        pending = db.query(Email).filter(Email.status == "pending").count()
        
        print(f"\n=== STATISTIQUES APRÈS CRÉATION ===")
        print(f"Total emails: {total}")
        print(f"Envoyés: {sent}")
        print(f"Échoués: {failed}")
        print(f"En attente: {pending}")
        print(f"Taux de succès: {(sent/total*100):.1f}%")
        
    except Exception as e:
        print(f"Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    main()
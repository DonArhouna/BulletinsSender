"""
Script pour vérifier les données dans PostgreSQL
"""
from app.db.session import SessionLocal
from app.modules.emails.models import Email
from app.modules.users.models import User, Tenant
from sqlalchemy import func

def check_database():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("VÉRIFICATION DE LA BASE DE DONNÉES POSTGRESQL")
        print("=" * 60)
        
        # Vérifier les tenants
        tenant_count = db.query(Tenant).count()
        print(f"\n📊 Tenants: {tenant_count}")
        if tenant_count > 0:
            tenants = db.query(Tenant).all()
            for tenant in tenants:
                print(f"  - {tenant.name} (ID: {tenant.id}, Domain: {tenant.domain})")
        
        # Vérifier les utilisateurs
        user_count = db.query(User).count()
        print(f"\n👤 Utilisateurs: {user_count}")
        if user_count > 0:
            users = db.query(User).limit(5).all()
            for user in users:
                print(f"  - {user.email} (Tenant ID: {user.tenant_id})")
        
        # Vérifier les emails
        email_count = db.query(Email).count()
        print(f"\n📧 Emails totaux: {email_count}")
        
        if email_count > 0:
            # Statistiques par statut
            print("\n📈 Statistiques par statut:")
            statuses = db.query(
                Email.status,
                func.count(Email.id).label('count')
            ).group_by(Email.status).all()
            
            for status, count in statuses:
                print(f"  - {status}: {count}")
            
            # Derniers emails
            print("\n📬 Derniers 5 emails:")
            recent_emails = db.query(Email).order_by(Email.created_at.desc()).limit(5).all()
            for email in recent_emails:
                print(f"  - À: {email.recipient_email}")
                print(f"    Sujet: {email.subject}")
                print(f"    Statut: {email.status}")
                print(f"    Date: {email.created_at}")
                print(f"    Tenant ID: {email.tenant_id}")
                print()
            
            # Groupement par mois (comme dans l'API)
            print("\n📅 Historique par période:")
            from sqlalchemy import case
            
            period_expr = func.date_trunc('month', Email.created_at)
            results = (
                db.query(
                    period_expr.label('period'),
                    func.count(Email.id).label('total_count'),
                    func.sum(
                        case(
                            (Email.status.in_(['sent', 'success']), 1),
                            else_=0
                        )
                    ).label('sent_count'),
                    func.sum(
                        case(
                            (Email.status.in_(['failed', 'error']), 1),
                            else_=0
                        )
                    ).label('failed_count'),
                    func.max(Email.created_at).label('latest_date')
                )
                .group_by(period_expr)
                .order_by(period_expr.desc())
                .limit(5)
                .all()
            )
            
            for result in results:
                latest_date = result.latest_date
                month_names = {
                    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
                    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
                    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
                }
                period_name = f"{month_names[latest_date.month]} {latest_date.year}"
                print(f"  - {period_name}")
                print(f"    Total: {result.total_count}")
                print(f"    Envoyés: {result.sent_count}")
                print(f"    Échoués: {result.failed_count}")
                print(f"    Dernière activité: {latest_date.strftime('%d/%m/%Y à %H:%M')}")
                print()
        else:
            print("\n⚠️  Aucun email dans la base de données")
            print("   Essayez d'envoyer des bulletins depuis l'interface client")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_database()


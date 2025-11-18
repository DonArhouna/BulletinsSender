from app.db.session import SessionLocal
from app.modules.emails.models import Email
from app.modules.users.models import User
from app.modules.sends.models import Send
from app.modules.users import crud as users_crud

def main():
    db = SessionLocal()
    try:
        print("=== ÉTAT ACTUEL DE LA BASE DE DONNÉES ===")

        # Check users and tenants
        users = db.query(User).all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  User {user.id}: {user.email}, tenant_id: {user.tenant_id}, is_superuser: {user.is_superuser}")

        # Check if there are any emails
        total_emails = db.query(Email).count()
        print(f"\nTotal emails: {total_emails}")

        if total_emails == 0:
            print("[X] Aucun email dans la base - les bulletins n'ont pas encore été envoyés")

        # Check sends
        sends = db.query(Send).all()
        print(f"\nTotal sends: {len(sends)}")
        for send in sends:
            print(f"  Send {send.id}: User {send.user_id}, Nb bulletins: {send.nb_bulletins}, Status: {send.status}, Created: {send.created_at}")

        # CORRECTION: Créer un tenant par défaut puis assigner des tenant_ids
        print("\n=== CORRECTION DES TENANTS ===")

        # Vérifier s'il existe déjà des tenants avec SQLAlchemy text
        from sqlalchemy import text
        result = db.execute(text("SELECT id, domain FROM tenant"))
        existing_tenants = result.fetchall()
        print(f"Tenants existants: {len(existing_tenants)}")
        for tenant in existing_tenants:
            print(f"  Tenant {tenant[0]}: {tenant[1]}")

        if not existing_tenants:
            # Créer un tenant par défaut avec SQL direct
            db.execute(text("INSERT INTO tenant (name, domain, created_at, updated_at) VALUES ('Default Tenant', 'default', NOW(), NOW())"))
            db.commit()
            # Récupérer l'ID du tenant créé
            result = db.execute(text("SELECT id FROM tenant WHERE domain = 'default'"))
            tenant_row = result.fetchone()
            default_tenant_id = tenant_row[0] if tenant_row else 1
            print(f"[OK] Créé tenant par défaut: ID {default_tenant_id}, domaine 'default'")
        else:
            default_tenant_id = existing_tenants[0][0]

        # Assigner le tenant aux utilisateurs sans tenant_id
        users_without_tenant = db.query(User).filter(User.tenant_id.is_(None)).all()
        if users_without_tenant:
            print(f"Utilisateurs sans tenant_id trouvés: {len(users_without_tenant)}")
            for user in users_without_tenant:
                users_crud.user.update(db, db_obj=user, obj_in={"tenant_id": default_tenant_id})
                print(f"  [OK] Assigné tenant_id={default_tenant_id} à user {user.id} ({user.email})")
        else:
            print("Tous les utilisateurs ont un tenant_id valide")

        # Vérifier si on peut simuler des emails pour les tests
        print("\n=== VÉRIFICATION APRÈS CORRECTIONS ===")
        users_after = db.query(User).all()
        for user in users_after:
            print(f"  User {user.id}: tenant_id: {user.tenant_id}")

    finally:
        db.close()

if __name__ == '__main__':
    main()

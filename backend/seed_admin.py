from app.db.session import SessionLocal
from app.modules.users import crud, schemas

def seed_admin():
    db = SessionLocal()
    try:
        user = crud.user.get_by_email(db, email="admin@admin.com")
        if not user:
            user_in = schemas.UserCreate(
                email="admin@admin.com",
                password="admin123",
                full_name="Super Admin",
                is_superuser=True
            )
            crud.user.create(db, obj_in=user_in)
            print("Super admin créé avec succès")
        else:
            print("Super admin existe déjà")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()

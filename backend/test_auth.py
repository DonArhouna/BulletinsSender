from app.db.session import SessionLocal
from app.modules.users import crud

db = SessionLocal()
user = crud.user.authenticate(db, email_or_username='admin@admin.com', password='admin123')
print('Auth result:', user is not None)
if user:
    print('User:', user.email)
db.close()

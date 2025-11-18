from app.db.session import engine
from app.db.base import Base
Base.metadata.create_all(bind=engine)
from app.modules.users import crud, models
from sqlalchemy.orm import Session

session = Session(engine)
user = crud.user.get_by_email_or_username(session, email_or_username='awone@h-tsoft.com')
print('User:', user)
print('Has first_login attr:', hasattr(user, 'first_login'))
if hasattr(user, 'first_login'):
    print('First login:', user.first_login)
session.close()

from app.db import base  # ensure all models are imported and mappers configured
from app.db.session import SessionLocal
from app.modules.sends import models


if __name__ == '__main__':
    db = SessionLocal()
    try:
        total = db.query(models.Send).count()
        print('COUNT:', total)
        rows = db.query(models.Send).order_by(models.Send.created_at.desc()).limit(10).all()
        for s in rows:
            print(s.id, s.user_id, s.nb_bulletins, s.total_amount, s.invoice_path, s.created_at)
    except Exception as e:
        print('ERROR:', e)
    finally:
        db.close()

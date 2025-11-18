from app.db import base
from app.db.session import SessionLocal
from app.modules.sends import crud as sends_crud, models as sends_models


def main():
    db = SessionLocal()
    try:
        sends = db.query(sends_models.Send).order_by(sends_models.Send.created_at.asc()).all()
        print('Found', len(sends), 'sends')
        updated = 0
        errors = 0
        for s in sends:
            try:
                old_price = s.price_per_bulletin
                old_total = s.total_amount
                s2 = sends_crud.send.recompute_totals(db, s)
                if s2.price_per_bulletin != old_price or s2.total_amount != old_total:
                    print(f'Updated Send {s.id}: {old_price}->{s2.price_per_bulletin}, {old_total}->{s2.total_amount}')
                    updated += 1
            except Exception as e:
                print('Failed to recalc for send', s.id, 'error:', e)
                errors += 1
        print('Done. updated:', updated, 'errors:', errors)
    finally:
        db.close()

if __name__ == '__main__':
    main()

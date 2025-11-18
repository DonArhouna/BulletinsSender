from app.db import base
from app.db.session import SessionLocal
from app.modules.emails import models as email_models
from app.modules.users import models as user_models
from app.modules.sends import crud as sends_crud
from datetime import datetime
from collections import defaultdict


def truncate_min(dt: datetime):
    return dt.replace(second=0, microsecond=0)


def main():
    db = SessionLocal()
    try:
        emails = db.query(email_models.Email).order_by(email_models.Email.created_at.asc()).all()
        print('Found', len(emails), 'emails')
        groups = defaultdict(list)
        for e in emails:
            if not e.created_at:
                key_time = None
            else:
                key_time = truncate_min(e.created_at)
            key = (e.tenant_id, e.sender_email, key_time)
            groups[key].append(e)

        created = 0
        skipped = 0
        for (tenant_id, sender_email, minute), group in groups.items():
            nb = len(group)
            # Skip tiny groups (like single test emails) if you want - but we'll create all
            # Find user by sender_email in same tenant
            user = None
            if sender_email:
                user = db.query(user_models.User).filter(user_models.User.email == sender_email, user_models.User.tenant_id == tenant_id).first()
            if not user:
                # fallback: any user in tenant
                user = db.query(user_models.User).filter(user_models.User.tenant_id == tenant_id).first()
            if not user:
                print('No user found for tenant', tenant_id, 'skipping group', sender_email, minute)
                skipped += 1
                continue
            try:
                send_in = type('X',(object,),{'nb_bulletins': nb, 'user_subscription_id': None, 'pricing_plan_id': None})()
                s_obj = sends_crud.send.create(db, obj_in=send_in, user_id=user.id, tenant_id=tenant_id)
                created += 1
                print('Created Send', s_obj.id, 'for user', user.email, 'nb', nb)
            except Exception as e:
                print('Failed to create send for', sender_email, minute, 'error:', e)
                skipped += 1

        print('Done. created:', created, 'skipped:', skipped)
    finally:
        db.close()

if __name__ == '__main__':
    main()

from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.modules.emails import models, schemas


class CRUDEmail:
    def get(self, db: Session, id: int) -> Optional[models.Email]:
        return db.query(models.Email).filter(models.Email.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, tenant_id: Optional[int] = None
    ) -> list[models.Email]:
        query = db.query(models.Email)
        if tenant_id is not None:
            query = query.filter(models.Email.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: schemas.EmailCreate, tenant_id: Optional[int] = None) -> models.Email:
        db_obj = models.Email(
            subject=obj_in.subject,
            body=obj_in.body,
            recipient_email=obj_in.recipient_email,
            sender_email=obj_in.sender_email,
            tenant_id=tenant_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: models.Email, obj_in: Union[Dict[str, Any], models.Email]
    ) -> models.Email:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.__dict__
        for field in update_data:
            if hasattr(db_obj, field) and field != '_sa_instance_state':
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.Email:
        obj = db.query(models.Email).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def create_bulk(self, db: Session, *, bulk_email: schemas.BulkEmailCreate, tenant_id: Optional[int] = None) -> List[models.Email]:
        emails = []
        for recipient_email in bulk_email.recipient_emails:
            email_obj = models.Email(
                subject=bulk_email.subject,
                body=bulk_email.body,
                recipient_email=recipient_email,
                sender_email=bulk_email.sender_email,
                tenant_id=tenant_id,
            )
            db.add(email_obj)
            emails.append(email_obj)
        db.commit()
        for email in emails:
            db.refresh(email)
        return emails


email = CRUDEmail()

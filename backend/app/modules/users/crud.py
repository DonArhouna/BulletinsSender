from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.core.security import get_password_hash, verify_password
from app.modules.users import models, schemas
from app.modules.subscriptions import crud as subscription_crud


class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.email == email).first()

    def get_by_email_or_username(self, db: Session, *, email_or_username: str) -> Optional[models.User]:
        return db.query(models.User).filter(
            or_(models.User.email == email_or_username, models.User.username == email_or_username)
        ).first()

    def get_by_email_and_tenant(self, db: Session, *, email: str, tenant_id: int) -> Optional[models.User]:
        return db.query(models.User).filter(
            and_(models.User.email == email, models.User.tenant_id == tenant_id)
        ).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, tenant_id: Optional[int] = None
    ) -> list[models.User]:
        query = db.query(models.User)
        if tenant_id is not None:
            query = query.filter(models.User.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: schemas.UserCreate, tenant_id: Optional[int] = None) -> models.User:
        from sqlalchemy import func
        # Determine pricing_plan automatically if subscription_plan_id provided
        subscription_id = getattr(obj_in, 'subscription_plan_id', None)
        pricing_id = getattr(obj_in, 'pricing_plan_id', None)
        if subscription_id and not pricing_id:
            sub = subscription_crud.subscription_plan.get(db, subscription_id)
            if sub:
                pricing_id = getattr(sub, 'pricing_plan_id', None)

        db_obj = models.User(
            email=obj_in.email,
            username=getattr(obj_in, 'username', None),
            hashed_password=get_password_hash(obj_in.password),
            full_name=getattr(obj_in, 'full_name', None),
            company=getattr(obj_in, 'company', None),
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
            tenant_id=tenant_id,
            subscription_plan_id=subscription_id,
            pricing_plan_id=pricing_id,
            updated_at=func.now(),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: models.User, obj_in: Union[schemas.UserUpdate, Dict[str, Any]]
    ) -> models.User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        # If subscription_plan_id is changed, update pricing_plan_id to follow subscription's pricing
        if update_data.get("subscription_plan_id") is not None:
            sub = subscription_crud.subscription_plan.get(db, update_data.get("subscription_plan_id"))
            if sub:
                update_data["pricing_plan_id"] = getattr(sub, 'pricing_plan_id', None)

        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.User:
        obj = db.query(models.User).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def authenticate(self, db: Session, *, email_or_username: str, password: str) -> Optional[models.User]:
        user = self.get_by_email_or_username(db, email_or_username=email_or_username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: models.User) -> bool:
        return user.is_active

    def is_superuser(self, user: models.User) -> bool:
        return user.is_superuser


class CRUDTenant:
    def get(self, db: Session, id: int) -> Optional[models.Tenant]:
        return db.query(models.Tenant).filter(models.Tenant.id == id).first()

    def get_by_domain(self, db: Session, *, domain: str) -> Optional[models.Tenant]:
        return db.query(models.Tenant).filter(models.Tenant.domain == domain).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[models.Tenant]:
        return db.query(models.Tenant).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: schemas.TenantCreate) -> models.Tenant:
        db_obj = models.Tenant(
            name=obj_in.name,
            domain=obj_in.domain,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: models.Tenant, obj_in: Union[schemas.TenantUpdate, Dict[str, Any]]
    ) -> models.Tenant:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.Tenant:
        obj = db.query(models.Tenant).get(id)
        db.delete(obj)
        db.commit()
        return obj


user = CRUDUser()
tenant = CRUDTenant()

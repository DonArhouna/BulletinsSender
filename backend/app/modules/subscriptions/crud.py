from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.modules.subscriptions import models, schemas


class CRUDSubscriptionPlan:
    def get(self, db: Session, id: int) -> Optional[models.SubscriptionPlan]:
        return db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.id == id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[models.SubscriptionPlan]:
        return db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == name).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[models.SubscriptionPlan]:
        q = db.query(models.SubscriptionPlan)
        if active_only:
            q = q.filter(models.SubscriptionPlan.is_active == True)
        return q.order_by(models.SubscriptionPlan.duration_months.asc()).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: schemas.SubscriptionPlanCreate) -> models.SubscriptionPlan:
        db_obj = models.SubscriptionPlan(
            name=obj_in.name,
            duration_months=obj_in.duration_months,
            is_active=obj_in.is_active,
            pricing_plan_id=getattr(obj_in, 'pricing_plan_id', None),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: models.SubscriptionPlan, obj_in: Union[schemas.SubscriptionPlanUpdate, Dict[str, Any]]) -> models.SubscriptionPlan:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.SubscriptionPlan:
        obj = db.query(models.SubscriptionPlan).get(id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDPricingPlan:
    def get(self, db: Session, id: int) -> Optional[models.PricingPlan]:
        return db.query(models.PricingPlan).filter(models.PricingPlan.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[models.PricingPlan]:
        q = db.query(models.PricingPlan)
        if active_only:
            q = q.filter(models.PricingPlan.is_active == True)
        return q.order_by(models.PricingPlan.id.asc()).offset(skip).limit(limit).all()

    def get_by_sub_plan(self, db: Session, subscription_plan_id: int) -> List[models.PricingPlan]:
        # Return pricing plans that historically reference the given subscription_plan_id
        return db.query(models.PricingPlan).filter(models.PricingPlan.subscription_plan_id == subscription_plan_id).all()

    def create(self, db: Session, *, obj_in: schemas.PricingPlanCreate) -> models.PricingPlan:
        db_obj = models.PricingPlan(
            subscription_plan_id=obj_in.subscription_plan_id,
            price_per_bulletin=obj_in.price_per_bulletin,
            currency=obj_in.currency,
            is_active=obj_in.is_active,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: models.PricingPlan, obj_in: Union[schemas.PricingPlanUpdate, Dict[str, Any]]) -> models.PricingPlan:
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> models.PricingPlan:
        obj = db.query(models.PricingPlan).get(id)
        db.delete(obj)
        db.commit()
        return obj


subscription_plan = CRUDSubscriptionPlan()
pricing_plan = CRUDPricingPlan()
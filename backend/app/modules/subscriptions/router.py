from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import deps
from app.modules.subscriptions import crud, schemas, models
from app.modules.users import models as user_models
from pydantic import BaseModel

router = APIRouter()


@router.get("/subscriptions/plans", response_model=list[schemas.SubscriptionPlan])
def list_subscription_plans(
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_superuser),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> Any:
    return crud.subscription_plan.get_multi(db, skip=skip, limit=limit, active_only=active_only)


@router.post("/subscriptions/plans", response_model=schemas.SubscriptionPlan)
def create_subscription_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.SubscriptionPlanCreate,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    if crud.subscription_plan.get_by_name(db, plan_in.name):
        raise HTTPException(status_code=400, detail="Un abonnement avec ce nom existe déjà")
    # If a pricing_plan_id was provided, ensure it exists
    if getattr(plan_in, 'pricing_plan_id', None) is not None:
        if not crud.pricing_plan.get(db, plan_in.pricing_plan_id):
            raise HTTPException(status_code=404, detail="Forfait associé introuvable")
    return crud.subscription_plan.create(db, obj_in=plan_in)


@router.put("/subscriptions/plans/{plan_id}", response_model=schemas.SubscriptionPlan)
def update_subscription_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: schemas.SubscriptionPlanUpdate,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    plan = crud.subscription_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return crud.subscription_plan.update(db, db_obj=plan, obj_in=plan_in)


@router.get("/pricing/plans", response_model=list[schemas.PricingPlan])
def list_pricing_plans(
    db: Session = Depends(deps.get_db),
    current_user: user_models.User = Depends(deps.get_current_superuser),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> Any:
    return crud.pricing_plan.get_multi(db, skip=skip, limit=limit, active_only=active_only)


@router.post("/pricing/plans", response_model=schemas.PricingPlan)
def create_pricing_plan(
    *,
    db: Session = Depends(deps.get_db),
    pricing_in: schemas.PricingPlanCreate,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    # Creating a Forfait (PricingPlan) does not require selecting an Abonnement.
    # Keep backward compatibility: if subscription_plan_id is provided, ensure it exists.
    if getattr(pricing_in, 'subscription_plan_id', None) is not None:
        if not crud.subscription_plan.get(db, pricing_in.subscription_plan_id):
            raise HTTPException(status_code=404, detail="Abonnement associé introuvable")
    return crud.pricing_plan.create(db, obj_in=pricing_in)


@router.put("/pricing/plans/{pricing_id}", response_model=schemas.PricingPlan)
def update_pricing_plan(
    *,
    db: Session = Depends(deps.get_db),
    pricing_id: int,
    pricing_in: schemas.PricingPlanUpdate,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    pricing = crud.pricing_plan.get(db, pricing_id)
    if not pricing:
        raise HTTPException(status_code=404, detail="Forfait introuvable")
    return crud.pricing_plan.update(db, db_obj=pricing, obj_in=pricing_in)


@router.get("/subscriptions/plans/{plan_id}", response_model=schemas.SubscriptionPlan)
def get_subscription_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    plan = crud.subscription_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return plan


@router.get("/pricing/plans/{pricing_id}", response_model=schemas.PricingPlan)
def get_pricing_plan(
    *,
    db: Session = Depends(deps.get_db),
    pricing_id: int,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    pricing = crud.pricing_plan.get(db, pricing_id)
    if not pricing:
        raise HTTPException(status_code=404, detail="Forfait introuvable")
    return pricing


class AssignRequest(BaseModel):
    user_id: int
    subscription_plan_id: int
    pricing_plan_id: int


@router.post("/subscriptions/assign")
def assign_subscription_to_user(
    *,
    db: Session = Depends(deps.get_db),
    payload: AssignRequest,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    user = db.query(user_models.User).filter(user_models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    sub = crud.subscription_plan.get(db, payload.subscription_plan_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    # If pricing_plan_id provided, validate it; otherwise derive from subscription
    if getattr(payload, 'pricing_plan_id', None) is not None:
        if not crud.pricing_plan.get(db, payload.pricing_plan_id):
            raise HTTPException(status_code=404, detail="Forfait introuvable")
        user.pricing_plan_id = payload.pricing_plan_id
    else:
        user.pricing_plan_id = getattr(sub, 'pricing_plan_id', None)
    user.subscription_plan_id = payload.subscription_plan_id
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"status": "ok"}


@router.delete("/pricing/plans/{pricing_id}")
def delete_pricing_plan(
    *,
    db: Session = Depends(deps.get_db),
    pricing_id: int,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    pricing = crud.pricing_plan.get(db, pricing_id)
    if not pricing:
        raise HTTPException(status_code=404, detail="Forfait introuvable")

    # Instead of preventing deletion, deactivate the pricing plan
    pricing.is_active = False
    db.add(pricing)
    db.commit()
    db.refresh(pricing)

    return {"status": "ok", "message": "Forfait désactivé"}


@router.delete("/subscriptions/plans/{plan_id}")
def delete_subscription_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: user_models.User = Depends(deps.get_current_superuser),
) -> Any:
    plan = crud.subscription_plan.get(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")

    # Instead of preventing deletion, deactivate the subscription plan
    plan.is_active = False
    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {"status": "ok", "message": "Abonnement désactivé"}
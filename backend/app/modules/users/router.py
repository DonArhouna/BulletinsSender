from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
import traceback
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import deps
from app.core import security
from app.core.config import settings
from app.modules.users import crud, models, schemas

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/auth/login", response_model=schemas.Token)
def login_access_token(
    login_data: schemas.LoginRequest = None,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        if login_data:
            email_or_username = login_data.email_or_username
            password = login_data.password
        else:
            email_or_username = form_data.username
            password = form_data.password
        user = crud.user.authenticate(
            db, email_or_username=email_or_username, password=password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password"
            )
        elif not crud.user.is_active(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token": security.create_access_token(
                user.id, expires_delta=access_token_expires
            ),
            "token_type": "bearer",
            "first_login": getattr(user, 'first_login', True),  # Indiquer si c'est la première connexion
        }
    except HTTPException:
        # Rethrow HTTPExceptions (validation/auth errors) so they are handled normally
        raise
    except Exception:
        # Log full traceback to a file for debugging, then return a controlled 500
        log_path = os.path.join(os.getcwd(), "debug_login_error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n--- Exception during /auth/login ---\n")
            traceback.print_exc(file=f)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/auth/register", response_model=schemas.User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.get("/auth/me", response_model=schemas.User)
def read_users_me(
    db: Session = Depends(deps.get_db), current_user: models.User = Depends(deps.get_current_user)
):
    """
    Get current user.
    """
    return current_user


@router.post("/auth/change-password")
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
    password_data: schemas.ChangePasswordRequest,
) -> Any:
    """
    Change current user's password.
    """
    # Pour la première connexion, on ne vérifie pas l'ancien mot de passe
    if not getattr(current_user, 'first_login', True):
        if not crud.user.authenticate(db, email_or_username=current_user.email, password=password_data.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

    # Mettre à jour le mot de passe et désactiver first_login
    crud.user.update(db, db_obj=current_user, obj_in={
        "password": password_data.new_password,
        "first_login": False
    })
    return {"msg": "Password updated successfully"}


@router.get("/users/", response_model=list[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve users.
    """
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/users/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user


@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = crud.user.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get("/users/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db, id=user_id)
    if user == current_user:
        return user
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Delete a user.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = crud.user.remove(db, id=user_id)
    return user


# Tenant endpoints
@router.get("/tenants/", response_model=list[schemas.Tenant])
def read_tenants(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Retrieve tenants.
    """
    tenants = crud.tenant.get_multi(db, skip=skip, limit=limit)
    return tenants


@router.post("/tenants/", response_model=schemas.Tenant)
def create_tenant(
    *,
    db: Session = Depends(deps.get_db),
    tenant_in: schemas.TenantCreate,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create new tenant.
    """
    tenant = crud.tenant.get_by_domain(db, domain=tenant_in.domain)
    if tenant:
        raise HTTPException(
            status_code=400,
            detail="The tenant with this domain already exists in the system",
        )
    tenant = crud.tenant.create(db, obj_in=tenant_in)
    return tenant


@router.get("/tenants/{tenant_id}", response_model=schemas.Tenant)
def read_tenant_by_id(
    tenant_id: int,
    current_user: models.User = Depends(deps.get_current_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific tenant by id.
    """
    tenant = crud.tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.put("/tenants/{tenant_id}", response_model=schemas.Tenant)
def update_tenant(
    *,
    db: Session = Depends(deps.get_db),
    tenant_id: int,
    tenant_in: schemas.TenantUpdate,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Update a tenant.
    """
    tenant = crud.tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="The tenant with this id does not exist in the system",
        )
    tenant = crud.tenant.update(db, db_obj=tenant, obj_in=tenant_in)
    return tenant


@router.delete("/tenants/{tenant_id}", response_model=schemas.Tenant)
def delete_tenant(
    *,
    db: Session = Depends(deps.get_db),
    tenant_id: int,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Delete a tenant.
    """
    tenant = crud.tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant = crud.tenant.remove(db, id=tenant_id)
    return tenant


@router.post("/users/{user_id}/block")
def block_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Block a user by setting is_active to False.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    if user.is_superuser:
        raise HTTPException(status_code=400, detail="Cannot block a superuser")

    crud.user.update(db, db_obj=user, obj_in={"is_active": False})
    return {"status": "ok", "message": "User blocked successfully"}


@router.post("/users/{user_id}/unblock")
def unblock_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Unblock a user by setting is_active to True.
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    crud.user.update(db, db_obj=user, obj_in={"is_active": True})
    return {"status": "ok", "message": "User unblocked successfully"}


@router.get("/users-stats")
def get_users_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Get statistics about users for super admin dashboard.
    Returns total users count and active employees count (unique email recipients).
    """
    from app.modules.emails import models as email_models
    from sqlalchemy import func, distinct

    # Total users count
    total_users = db.query(models.User).count()

    # Active employees count (unique recipients who received emails)
    active_employees = db.query(
        func.count(distinct(email_models.Email.recipient_email))
    ).filter(
        email_models.Email.status.in_(["sent", "success"])
    ).scalar() or 0

    return {
        "total_users": total_users,
        "active_employees": active_employees
    }


@router.get("/user-stats")
def get_user_stats(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get statistics about current user's activity for client dashboard.
    Returns total sent emails and unique recipients for the current user.
    """
    from app.modules.emails import models as email_models
    from sqlalchemy import func, distinct

    # Total emails sent by this user (through emails table)
    user_sent_emails = db.query(email_models.Email).filter(
        email_models.Email.sender_email == current_user.email,
        email_models.Email.status == "sent"
    ).count()

    # Unique recipients who received emails from this user
    unique_recipients = db.query(
        func.count(distinct(email_models.Email.recipient_email))
    ).filter(
        email_models.Email.sender_email == current_user.email,
        email_models.Email.status == "sent"
    ).scalar() or 0

    return {
        "total_users": 1,  # Current user
        "active_employees": unique_recipients
    }

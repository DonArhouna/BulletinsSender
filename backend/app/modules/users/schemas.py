from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    full_name: Optional[str] = None
    company: Optional[str] = None
    first_login: Optional[bool] = True


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str
    subscription_plan_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    subscription_plan_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional properties to return via API
class User(UserInDBBase):
    subscription_plan_id: Optional[int] = None
    pricing_plan_id: Optional[int] = None


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    first_login: Optional[bool] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    sub: Optional[str] = None


# Login schemas
class LoginRequest(BaseModel):
    email_or_username: str
    password: str


# Change password schemas
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# Tenant schemas
class TenantBase(BaseModel):
    name: str
    domain: str
    is_active: Optional[bool] = True


class TenantCreate(TenantBase):
    pass


class TenantUpdate(TenantBase):
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None


class Tenant(TenantBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

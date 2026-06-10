from typing import Literal, Optional

from pydantic import BaseModel, EmailStr

Plan = Literal["free", "starter", "brand", "studio"]


class User(BaseModel):
    id: str
    email: EmailStr
    plan: Plan = "free"
    created_at: str
    stripe_customer_id: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Subscription(BaseModel):
    user_id: str
    plan: Plan
    stripe_customer_id: Optional[str] = None

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.models.user import TokenResponse, UserLogin, UserRegister
from app.services import auth_service, email_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister, db: aiosqlite.Connection = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    user = await auth_service.register_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=409, detail="Email already registered")
    email_service.send_welcome(user["email"])
    return TokenResponse(access_token=auth_service.create_access_token(user["id"], user["email"]))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    user = await auth_service.authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=auth_service.create_access_token(user["id"], user["email"]))

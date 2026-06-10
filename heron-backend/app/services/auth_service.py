"""JWT creation/validation and password hashing."""

import uuid
from datetime import datetime, timedelta, timezone

import aiosqlite
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expires}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


async def register_user(db: aiosqlite.Connection, email: str, password: str) -> dict | None:
    """Create a user; returns the user row, or None if the email is taken."""
    cursor = await db.execute("SELECT id FROM users WHERE email = ?", (email,))
    if await cursor.fetchone() is not None:
        return None
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO users (id, email, password_hash, plan, created_at) VALUES (?, ?, ?, 'free', ?)",
        (user_id, email, hash_password(password), created_at),
    )
    await db.commit()
    return {"id": user_id, "email": email, "plan": "free", "created_at": created_at}


async def authenticate_user(db: aiosqlite.Connection, email: str, password: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = await cursor.fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


async def get_user_by_id(db: aiosqlite.Connection, user_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None

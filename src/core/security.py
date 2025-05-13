from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import settings

from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist
from models.user import User
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, role: str | None, jti: str | None = None):
    to_encode = {
        "sub": subject,
        "role": role,
        "jti": jti or str(uuid4()),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
        
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(email: str, password: str) -> User | None:
    """
    Verify email and password, update last_login, and return the User instance.
    Returns None if authentication fails.
    """
    try:
        user = await User.get(email=email)
    except DoesNotExist:
        return None

    if not verify_password(password, user.hashed_pw):
        return None

    user.last_login = datetime.utcnow()
    await user.save(update_fields=["last_login"])
    return user
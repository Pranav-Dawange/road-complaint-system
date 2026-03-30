import os
from datetime import datetime, timedelta
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import execute_query

load_dotenv()  # Reads .env if present; silently skips if file is missing


# ── JWT Configuration (loaded from .env with safe fallbacks) ────────────────
SECRET_KEY                  = os.getenv("SECRET_KEY", "road_complaint_secret_key_2025")
ALGORITHM                   = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Password hashing (bcrypt) ──────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 scheme — reads token from Authorization: Bearer <token> ─────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    Encodes: user_id, sub (username), role, exp (expiry).
    """
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    FastAPI dependency — decodes JWT and returns user info dict.
    Raises 401 if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id  = payload.get("user_id")
        username = payload.get("sub")
        role     = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"user_id": user_id, "username": username, "role": role}
    except JWTError:
        raise credentials_exception


def require_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory.
    Usage:  current_user = Depends(require_role(["officer", "admin"]))
    Raises 403 if the authenticated user's role is not in allowed_roles.
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Allowed roles: {allowed_roles}. Your role: {current_user['role']}"
            )
        return current_user
    return role_checker

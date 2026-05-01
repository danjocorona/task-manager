# auth.py
# Handles everything authentication related:
#   - Password hashing and verification with bcrypt
#   - JWT token creation on login
#   - JWT token decoding and current user extraction (FastAPI dependency)
 
from datetime import datetime, timedelta
from typing import Optional
 
import bcrypt, os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
 
from database import get_session
from models import User

# ────────────────── CONFIGURATION ─────────────────────────────

SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-fallback-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24   # Tokens expire after 24 hours

# ────────────────── PASSWORD HASHING ──────────────────────────

# Using bcrypt directly (no passlib) to avoid compatibility issues
# with passlib's outdated bcrypt integration.
 
def hash_password(plain_password: str) -> str:
    """
    Returns a bcrypt hash of the plain text password.
    bcrypt.gensalt() generates a random salt each time,
    so the same password produces a different hash every call.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")
 
 
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Returns True if the plain text password matches the stored hash.
    bcrypt.checkpw handles the salt extraction automatically.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes   = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)

# ──────────────────────── JWT Tokens ───────────────────────────

# Tells FastAPI where clients should send their token.
# The frontend will POST credentials to /auth/login and recieve a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT token containing the provided data payload.
    The token expires after ACCESS_TOKEN_EXPIRE_MINUTES by default.

    Args:
        data: Dictionary to encode - typically {"sub": username}
        expires_delta: Optional custom expiry duration

    Returns:
        Encoded JWT string to send to the client
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ────────────── CURRENT USER DEPENDENCY ─────────────────────────
 
def get_current_user(
    token:   str     = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    FastAPI dependency — decodes the JWT from the Authorization header,
    looks up the user in the database, and returns them.
 
    Raises HTTP 401 if the token is missing, invalid, expired, or the
    user no longer exists. Inject into any route that requires auth:
 
        def my_route(current_user: User = Depends(get_current_user)):
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
 
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
 
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
 
    return user
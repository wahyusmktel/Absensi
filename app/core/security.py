"""
Modul keamanan: hashing password dan pengelolaan JWT Token.
Memenuhi standar keamanan industri: bcrypt hashing dan JWT token.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Inisialisasi CryptContext dengan algoritma bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Memverifikasi kesesuaian password teks biasa dengan hash tersimpan.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Menghasilkan nilai hash aman dari password menggunakan bcrypt.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Membuat token JWT dengan subjek dan klaim tambahan.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Mendekode dan memvalidasi JWT token.
    Mengembalikan payload dictionary jika valid, atau None jika tidak valid/kadaluarsa.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

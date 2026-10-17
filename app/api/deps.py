"""
Modul Dependencies untuk FastAPI.
Menyediakan autentikasi JWT, ekstraksi pengguna aktif, dan otorisasi berbasis peran (RBAC).
"""

from typing import List, Optional
from uuid import UUID
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User, UserRole

# Skema OAuth2 Bearer token (opsional untuk API request)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_from_token(
    token: Optional[str],
    db: AsyncSession
) -> Optional[User]:
    """
    Fungsi bantuan untuk mengambil data pengguna dari database berdasarkan token JWT.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None

    # Query pengguna aktif
    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user


async def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency untuk mendapatkan pengguna yang sedang terautentikasi.
    Mendukung token via Authorization header (Bearer) dan Cookie (untuk web browser).
    """
    token = bearer_token or access_token_cookie

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan. Silakan login terlebih dahulu.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_from_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi login telah kadaluarsa atau tidak valid. Silakan login kembali.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory untuk otorisasi akses berdasarkan peran pengguna (RBAC).
    Mencegah akses yang tidak memiliki izin (Access Control Guard).
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki hak akses untuk tindakan ini.",
            )
        return current_user

    return role_checker

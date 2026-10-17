"""
Router API RESTful untuk Endpoint Autentikasi dan Registrasi.
Menyediakan integrasi via JSON API untuk klien mobile / frontend mandiri.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    LoginRequest,
    SchoolRegistrationRequest,
    SchoolResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


@router.post(
    "/register-school",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Registrasi Sekolah & Akun Operator Baru"
)
async def api_register_school(
    payload: SchoolRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Mendaftarkan profil sekolah baru sekaligus akun operator sekolah sebagai tenant terisolasi.
    """
    success, msg, school, operator = await AuthService.register_school_with_operator(db, payload)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {
        "success": True,
        "message": msg,
        "data": {
            "school": SchoolResponse.model_validate(school),
            "operator": UserResponse.model_validate(operator),
        }
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login Akun Pengguna"
)
async def api_login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Autentikasi kredensial pengguna dan mengembalikan JWT access token.
    """
    success, msg, user, token = await AuthService.authenticate_user(db, payload)
    if not success:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Ambil Informasi Akun Aktif"
)
async def api_me(
    current_user: User = Depends(get_current_user)
):
    """
    Mendapatkan detail profil akun pengguna yang sedang login.
    """
    return UserResponse.model_validate(current_user)

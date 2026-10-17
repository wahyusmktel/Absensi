"""
Schema Pydantic untuk validasi input dan output (DTO/Data Transfer Object).
Mencegah serangan injection dan memastikan validitas data.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.models import UserRole


# ---------------------------------------------------------
# Skema Data Sekolah (School)
# ---------------------------------------------------------

class SchoolBase(BaseModel):
    npsn: str = Field(..., min_length=8, max_length=20, description="Nomor Pokok Sekolah Nasional")
    name: str = Field(..., min_length=3, max_length=255, description="Nama Sekolah Lengkap")
    education_level: str = Field(default="SMP", max_length=50, description="Jenjang Pendidikan")
    address: Optional[str] = Field(default=None, description="Alamat Sekolah")
    phone: Optional[str] = Field(default=None, max_length=30, description="Nomor Telepon")
    email: Optional[EmailStr] = Field(default=None, description="Email Resmi Sekolah")


class SchoolCreate(SchoolBase):
    pass


class SchoolResponse(SchoolBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Skema Registrasi Sekolah Bersama Akun Operator
# ---------------------------------------------------------

class SchoolRegistrationRequest(BaseModel):
    """
    Formulir pendaftaran sekolah baru beserta akun Administrator / Operator Sekolah.
    """
    # Data Sekolah
    school_npsn: str = Field(..., min_length=8, max_length=20)
    school_name: str = Field(..., min_length=3, max_length=255)
    school_address: Optional[str] = None
    school_phone: Optional[str] = None
    school_email: Optional[EmailStr] = None

    # Data Akun Operator / Admin Sekolah
    operator_name: str = Field(..., min_length=3, max_length=255)
    operator_email: EmailStr
    operator_password: str = Field(..., min_length=8, max_length=100)
    operator_phone: Optional[str] = None
    operator_nip: Optional[str] = None


# ---------------------------------------------------------
# Skema Pengguna (User)
# ---------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=255)
    role: UserRole = UserRole.OPERATOR_SEKOLAH
    nip: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    school_id: Optional[UUID] = None


class UserResponse(UserBase):
    id: UUID
    school_id: Optional[UUID] = None
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Skema Autentikasi
# ---------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

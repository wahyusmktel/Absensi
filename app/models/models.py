"""
Model-model basis data relasional menggunakan SQLAlchemy.
Menerapkan UUID v4 untuk identifikasi unik yang aman dan anti enumerasi.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, Enum):
    """
    Daftar peran pengguna (Role-Based Access Control).
    """
    SUPERADMIN = "superadmin"
    OPERATOR_SEKOLAH = "operator_sekolah"
    KEPALA_SEKOLAH = "kepala_sekolah"
    GURU = "guru"
    SISWA = "siswa"


class School(Base):
    """
    Tabel data sekolah yang terdaftar dalam sistem multi-tenant.
    """
    __tablename__ = "schools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    npsn = Column(String(20), unique=True, index=True, nullable=False)  # Nomor Pokok Sekolah Nasional
    name = Column(String(255), nullable=False)                         # Nama Sekolah
    education_level = Column(String(50), default="SMP", nullable=False) # Jenjang (SMP/MTs)
    address = Column(Text, nullable=True)                              # Alamat Lengkap
    phone = Column(String(30), nullable=True)                          # No Telepon Sekolah
    email = Column(String(255), nullable=True)                         # Email Resmi Sekolah
    is_active = Column(Boolean, default=True, nullable=False)          # Status Aktif Sekolah

    # Timestamp audit trail
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relasi ke pengguna dan data sekolah
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")


class User(Base):
    """
    Tabel pengguna sistem dengan role-based access control.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Identitas & Autentikasi
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR_SEKOLAH, nullable=False, index=True)
    
    # Data Tambahan
    nip = Column(String(50), nullable=True, index=True)   # Nomor Induk Pegawai (untuk guru/kepsek/operator)
    phone = Column(String(30), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # Status Akun
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamp audit trail
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relasi
    school = relationship("School", back_populates="users")

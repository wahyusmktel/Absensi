"""
Layanan Autentikasi dan Registrasi Sekolah.
Menangani logika bisnis pendaftaran sekolah dan login multi-tenant.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.models import School, User, UserRole
from app.schemas.schemas import SchoolRegistrationRequest, LoginRequest


class AuthService:
    """
    Kelas layanan untuk autentikasi dan pendaftaran sekolah.
    """

    @staticmethod
    async def register_school_with_operator(
        db: AsyncSession,
        data: SchoolRegistrationRequest
    ) -> Tuple[bool, str, Optional[School], Optional[User]]:
        """
        Mendaftarkan sekolah baru beserta akun operator sekolah.
        Menggunakan transaksi basis data atomic untuk memastikan integritas data.
        """
        # 1. Validasi keunikan NPSN Sekolah
        npsn_check = await db.execute(select(School).where(School.npsn == data.school_npsn.strip()))
        if npsn_check.scalar_one_or_none():
            return False, f"NPSN '{data.school_npsn}' sudah terdaftar dalam sistem.", None, None

        # 2. Validasi keunikan Email Operator
        email_clean = data.operator_email.strip().lower()
        email_check = await db.execute(select(User).where(User.email == email_clean))
        if email_check.scalar_one_or_none():
            return False, f"Email operator '{email_clean}' sudah digunakan akun lain.", None, None

        try:
            # 3. Buat entitas Sekolah baru
            school = School(
                npsn=data.school_npsn.strip(),
                name=data.school_name.strip(),
                address=data.school_address.strip() if data.school_address else None,
                phone=data.school_phone.strip() if data.school_phone else None,
                email=data.school_email.strip().lower() if data.school_email else None,
                is_active=True
            )
            db.add(school)
            await db.flush()  # Dapatkan ID sekolah yang baru dibuat

            # 4. Buat entitas Operator Sekolah
            operator = User(
                school_id=school.id,
                email=email_clean,
                hashed_password=get_password_hash(data.operator_password),
                full_name=data.operator_name.strip(),
                role=UserRole.OPERATOR_SEKOLAH,
                phone=data.operator_phone.strip() if data.operator_phone else None,
                nip=data.operator_nip.strip() if data.operator_nip else None,
                is_active=True
            )
            db.add(operator)
            await db.commit()
            await db.refresh(school)
            await db.refresh(operator)

            return True, "Registrasi sekolah dan akun operator berhasil disimpan.", school, operator

        except Exception as e:
            await db.rollback()
            return False, f"Terjadi kesalahan saat memproses registrasi: {str(e)}", None, None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        data: LoginRequest
    ) -> Tuple[bool, str, Optional[User], Optional[str]]:
        """
        Memverifikasi kredensial pengguna dan menghasilkan JWT token.
        """
        email_clean = data.email.strip().lower()
        query = select(User).where(User.email == email_clean)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False, "Email atau password yang Anda masukkan salah.", None, None

        if not user.is_active:
            return False, "Akun Anda dinonaktifkan. Silakan hubungi administrator.", None, None

        if not verify_password(data.password, user.hashed_password):
            return False, "Email atau password yang Anda masukkan salah.", None, None

        # Perbarui waktu login terakhir
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()

        # Buat JWT access token dengan klaim peran dan ID sekolah
        token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "role": user.role.value,
                "school_id": str(user.school_id) if user.school_id else None,
                "email": user.email,
                "name": user.full_name
            }
        )

        return True, "Login berhasil.", user, token

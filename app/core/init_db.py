"""
Skrip Inisialisasi Database dan Akun Bawaan (Super Admin).
Membuat skema tabel secara otomatis dan memasukkan akun Super Administrator awal jika belum tersedia.
"""

from sqlalchemy import select
from app.core.config import settings
from app.core.database import async_engine, AsyncSessionLocal, Base
from app.core.security import get_password_hash
from app.models.models import User, UserRole


async def init_db():
    """
    Membuat semua tabel database PostgreSQL yang terdefinisi pada Base SQLAlchemy
    serta memasukkan akun Super Administrator awal dari konfigurasi .env.
    """
    # 1. Buat tabel jika belum ada
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Buat akun Super Admin jika belum ada
    async with AsyncSessionLocal() as session:
        query = select(User).where(User.email == settings.SUPERADMIN_EMAIL.lower())
        result = await session.execute(query)
        superadmin = result.scalar_one_or_none()

        if not superadmin:
            superadmin = User(
                email=settings.SUPERADMIN_EMAIL.lower(),
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                full_name=settings.SUPERADMIN_NAME,
                role=UserRole.SUPERADMIN,
                nip="000000000000000000",
                is_active=True
            )
            session.add(superadmin)
            await session.commit()
            print(f"[INIT DB] Super Admin berhasil dibuat: {settings.SUPERADMIN_EMAIL}")
        else:
            print(f"[INIT DB] Super Admin sudah tersedia: {settings.SUPERADMIN_EMAIL}")

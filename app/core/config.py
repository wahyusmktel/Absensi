"""
Konfigurasi aplikasi dan environment variable.
Memuat seluruh nilai dari file .env secara terpusat dan aman.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Kelas pengaturan utama aplikasi.
    Menggunakan pydantic-settings untuk validasi tipe data otomatis.
    """
    # Environment info
    ENV_MODE: str = "development"
    APP_NAME: str = "PresensiPintar"
    APP_DESCRIPTION: str = "Sistem Informasi Absensi Sekolah Menengah Pertama"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server binding
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # PostgreSQL Database
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "admin"
    DB_NAME: str = "absensi_smp_db"

    # Security & JWT
    SECRET_KEY: str = "rahasia-default-ubah-di-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 jam

    # Super Admin bawaan sistem
    SUPERADMIN_EMAIL: str = "superadmin@absensi.go.id"
    SUPERADMIN_PASSWORD: str = "SuperAdmin123!"
    SUPERADMIN_NAME: str = "Super Administrator"

    @property
    def async_database_url(self) -> str:
        """
        URL database asynchronous menggunakan driver asyncpg.
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_database_url(self) -> str:
        """
        URL database synchronous menggunakan driver psycopg2.
        """
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instance tunggal (singleton) untuk digunakan di seluruh aplikasi
settings = Settings()

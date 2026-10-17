"""
Pengujian otomatis untuk registrasi sekolah dan autentikasi login.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_home_redirect_to_login():
    """
    Memastikan root '/' mengarahkan ke halaman '/login'.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/", follow_redirects=False)
        assert response.status_code in [302, 307]
        assert "/login" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_login_page_renders_coreui():
    """
    Memastikan halaman login berhasil dirender dengan elemen CoreUI.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/login")
        assert response.status_code == 200
        assert "PresensiPintar" in response.text
        assert "Masuk ke Akun Anda" in response.text
        assert "/static/css/style.css" in response.text


@pytest.mark.asyncio
async def test_register_school_and_login_flow():
    """
    Menguji alur lengkap:
    1. Registrasi sekolah baru dan akun operator
    2. Login dengan akun operator yang baru didaftarkan
    3. Mengakses dashboard dengan session cookie
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique_suffix = uuid.uuid4().hex[:6]
        npsn = f"99{unique_suffix[:6]}"
        operator_email = f"operator_{unique_suffix}@smpn.sch.id"

        # 1. Registrasi Sekolah
        reg_payload = {
            "school_npsn": npsn,
            "school_name": f"SMP Negeri {unique_suffix.upper()}",
            "school_address": "Jl. Pendidikan Nasional No. 1",
            "school_phone": "021-123456",
            "school_email": f"info_{unique_suffix}@smpn.sch.id",
            "operator_name": "Operator Uji Coba",
            "operator_email": operator_email,
            "operator_password": "PasswordKuat123!",
            "operator_phone": "08123456789",
            "operator_nip": "199001012015011001",
        }
        reg_res = await ac.post("/register", data=reg_payload, follow_redirects=False)
        assert reg_res.status_code in [302, 303], f"Registrasi gagal: {reg_res.text}"
        assert "/login" in reg_res.headers.get("location", "")

        # 2. Login Operator
        login_res = await ac.post(
            "/login",
            data={
                "email": operator_email,
                "password": "PasswordKuat123!"
            },
            follow_redirects=False
        )
        assert login_res.status_code in [302, 303]
        assert "/dashboard" in login_res.headers.get("location", "")
        token = login_res.cookies.get("access_token")
        assert token is not None

        # 3. Akses Dashboard dengan Cookie
        dash_res = await ac.get("/dashboard", cookies={"access_token": token})
        assert dash_res.status_code == 200
        assert "Operator Uji Coba" in dash_res.text
        assert npsn in dash_res.text


@pytest.mark.asyncio
async def test_superadmin_login_and_view_schools():
    """
    Menguji login Super Admin bawaan sistem dan melihat daftar sekolah terdaftar.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login superadmin
        login_res = await ac.post(
            "/login",
            data={
                "email": settings.SUPERADMIN_EMAIL,
                "password": settings.SUPERADMIN_PASSWORD
            },
            follow_redirects=False
        )
        assert login_res.status_code in [302, 303]
        token = login_res.cookies.get("access_token")
        assert token is not None

        # Akses Data Sekolah
        schools_res = await ac.get("/schools", cookies={"access_token": token})
        assert schools_res.status_code == 200
        assert "Data Sekolah Terdaftar" in schools_res.text

"""
Pengujian fitur keamanan routing, URL bersih, proteksi sesi login ganda, dan halaman 404 kustom.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_invalid_url_renders_custom_404_page():
    """
    Memastikan URL yang tidak valid menampilkan halaman kustom 404 CoreUI dengan status 404.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/url-acak-tidak-ada-dalam-sistem-12345")
        assert res.status_code == 404
        assert "404" in res.text
        assert "Halaman Tidak Ditemukan" in res.text
        assert "PresensiPintar" in res.text
        assert "/dashboard" in res.text


@pytest.mark.asyncio
async def test_authenticated_user_cannot_revisit_login_page():
    """
    Memastikan pengguna yang sudah terotentikasi (memiliki access_token aktif)
    tidak dapat mengakses formulir login dan langsung dialihkan ke /dashboard.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login dengan Super Admin
        login_res = await ac.post(
            "/login",
            data={
                "email": settings.SUPERADMIN_EMAIL,
                "password": settings.SUPERADMIN_PASSWORD
            },
            follow_redirects=False
        )
        token = login_res.cookies.get("access_token")
        assert token is not None

        # Coba buka halaman login kembali saat sudah terautentikasi
        revisit_res = await ac.get("/login", cookies={"access_token": token}, follow_redirects=False)
        assert revisit_res.status_code in [302, 303, 307]
        assert revisit_res.headers.get("location") == "/dashboard"

        # Coba buka halaman register saat sudah terautentikasi
        register_revisit_res = await ac.get("/register", cookies={"access_token": token}, follow_redirects=False)
        assert register_revisit_res.status_code in [302, 303, 307]
        assert register_revisit_res.headers.get("location") == "/dashboard"


@pytest.mark.asyncio
async def test_logout_redirect_is_clean_without_query_params():
    """
    Memastikan proses logout menghasilkan URL bersih tanpa query string pesan (?success_msg=...).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        logout_res = await ac.get("/logout", follow_redirects=False)
        assert logout_res.status_code in [302, 303, 307]
        location = logout_res.headers.get("location", "")
        # Lokasi wajib tepat /login tanpa embel-embel query string pesan
        assert location == "/login"
        assert "?" not in location

"""
Router Web UI untuk Autentikasi, Registrasi Sekolah, dan Dashboard.
Render antarmuka pengguna berbasis template Jinja2 dan CoreUI.
"""

from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_from_token
from app.core.database import get_db
from app.models.models import School, User, UserRole
from app.schemas.schemas import SchoolRegistrationRequest, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Halaman pembuka: jika sudah login diarahkan ke dashboard, jika belum diarahkan ke login.
    """
    token = request.cookies.get("access_token")
    user = await get_current_user_from_token(token, db) if token else None
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# ---------------------------------------------------------
# Halaman Login
# ---------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Menampilkan formulir login akun.
    """
    token = request.cookies.get("access_token")
    if token:
        user = await get_current_user_from_token(token, db)
        if user:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "success_msg": success_msg,
            "error_msg": error_msg,
        }
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Memproses submit form login pengguna.
    Menyimpan JWT token ke HTTP-Only cookie untuk keamanan maksimal.
    """
    try:
        login_data = LoginRequest(email=email, password=password)
    except ValidationError:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "error_msg": "Format email atau kata sandi tidak valid.",
                "email": email,
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    success, msg, user, token = await AuthService.authenticate_user(db, login_data)

    if not success:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "error_msg": msg,
                "email": email,
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Buat respon pengalihan ke dashboard dan pasang HttpOnly cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,       # Mencegah pencurian token via serangan XSS
        secure=False,        # Ubah ke True di HTTPS production
        samesite="lax",      # Perlindungan terhadap serangan CSRF
        max_age=86400,       # 1 hari (24 jam)
    )
    return response


# ---------------------------------------------------------
# Halaman Registrasi Sekolah
# ---------------------------------------------------------

@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    error_msg: Optional[str] = None
):
    """
    Menampilkan formulir pendaftaran sekolah baru & akun operator.
    """
    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "error_msg": error_msg,
            "form": {}
        }
    )


@router.post("/register")
async def register_submit(
    request: Request,
    school_npsn: str = Form(...),
    school_name: str = Form(...),
    school_address: Optional[str] = Form(None),
    school_phone: Optional[str] = Form(None),
    school_email: Optional[str] = Form(None),
    operator_name: str = Form(...),
    operator_email: str = Form(...),
    operator_password: str = Form(...),
    operator_phone: Optional[str] = Form(None),
    operator_nip: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Memproses pendaftaran sekolah baru dan akun operator sekolah.
    """
    form_data = {
        "school_npsn": school_npsn,
        "school_name": school_name,
        "school_address": school_address,
        "school_phone": school_phone,
        "school_email": school_email,
        "operator_name": operator_name,
        "operator_email": operator_email,
        "operator_phone": operator_phone,
        "operator_nip": operator_nip,
    }

    try:
        reg_payload = SchoolRegistrationRequest(
            school_npsn=school_npsn,
            school_name=school_name,
            school_address=school_address if school_address else None,
            school_phone=school_phone if school_phone else None,
            school_email=school_email if school_email else None,
            operator_name=operator_name,
            operator_email=operator_email,
            operator_password=operator_password,
            operator_phone=operator_phone if operator_phone else None,
            operator_nip=operator_nip if operator_nip else None,
        )
    except ValidationError as ve:
        error_first = ve.errors()[0]["msg"]
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error_msg": f"Validasi gagal: {error_first}",
                "form": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    success, msg, school, operator = await AuthService.register_school_with_operator(db, reg_payload)

    if not success:
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "error_msg": msg,
                "form": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Berhasil mendaftar, arahkan ke halaman login dengan pesan sukses
    redirect_url = f"/login?success_msg=Sekolah+{school.name}+berhasil+didaftarkan.+Silakan+masuk+menggunakan+email+operator."
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# Halaman Dashboard
# ---------------------------------------------------------

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Menampilkan dasbor utama untuk pengguna yang telah terautentikasi.
    """
    token = request.cookies.get("access_token")
    user = await get_current_user_from_token(token, db) if token else None

    if not user:
        return RedirectResponse(
            url="/login?error_msg=Sesi+login+telah+berakhir.+Silakan+masuk+kembali.",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Ambil data sekolah jika user terafiliasi dengan suatu sekolah
    school = None
    if user.school_id:
        res = await db.execute(select(School).where(School.id == user.school_id))
        school = res.scalar_one_or_none()

    # Hitung total sekolah (untuk dashboard superadmin)
    total_schools_count = 0
    if user.role == UserRole.SUPERADMIN:
        count_res = await db.execute(select(func.count(School.id)))
        total_schools_count = count_res.scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "school": school,
            "total_schools": total_schools_count,
            "str": str,
        }
    )


# ---------------------------------------------------------
# Halaman Data Sekolah (Super Admin) - Paginasi 10 per halaman
# ---------------------------------------------------------

@router.get("/schools", response_class=HTMLResponse)
async def schools_list_page(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Menampilkan daftar semua sekolah terdaftar dengan paginasi 10 data per halaman.
    Khusus untuk role Super Admin.
    """
    token = request.cookies.get("access_token")
    user = await get_current_user_from_token(token, db) if token else None

    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if user.role != UserRole.SUPERADMIN:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    limit = 10
    if page < 1:
        page = 1
    offset = (page - 1) * limit

    # Query total record
    total_res = await db.execute(select(func.count(School.id)))
    total_count = total_res.scalar() or 0
    total_pages = ceil(total_count / limit) if total_count > 0 else 1

    # Query list sekolah
    schools_res = await db.execute(
        select(School).order_by(School.created_at.desc()).offset(offset).limit(limit)
    )
    schools = schools_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="schools/list.html",
        context={
            "user": user,
            "schools": schools,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "str": str,
            "range": range,
        }
    )


# ---------------------------------------------------------
# Logout
# ---------------------------------------------------------

@router.get("/logout")
async def logout():
    """
    Menghapus cookie sesi autentikasi dan mengarahkan kembali ke login.
    """
    response = RedirectResponse(
        url="/login?success_msg=Anda+telah+berhasil+keluar+dari+sistem.",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie(key="access_token")
    return response

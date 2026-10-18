"""
Router Web UI untuk Autentikasi, Registrasi Sekolah, Master Pendataan Awal, Jadwal Pelajaran, dan Guru Piket.
Render antarmuka pengguna berbasis template Jinja2 dan CoreUI + Font Awesome.
"""

from datetime import datetime, time
from math import ceil
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_from_token
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.models import (
    AcademicYear,
    AttendanceStatus,
    Classroom,
    DayOfWeek,
    DutyTeacher,
    Schedule,
    School,
    Student,
    Subject,
    Teacher,
    TeacherAttendance,
    User,
    UserRole,
)
from app.schemas.schemas import SchoolRegistrationRequest, LoginRequest
from app.services.academic_service import (
    AcademicYearService,
    ClassroomService,
    DutyTeacherService,
    ScheduleService,
    StudentService,
    SubjectService,
    TeacherService,
)
from app.services.attendance_service import AttendanceService
from app.services.auth_service import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Helper untuk memeriksa otorisasi login & tenant sekolah
async def _get_auth_context(request: Request, db: AsyncSession):
    token = request.cookies.get("access_token")
    if not token:
        return None, None
    user = await get_current_user_from_token(token, db)
    if not user:
        return None, None
    school = None
    if user.school_id:
        res = await db.execute(select(School).where(School.id == user.school_id))
        school = res.scalar_one_or_none()
    return user, school


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


# ---------------------------------------------------------
# AUTENTIKASI: Login, Register, Logout
# ---------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Halaman masuk (login).
    Jika pengguna sudah memiliki sesi login aktif, otomatis dialihkan ke /dashboard
    sehingga tidak dapat mengakses kembali formulir login.
    """
    user, _ = await _get_auth_context(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Jika sudah login, langsung alihkan ke dashboard
    user_check, _ = await _get_auth_context(request, db)
    if user_check:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

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

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Halaman registrasi sekolah.
    Jika pengguna sudah login, otomatis diarahkan ke /dashboard.
    """
    user, _ = await _get_auth_context(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
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

    # Bersih tanpa query parameter di URL
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout():
    """
    Keluar dari sistem secara bersih tanpa query string di URL.
    """
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie(key="access_token")
    return response


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = None
    today_date = datetime.now().date()
    today_dow = AttendanceService.get_today_day_of_week(today_date)
    today_day_name = today_dow.value if today_dow else "Minggu (Hari Libur)"

    context = {
        "user": user,
        "school": school,
        "active_academic_year": None,
        "active_menu": "dashboard",
        "today_day_name": today_day_name,
        "str": str,
    }

    # Data Khusus Super Admin
    if user.role == UserRole.SUPERADMIN:
        sc_res = await db.execute(select(func.count(School.id)).where(School.deleted_at.is_(None)))
        context["total_schools"] = sc_res.scalar() or 0

        tg_res = await db.execute(select(func.count(Teacher.id)).where(Teacher.deleted_at.is_(None)))
        context["total_teachers_global"] = tg_res.scalar() or 0

        stg_res = await db.execute(select(func.count(Student.id)).where(Student.deleted_at.is_(None)))
        context["total_students_global"] = stg_res.scalar() or 0

        atg_res = await db.execute(select(func.count(TeacherAttendance.id)).where(TeacherAttendance.deleted_at.is_(None)))
        context["total_attendances_global"] = atg_res.scalar() or 0

        return templates.TemplateResponse(request=request, name="dashboard.html", context=context)

    # Data untuk Pengguna di Sekolah (Operator, Kepala Sekolah, Guru, Siswa)
    if user.school_id:
        active_ay = await AcademicYearService.get_active(db, user.school_id)
        context["active_academic_year"] = active_ay
        ay_id = active_ay.id if active_ay else None

        # Data Kepala Sekolah
        if user.role == UserRole.KEPALA_SEKOLAH:
            stats = await AttendanceService.get_summary_stats(db, user.school_id, academic_year_id=ay_id, target_date=today_date)
            context["stats_today"] = stats

            # Guru piket hari ini
            if active_ay and today_dow:
                duties, _, _ = await DutyTeacherService.get_list(db, user.school_id, academic_year_id=active_ay.id, day_of_week=today_dow, limit=10)
                context["duty_teachers_today"] = duties
            else:
                context["duty_teachers_today"] = []

            # 5 Presensi terbaru hari ini
            rec_query = select(TeacherAttendance).options(
                selectinload(TeacherAttendance.teacher),
                selectinload(TeacherAttendance.schedule).selectinload(Schedule.classroom),
                selectinload(TeacherAttendance.schedule).selectinload(Schedule.subject)
            ).where(
                TeacherAttendance.school_id == user.school_id,
                TeacherAttendance.attendance_date == today_date,
                TeacherAttendance.deleted_at.is_(None)
            ).order_by(TeacherAttendance.created_at.desc()).limit(5)
            rec_res = await db.execute(rec_query)
            context["recent_attendances"] = rec_res.scalars().all()

        # Data Guru
        elif user.role == UserRole.GURU:
            curr_teacher = await AttendanceService.get_teacher_by_user_or_id(db, user.school_id, user)
            context["current_teacher"] = curr_teacher
            if curr_teacher and active_ay:
                schedules = await AttendanceService.get_schedules_for_attendance(
                    db, user.school_id, academic_year_id=active_ay.id, teacher_id=curr_teacher.id, target_date=today_date
                )
                context["teacher_today_schedules"] = schedules
            else:
                context["teacher_today_schedules"] = []

        # Data Siswa
        elif user.role == UserRole.SISWA:
            student = await StudentService.get_by_user_id(db, user.id)
            context["student"] = student
            if student and student.classroom_id and active_ay:
                student_classes = await AttendanceService.get_student_class_today(
                    db, user.school_id, classroom_id=student.classroom_id, academic_year_id=active_ay.id, target_date=today_date
                )
                context["student_today_classes"] = student_classes
            else:
                context["student_today_classes"] = []

            # Guru piket hari ini untuk siswa
            if active_ay and today_dow:
                duties, _, _ = await DutyTeacherService.get_list(db, user.school_id, academic_year_id=active_ay.id, day_of_week=today_dow, limit=10)
                context["duty_teachers_today"] = duties
            else:
                context["duty_teachers_today"] = []

        # Data Default / Operator Sekolah
        else:
            t_res = await db.execute(select(func.count(Teacher.id)).where(Teacher.school_id == user.school_id, Teacher.deleted_at.is_(None)))
            context["total_teachers"] = t_res.scalar() or 0

            st_res = await db.execute(select(func.count(Student.id)).where(Student.school_id == user.school_id, Student.deleted_at.is_(None)))
            context["total_students"] = st_res.scalar() or 0

            c_res = await db.execute(select(func.count(Classroom.id)).where(Classroom.school_id == user.school_id, Classroom.deleted_at.is_(None)))
            context["total_classrooms"] = c_res.scalar() or 0

            s_res = await db.execute(select(func.count(Subject.id)).where(Subject.school_id == user.school_id, Subject.deleted_at.is_(None)))
            context["total_subjects"] = s_res.scalar() or 0

            if active_ay:
                sch_res = await db.execute(select(func.count(Schedule.id)).where(
                    Schedule.school_id == user.school_id,
                    Schedule.academic_year_id == active_ay.id,
                    Schedule.deleted_at.is_(None)
                ))
                context["total_schedules"] = sch_res.scalar() or 0

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=context
    )


# ---------------------------------------------------------
# SUPER ADMIN: Data Sekolah
# ---------------------------------------------------------

@router.get("/schools", response_class=HTMLResponse)
async def schools_list_page(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or user.role != UserRole.SUPERADMIN:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    limit = 10
    if page < 1:
        page = 1
    offset = (page - 1) * limit

    total_res = await db.execute(select(func.count(School.id)).where(School.deleted_at.is_(None)))
    total_count = total_res.scalar() or 0
    total_pages = ceil(total_count / limit) if total_count > 0 else 1

    schools_res = await db.execute(
        select(School).where(School.deleted_at.is_(None)).order_by(School.created_at.desc()).offset(offset).limit(limit)
    )
    schools = schools_res.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="schools/list.html",
        context={
            "user": user,
            "school": school,
            "schools": schools,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "active_menu": "schools",
            "str": str,
            "range": range,
        }
    )


# ---------------------------------------------------------
# 1. DATA TAHUN PELAJARAN
# ---------------------------------------------------------

@router.get("/academic-years", response_class=HTMLResponse)
async def academic_years_page(
    request: Request,
    page: int = 1,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    years, total_count, total_pages = await AcademicYearService.get_list(db, user.school_id, page=page, limit=10)

    return templates.TemplateResponse(
        request=request,
        name="academic_years/list.html",
        context={
            "user": user,
            "school": school,
            "academic_years": years,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "academic_years",
            "str": str,
            "range": range,
        }
    )


@router.post("/academic-years")
async def academic_years_create(
    request: Request,
    name: str = Form(...),
    semester: str = Form(...),
    is_active: bool = Form(False),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    await AcademicYearService.create(
        db=db,
        school_id=user.school_id,
        name=name,
        semester=semester,
        is_active=is_active,
        start_date=s_date,
        end_date=e_date
    )
    return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/academic-years/{ay_id}/set-active")
async def academic_years_set_active(
    ay_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await AcademicYearService.set_active(db, user.school_id, ay_id)
    return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/academic-years/{ay_id}/delete")
async def academic_years_delete(
    ay_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await AcademicYearService.soft_delete(db, user.school_id, ay_id)
    return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# 2. DATA GURU
# ---------------------------------------------------------

@router.get("/teachers", response_class=HTMLResponse)
async def teachers_page(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    teachers, total_count, total_pages = await TeacherService.get_list(
        db, user.school_id, page=page, limit=10, search=search
    )

    return templates.TemplateResponse(
        request=request,
        name="teachers/list.html",
        context={
            "user": user,
            "school": school,
            "teachers": teachers,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "search": search or "",
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "teachers",
            "str": str,
            "range": range,
        }
    )


@router.post("/teachers")
async def teachers_create(
    request: Request,
    name: str = Form(...),
    nip: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    employment_status: Optional[str] = Form("PNS"),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await TeacherService.create(
        db=db,
        school_id=user.school_id,
        name=name,
        nip=nip,
        gender=gender,
        phone=phone,
        email=email,
        address=address,
        employment_status=employment_status
    )
    return RedirectResponse(url="/teachers", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/teachers/{teacher_id}/delete")
async def teachers_delete(
    teacher_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await TeacherService.soft_delete(db, user.school_id, teacher_id)
    return RedirectResponse(url="/teachers", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/teachers/sample-excel")
async def teachers_sample_excel():
    """
    Mengunduh berkas template Excel contoh untuk impor massal guru.
    """
    stream = TeacherService.generate_sample_excel()
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Template_Impor_Guru.xlsx"}
    )


@router.post("/teachers/import")
async def teachers_import_excel(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_bytes = await file.read()
    await TeacherService.import_from_excel(db, user.school_id, file_bytes)
    return RedirectResponse(url="/teachers", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/teachers/export-excel")
async def teachers_export_excel(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    school_name = school.name if school else "Sekolah"
    stream = await TeacherService.export_to_excel(db, user.school_id, school_name=school_name)
    filename = f"Data_Guru_{school_name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ---------------------------------------------------------
# 3. DATA MATA PELAJARAN
# ---------------------------------------------------------

@router.get("/subjects", response_class=HTMLResponse)
async def subjects_page(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    subjects, total_count, total_pages = await SubjectService.get_list(
        db, user.school_id, page=page, limit=10, search=search
    )

    return templates.TemplateResponse(
        request=request,
        name="subjects/list.html",
        context={
            "user": user,
            "school": school,
            "subjects": subjects,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "search": search or "",
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "subjects",
            "str": str,
            "range": range,
        }
    )


@router.post("/subjects")
async def subjects_create(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    grade_level: str = Form("Semua"),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await SubjectService.create(
        db=db,
        school_id=user.school_id,
        code=code,
        name=name,
        grade_level=grade_level,
        description=description
    )
    return RedirectResponse(url="/subjects", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/subjects/{subject_id}/delete")
async def subjects_delete(
    subject_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await SubjectService.soft_delete(db, user.school_id, subject_id)
    return RedirectResponse(url="/subjects", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# 4. DATA KELAS (Wali Kelas dari Guru)
# ---------------------------------------------------------

@router.get("/classrooms", response_class=HTMLResponse)
async def classrooms_page(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    ay_id = active_ay.id if active_ay else None

    classrooms, total_count, total_pages = await ClassroomService.get_list(
        db, user.school_id, academic_year_id=ay_id, page=page, limit=10, search=search
    )
    teachers_list = await TeacherService.get_all_active(db, user.school_id)

    return templates.TemplateResponse(
        request=request,
        name="classrooms/list.html",
        context={
            "user": user,
            "school": school,
            "classrooms": classrooms,
            "teachers_list": teachers_list,
            "active_ay": active_ay,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "search": search or "",
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "classrooms",
            "str": str,
            "range": range,
        }
    )


@router.post("/classrooms")
async def classrooms_create(
    request: Request,
    name: str = Form(...),
    grade_level: str = Form(...),
    homeroom_teacher_id: Optional[str] = Form(None),
    capacity: int = Form(32),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(
            url="/academic-years",
            status_code=status.HTTP_303_SEE_OTHER
        )

    wali_id = UUID(homeroom_teacher_id) if homeroom_teacher_id else None

    await ClassroomService.create(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        name=name,
        grade_level=grade_level,
        homeroom_teacher_id=wali_id,
        capacity=capacity
    )
    return RedirectResponse(url="/classrooms", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/classrooms/{classroom_id}/delete")
async def classrooms_delete(
    classroom_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await ClassroomService.soft_delete(db, user.school_id, classroom_id)
    return RedirectResponse(url="/classrooms", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# DATA SISWA (PESERTA DIDIK)
# ---------------------------------------------------------

@router.get("/students", response_class=HTMLResponse)
async def students_page(
    request: Request,
    page: int = 1,
    classroom_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    cid = UUID(classroom_id) if classroom_id else None
    students, total_count, total_pages = await StudentService.get_list(
        db, user.school_id, classroom_id=cid, page=page, limit=10, search=search
    )

    classrooms_list = await ClassroomService.get_all_active(db, user.school_id)

    return templates.TemplateResponse(
        request=request,
        name="students/list.html",
        context={
            "user": user,
            "school": school,
            "students": students,
            "classrooms_list": classrooms_list,
            "selected_class_id": classroom_id or "",
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "search": search or "",
            "active_menu": "students",
            "str": str,
            "range": range,
        }
    )


@router.post("/students")
async def students_create(
    request: Request,
    nisn: str = Form(...),
    name: str = Form(...),
    gender: str = Form("L"),
    classroom_id: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    nis: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    cid = UUID(classroom_id) if classroom_id else None
    await StudentService.create(
        db=db,
        school_id=user.school_id,
        classroom_id=cid,
        nisn=nisn,
        name=name,
        gender=gender,
        phone=phone,
        email=email,
        address=address,
        nis=nis
    )
    return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/students/{student_id}/delete")
async def students_delete(
    student_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await StudentService.soft_delete(db, user.school_id, student_id)
    return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/students/sample-excel")
async def students_sample_excel():
    """
    Mengunduh berkas template Excel contoh untuk impor massal siswa.
    """
    stream = StudentService.generate_sample_excel()
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Template_Impor_Siswa.xlsx"}
    )


@router.post("/students/import")
async def students_import_excel(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_bytes = await file.read()
    await StudentService.import_from_excel(db, user.school_id, file_bytes)
    return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/students/export-excel")
async def students_export_excel(
    request: Request,
    classroom_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    school_name = school.name if school else "Sekolah"
    cid = UUID(classroom_id) if classroom_id else None
    stream = await StudentService.export_to_excel(db, user.school_id, school_name=school_name, classroom_id=cid)
    filename = f"Data_Siswa_{school_name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ---------------------------------------------------------
# 5. JADWAL PELAJARAN (Atur Jadwal & Cetak)
# ---------------------------------------------------------

@router.get("/schedules", response_class=HTMLResponse)
async def schedules_page(
    request: Request,
    page: int = 1,
    classroom_id: Optional[str] = None,
    day_of_week: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(
            url="/academic-years",
            status_code=status.HTTP_303_SEE_OTHER
        )

    cid = UUID(classroom_id) if classroom_id else None
    dow = DayOfWeek(day_of_week) if day_of_week else None

    schedules, total_count, total_pages = await ScheduleService.get_list(
        db, user.school_id, academic_year_id=active_ay.id, classroom_id=cid, day_of_week=dow, page=page, limit=10
    )

    classrooms_list = await ClassroomService.get_all_active(db, user.school_id, academic_year_id=active_ay.id)
    subjects_list = await SubjectService.get_all_active(db, user.school_id)
    teachers_list = await TeacherService.get_all_active(db, user.school_id)

    return templates.TemplateResponse(
        request=request,
        name="schedules/list.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "schedules": schedules,
            "classrooms_list": classrooms_list,
            "subjects_list": subjects_list,
            "teachers_list": teachers_list,
            "days_list": list(DayOfWeek),
            "selected_class_id": classroom_id or "",
            "selected_day": day_of_week or "",
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "schedules",
            "str": str,
            "range": range,
        }
    )


@router.post("/schedules")
async def schedules_create(
    request: Request,
    classroom_id: str = Form(...),
    subject_id: str = Form(...),
    teacher_id: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)

    s_time = datetime.strptime(start_time, "%H:%M").time()
    e_time = datetime.strptime(end_time, "%H:%M").time()

    await ScheduleService.create(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        classroom_id=UUID(classroom_id),
        subject_id=UUID(subject_id),
        teacher_id=UUID(teacher_id),
        day_of_week=DayOfWeek(day_of_week),
        start_time=s_time,
        end_time=e_time,
        notes=notes
    )
    return RedirectResponse(url="/schedules", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/schedules/print", response_class=HTMLResponse)
async def schedules_print_page(
    request: Request,
    classroom_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/schedules", status_code=status.HTTP_303_SEE_OTHER)

    cid = UUID(classroom_id) if classroom_id else None
    filter_class = None
    if cid:
        c_res = await db.execute(select(Classroom).where(Classroom.id == cid))
        filter_class = c_res.scalar_one_or_none()

    schedules = await ScheduleService.get_all_for_print(
        db, user.school_id, academic_year_id=active_ay.id, classroom_id=cid
    )

    return templates.TemplateResponse(
        request=request,
        name="schedules/print.html",
        context={
            "school": school,
            "active_ay": active_ay,
            "filter_class": filter_class,
            "schedules": schedules,
        }
    )


@router.post("/schedules/{schedule_id}/delete")
async def schedules_delete(
    schedule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await ScheduleService.soft_delete(db, user.school_id, schedule_id)
    return RedirectResponse(url="/schedules", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# 6. DATA GURU PIKET (1 atau lebih guru / hari & Cetak)
# ---------------------------------------------------------

@router.get("/duty-teachers", response_class=HTMLResponse)
async def duty_teachers_page(
    request: Request,
    page: int = 1,
    day_of_week: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(
            url="/academic-years",
            status_code=status.HTTP_303_SEE_OTHER
        )

    dow = DayOfWeek(day_of_week) if day_of_week else None
    duties, total_count, total_pages = await DutyTeacherService.get_list(
        db, user.school_id, academic_year_id=active_ay.id, day_of_week=dow, page=page, limit=10
    )
    teachers_list = await TeacherService.get_all_active(db, user.school_id)

    return templates.TemplateResponse(
        request=request,
        name="duty_teachers/list.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "duty_teachers": duties,
            "teachers_list": teachers_list,
            "days_list": list(DayOfWeek),
            "selected_day": day_of_week or "",
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "duty_teachers",
            "str": str,
            "range": range,
        }
    )


@router.post("/duty-teachers")
async def duty_teachers_create(
    request: Request,
    teacher_id: str = Form(...),
    day_of_week: str = Form(...),
    duty_role: str = Form("Guru Piket Utama"),
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)

    await DutyTeacherService.create(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        teacher_id=UUID(teacher_id),
        day_of_week=DayOfWeek(day_of_week),
        duty_role=duty_role,
        notes=notes
    )
    return RedirectResponse(url="/duty-teachers", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/duty-teachers/print", response_class=HTMLResponse)
async def duty_teachers_print_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/duty-teachers", status_code=status.HTTP_303_SEE_OTHER)

    duties = await DutyTeacherService.get_all_for_print(db, user.school_id, academic_year_id=active_ay.id)

    return templates.TemplateResponse(
        request=request,
        name="duty_teachers/print.html",
        context={
            "school": school,
            "active_ay": active_ay,
            "duty_teachers": duties,
        }
    )


@router.post("/duty-teachers/{duty_id}/delete")
async def duty_teachers_delete(
    duty_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    await DutyTeacherService.soft_delete(db, user.school_id, duty_id)
    return RedirectResponse(url="/duty-teachers", status_code=status.HTTP_303_SEE_OTHER)


# ---------------------------------------------------------
# 7. ABSENSI GURU DI KELAS (Foto & Auto Lokasi GPS)
# ---------------------------------------------------------

@router.get("/attendance", response_class=HTMLResponse)
async def attendance_page(
    request: Request,
    teacher_id: Optional[str] = None,
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(
            url="/academic-years",
            status_code=status.HTTP_303_SEE_OTHER
        )

    tid = UUID(teacher_id) if teacher_id else None
    current_teacher = await AttendanceService.get_teacher_by_user_or_id(
        db, user.school_id, user, selected_teacher_id=tid
    )

    teachers_list = await TeacherService.get_all_active(db, user.school_id)
    today_date = datetime.now().date()
    today_dow = AttendanceService.get_today_day_of_week(today_date)
    today_day_name = today_dow.value if today_dow else "Minggu (Hari Libur)"

    today_schedules = []
    if current_teacher:
        today_schedules = await AttendanceService.get_schedules_for_attendance(
            db, user.school_id, academic_year_id=active_ay.id, teacher_id=current_teacher.id, target_date=today_date
        )

    return templates.TemplateResponse(
        request=request,
        name="attendance/index.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "current_teacher": current_teacher,
            "teachers_list": teachers_list,
            "today_schedules": today_schedules,
            "today_date": today_date,
            "today_day_name": today_day_name,
            "success_msg": success_msg,
            "error_msg": error_msg,
            "active_menu": "attendance",
            "str": str,
        }
    )


@router.post("/attendance/submit")
async def attendance_submit(
    request: Request,
    schedule_id: str = Form(...),
    teacher_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo_base64: Optional[str] = Form(None),
    location_accuracy: Optional[float] = Form(None),
    attendance_status: str = Form("Hadir", alias="status"),
    teaching_material: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    device_info: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    user, _ = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/academic-years", status_code=status.HTTP_303_SEE_OTHER)

    # Validasi koordinat GPS (Wajib Aktif)
    if latitude == 0.0 or longitude == 0.0 or latitude is None or longitude is None:
        return RedirectResponse(
            url="/attendance",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # Validasi Bukti Foto Kamera di Kelas
    if not photo_base64 or len(photo_base64.strip()) < 50:
        return RedirectResponse(
            url="/attendance",
            status_code=status.HTTP_303_SEE_OTHER
        )

    att_status = AttendanceStatus(attendance_status) if attendance_status in [s.value for s in AttendanceStatus] else AttendanceStatus.HADIR

    success, msg, _ = await AttendanceService.record_attendance(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        schedule_id=UUID(schedule_id),
        teacher_id=UUID(teacher_id),
        latitude=latitude,
        longitude=longitude,
        photo_base64=photo_base64,
        location_accuracy=location_accuracy,
        status=att_status,
        teaching_material=teaching_material,
        notes=notes,
        device_info=device_info
    )

    return RedirectResponse(url="/attendance", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/attendance/history", response_class=HTMLResponse)
async def attendance_history_page(
    request: Request,
    page: int = 1,
    filter_date: Optional[str] = None,
    teacher_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    ay_id = active_ay.id if active_ay else None

    f_date = datetime.strptime(filter_date, "%Y-%m-%d").date() if filter_date else None
    t_id = UUID(teacher_id) if teacher_id else None

    # Jika role guru biasa, otomatis batasi hanya melihat riwayat dirinya sendiri
    if user.role == UserRole.GURU:
        my_teacher = await AttendanceService.get_teacher_by_user_or_id(db, user.school_id, user)
        if my_teacher:
            t_id = my_teacher.id

    attendances, total_count, total_pages = await AttendanceService.get_history(
        db=db,
        school_id=user.school_id,
        academic_year_id=ay_id,
        teacher_id=t_id,
        filter_date=f_date,
        page=page,
        limit=10
    )

    teachers_list = await TeacherService.get_all_active(db, user.school_id)

    return templates.TemplateResponse(
        request=request,
        name="attendance/history.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "attendances": attendances,
            "teachers_list": teachers_list,
            "selected_date": filter_date or "",
            "selected_teacher_id": teacher_id or "",
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "active_menu": "attendance_history",
            "str": str,
            "range": range,
        }
    )


# ---------------------------------------------------------
# 8. LAPORAN & REKAPITULASI KEPALA SEKOLAH
# ---------------------------------------------------------

@router.get("/principal/reports", response_class=HTMLResponse)
async def principal_reports_page(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Halaman Rekapitulasi Presensi Guru untuk Kepala Sekolah & Operator.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    reports = await AttendanceService.get_rekap_report(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        start_date=s_date,
        end_date=e_date
    )

    return templates.TemplateResponse(
        request=request,
        name="principal/reports.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "reports": reports,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "active_menu": "principal_reports"
        }
    )


@router.get("/principal/reports/print", response_class=HTMLResponse)
async def principal_reports_print(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Format Cetak Dokumen Resmi PDF / Lembar Evaluasi Presensi Guru.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    reports = []
    if active_ay:
        reports = await AttendanceService.get_rekap_report(
            db=db,
            school_id=user.school_id,
            academic_year_id=active_ay.id,
            start_date=s_date,
            end_date=e_date
        )

    return templates.TemplateResponse(
        request=request,
        name="principal/print_report.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "reports": reports,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "now": datetime.now()
        }
    )


@router.get("/principal/reports/export-excel")
async def principal_reports_export_excel(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Ekspor berkas rekapitulasi kehadiran pendidik ke format Excel rapih.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    if not active_ay:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    school_name = school.name if school else "Sekolah"
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    reports = await AttendanceService.get_rekap_report(
        db=db,
        school_id=user.school_id,
        academic_year_id=active_ay.id,
        start_date=s_date,
        end_date=e_date
    )
    period_label = f"{start_date or 'Awal Periode'} s.d {end_date or 'Hari Ini'}"
    stream = AttendanceService.export_rekap_excel(
        school_name=school_name,
        period_label=period_label,
        rekap_data=reports
    )
    filename = f"Rekap_Presensi_Guru_{school_name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ---------------------------------------------------------
# 9. HALAMAN KHUSUS PERAN GURU
# ---------------------------------------------------------

@router.get("/teacher/my-schedules", response_class=HTMLResponse)
async def teacher_my_schedules_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Jadwal Mengajar Saya (Pribadi Guru) dalam satu minggu.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    my_teacher = await AttendanceService.get_teacher_by_user_or_id(db, user.school_id, user)

    schedules = []
    if active_ay and my_teacher:
        schedules = await ScheduleService.get_by_teacher(
            db=db,
            school_id=user.school_id,
            academic_year_id=active_ay.id,
            teacher_id=my_teacher.id
        )

    day_schedules = {d: [] for d in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]}
    for s in schedules:
        dow_val = s.day_of_week.value if hasattr(s.day_of_week, "value") else str(s.day_of_week)
        if dow_val in day_schedules:
            day_schedules[dow_val].append(s)

    return templates.TemplateResponse(
        request=request,
        name="teacher/my_schedules.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "my_teacher": my_teacher,
            "schedules": schedules,
            "day_schedules": day_schedules,
            "active_menu": "my_schedules"
        }
    )


@router.get("/teacher/my-attendance", response_class=HTMLResponse)
async def teacher_my_attendance_page(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Riwayat Presensi Pribadi Guru.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    my_teacher = await AttendanceService.get_teacher_by_user_or_id(db, user.school_id, user)

    attendances = []
    total_count = 0
    total_pages = 1

    if active_ay and my_teacher:
        attendances, total_count, total_pages = await AttendanceService.get_history(
            db=db,
            school_id=user.school_id,
            academic_year_id=active_ay.id,
            teacher_id=my_teacher.id,
            page=page,
            limit=10
        )

    return templates.TemplateResponse(
        request=request,
        name="teacher/my_attendance.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "my_teacher": my_teacher,
            "attendances": attendances,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "active_menu": "my_attendance",
            "str": str,
            "range": range
        }
    )


# ---------------------------------------------------------
# 10. HALAMAN KHUSUS PERAN SISWA
# ---------------------------------------------------------

@router.get("/student/my-class-schedule", response_class=HTMLResponse)
async def student_my_class_schedule_page(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Jadwal Pelajaran Kelas Saya (Pribadi Siswa) dalam satu minggu.
    """
    user, school = await _get_auth_context(request, db)
    if not user or not user.school_id:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    active_ay = await AcademicYearService.get_active(db, user.school_id)
    student = await StudentService.get_by_user_id(db, user.id)

    schedules = []
    if active_ay and student and student.classroom_id:
        schedules = await ScheduleService.get_all_for_print(
            db=db,
            school_id=user.school_id,
            academic_year_id=active_ay.id,
            classroom_id=student.classroom_id
        )

    day_schedules = {d: [] for d in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]}
    for s in schedules:
        dow_val = s.day_of_week.value if hasattr(s.day_of_week, "value") else str(s.day_of_week)
        if dow_val in day_schedules:
            day_schedules[dow_val].append(s)

    return templates.TemplateResponse(
        request=request,
        name="student/schedule.html",
        context={
            "user": user,
            "school": school,
            "active_ay": active_ay,
            "student": student,
            "classroom": student.classroom if student else None,
            "schedules": schedules,
            "day_schedules": day_schedules,
            "active_menu": "student_schedule"
        }
    )


# ---------------------------------------------------------
# 11. MANAJEMEN AKUN PENGGUNA SEKOLAH
# ---------------------------------------------------------

@router.get("/school/users", response_class=HTMLResponse)
async def school_users_page(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Halaman Kelola Akun Pengguna Sekolah (Superadmin & Operator Sekolah).
    """
    user, school = await _get_auth_context(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if user.role not in [UserRole.SUPERADMIN, UserRole.OPERATOR_SEKOLAH]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    # Superadmin dapat melihat pengguna global atau spesifik sekolah
    target_school_id = None if user.role == UserRole.SUPERADMIN else user.school_id
    role_filter = UserRole(role) if role in [r.value for r in UserRole] else None

    users_list, total_count, total_pages = await AuthService.get_school_users(
        db=db,
        school_id=target_school_id,
        page=page,
        limit=10,
        search=search,
        role=role_filter
    )

    return templates.TemplateResponse(
        request=request,
        name="school_users/list.html",
        context={
            "user": user,
            "school": school,
            "users": users_list,
            "page": page,
            "total_count": total_count,
            "total_pages": total_pages,
            "search": search or "",
            "selected_role": role or "",
            "roles": [UserRole.SUPERADMIN, UserRole.OPERATOR_SEKOLAH, UserRole.KEPALA_SEKOLAH, UserRole.GURU, UserRole.SISWA],
            "active_menu": "school_users",
            "str": str,
            "range": range
        }
    )


@router.post("/school/users")
async def school_users_create(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    nip: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Menambahkan Akun Pengguna Baru ke Sekolah / Sistem.
    """
    user, _ = await _get_auth_context(request, db)
    if not user or user.role not in [UserRole.SUPERADMIN, UserRole.OPERATOR_SEKOLAH]:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    target_role = UserRole(role) if role in [r.value for r in UserRole] else UserRole.GURU
    target_school_id = None if (user.role == UserRole.SUPERADMIN and target_role == UserRole.SUPERADMIN) else user.school_id

    await AuthService.create_school_user(
        db=db,
        school_id=target_school_id,
        email=email,
        password=password,
        full_name=full_name,
        role=target_role,
        phone=phone,
        nip=nip
    )

    return RedirectResponse(url="/school/users", status_code=status.HTTP_303_SEE_OTHER)

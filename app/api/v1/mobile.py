"""
Router API RESTful untuk Aplikasi Mobile (Smartphone).
Menyediakan integrasi backend yang cepat dan aman untuk aplikasi Android / iOS (Flutter / React Native).
Mendukung presensi guru dengan kamera + GPS geolokasi, monitoring siswa, jadwal harian, dan riwayat presensi.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.models import AttendanceStatus, DayOfWeek, User, UserRole
from app.services.academic_service import (
    AcademicYearService,
    DutyTeacherService,
    ScheduleService,
    StudentService,
    TeacherService,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/mobile", tags=["Aplikasi Mobile"])


# ---------------------------------------------------------
# Pydantic Schemas untuk Mobile Request & Response
# ---------------------------------------------------------

class MobileAttendanceSubmitRequest(BaseModel):
    schedule_id: str = Field(..., description="ID Jadwal Pelajaran (UUID)")
    teacher_id: Optional[str] = Field(None, description="ID Guru (opsional jika login sebagai guru)")
    latitude: float = Field(..., description="Titik Koordinat Latitude GPS")
    longitude: float = Field(..., description="Titik Koordinat Longitude GPS")
    location_accuracy: Optional[float] = Field(None, description="Akurasi GPS dalam meter")
    photo_base64: str = Field(..., description="Foto bukti kehadiran di kelas format base64")
    attendance_status: str = Field("hadir", description="Status kehadiran: hadir, sakit, izin, alpa")
    teaching_material: Optional[str] = Field(None, description="Materi pokok pembelajaran yang diajarkan")
    notes: Optional[str] = Field(None, description="Catatan guru di kelas")
    device_info: Optional[str] = Field(None, description="Informasi perangkat smartphone")


# ---------------------------------------------------------
# 1. PROFIL PENGGUNA MOBILE
# ---------------------------------------------------------

@router.get("/profile", summary="Ambil Profil Pengguna Mobile")
async def mobile_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mengambil data profil pengguna mobile beserta entitas terkait (Guru / Siswa / Operator).
    """
    profile_data: Dict[str, Any] = {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "nip": current_user.nip,
        "phone": current_user.phone,
        "school_id": str(current_user.school_id) if current_user.school_id else None,
        "teacher_info": None,
        "student_info": None
    }

    if current_user.role == UserRole.GURU and current_user.school_id:
        teacher = await AttendanceService.get_teacher_by_user_or_id(db, current_user.school_id, current_user)
        if teacher:
            profile_data["teacher_info"] = {
                "id": str(teacher.id),
                "nip": teacher.nip,
                "name": teacher.name,
                "gender": teacher.gender.value if hasattr(teacher.gender, "value") else str(teacher.gender),
                "phone": teacher.phone,
                "employment_status": teacher.employment_status
            }

    elif current_user.role == UserRole.SISWA:
        student = await StudentService.get_by_user_id(db, current_user.id)
        if student:
            profile_data["student_info"] = {
                "id": str(student.id),
                "nisn": student.nisn,
                "nis": student.nis,
                "name": student.name,
                "gender": student.gender.value if hasattr(student.gender, "value") else str(student.gender),
                "classroom_id": str(student.classroom_id) if student.classroom_id else None,
                "classroom_name": student.classroom.name if student.classroom else None
            }

    return {
        "success": True,
        "data": profile_data
    }


# ---------------------------------------------------------
# 2. FITUR GURU: JADWAL & PRESENSI KELAS
# ---------------------------------------------------------

@router.get(
    "/teacher/today-schedules",
    summary="Ambil Jadwal Mengajar Guru Hari Ini",
    dependencies=[Depends(require_roles([UserRole.GURU, UserRole.OPERATOR_SEKOLAH, UserRole.KEPALA_SEKOLAH]))]
)
async def mobile_teacher_today_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mengambil daftar jadwal mengajar guru pada hari ini dengan status kehadiran per sesi.
    """
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Pengguna tidak terhubung ke sekolah.")

    active_ay = await AcademicYearService.get_active(db, current_user.school_id)
    if not active_ay:
        raise HTTPException(status_code=400, detail="Belum ada Tahun Pelajaran aktif di sekolah ini.")

    teacher = await AttendanceService.get_teacher_by_user_or_id(db, current_user.school_id, current_user)
    if not teacher:
        raise HTTPException(status_code=404, detail="Data profil guru tidak ditemukan.")

    today_schedules = await AttendanceService.get_schedules_for_attendance(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=active_ay.id,
        teacher_id=teacher.id
    )

    items = []
    for item in today_schedules:
        sched = item["schedule"]
        att = item["attendance"]
        items.append({
            "schedule_id": str(sched.id),
            "period_number": sched.period_number,
            "start_time": sched.start_time.strftime("%H:%M"),
            "end_time": sched.end_time.strftime("%H:%M"),
            "subject_name": sched.subject.name if sched.subject else "-",
            "classroom_name": sched.classroom.name if sched.classroom else "-",
            "grade_level": sched.classroom.grade_level if sched.classroom else "-",
            "attendance": {
                "id": str(att.id) if att else None,
                "status": att.status.value if att else "belum_hadir",
                "check_in_time": att.check_in_time.strftime("%H:%M:%S") if (att and att.check_in_time) else None,
                "photo_url": att.photo_url if att else None,
                "teaching_material": att.teaching_material if att else None,
            } if att else None,
            "is_attended": att is not None
        })

    return {
        "success": True,
        "teacher": {
            "id": str(teacher.id),
            "name": teacher.name,
            "nip": teacher.nip
        },
        "count": len(items),
        "data": items
    }


@router.post(
    "/teacher/attendance",
    summary="Kirim Presensi Guru di Kelas (Kamera + GPS)",
    dependencies=[Depends(require_roles([UserRole.GURU, UserRole.OPERATOR_SEKOLAH]))]
)
async def mobile_teacher_record_attendance(
    payload: MobileAttendanceSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mencatat presensi kehadiran guru di kelas dengan validasi koordinat GPS dan foto kamera wajib.
    """
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Pengguna tidak terhubung ke sekolah.")

    active_ay = await AcademicYearService.get_active(db, current_user.school_id)
    if not active_ay:
        raise HTTPException(status_code=400, detail="Belum ada Tahun Pelajaran aktif.")

    # Tentukan ID guru
    teacher_id: Optional[UUID] = None
    if payload.teacher_id:
        try:
            teacher_id = UUID(payload.teacher_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID Guru tidak valid.")
    else:
        teacher = await AttendanceService.get_teacher_by_user_or_id(db, current_user.school_id, current_user)
        if not teacher:
            raise HTTPException(status_code=404, detail="Data guru tidak ditemukan untuk akun ini.")
        teacher_id = teacher.id

    try:
        schedule_uuid = UUID(payload.schedule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID Jadwal tidak valid.")

    att_status = (
        AttendanceStatus(payload.attendance_status)
        if payload.attendance_status in [s.value for s in AttendanceStatus]
        else AttendanceStatus.HADIR
    )

    success, msg, att = await AttendanceService.record_attendance(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=active_ay.id,
        schedule_id=schedule_uuid,
        teacher_id=teacher_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        photo_base64=payload.photo_base64,
        location_accuracy=payload.location_accuracy,
        status=att_status,
        teaching_material=payload.teaching_material,
        notes=payload.notes,
        device_info=payload.device_info or "Mobile App (Android/iOS)"
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "message": msg,
        "data": {
            "attendance_id": str(att.id) if att else None,
            "status": att.status.value if att else None,
            "check_in_time": att.check_in_time.isoformat() if (att and att.check_in_time) else None,
            "photo_url": att.photo_url if att else None
        }
    }


@router.get(
    "/teacher/attendance/history",
    summary="Riwayat Presensi Guru Pribadi",
    dependencies=[Depends(require_roles([UserRole.GURU, UserRole.OPERATOR_SEKOLAH, UserRole.KEPALA_SEKOLAH]))]
)
async def mobile_teacher_attendance_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mengambil riwayat presensi guru pribadi dengan paginasi.
    """
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Pengguna tidak terhubung ke sekolah.")

    active_ay = await AcademicYearService.get_active(db, current_user.school_id)
    ay_id = active_ay.id if active_ay else None

    teacher = await AttendanceService.get_teacher_by_user_or_id(db, current_user.school_id, current_user)
    teacher_id = teacher.id if teacher else None

    attendances, total_count, total_pages = await AttendanceService.get_history(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=ay_id,
        teacher_id=teacher_id,
        page=page,
        limit=limit
    )

    items = []
    for att in attendances:
        items.append({
            "id": str(att.id),
            "date": att.attendance_date.strftime("%Y-%m-%d"),
            "check_in_time": att.check_in_time.strftime("%H:%M:%S") if att.check_in_time else None,
            "status": att.status.value,
            "photo_url": att.photo_url,
            "classroom_name": att.classroom.name if att.classroom else "-",
            "subject_name": att.subject.name if att.subject else "-",
            "teaching_material": att.teaching_material,
            "latitude": att.latitude,
            "longitude": att.longitude,
            "is_within_radius": att.is_within_radius
        })

    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": items
    }


# ---------------------------------------------------------
# 3. FITUR SISWA: MONITORING PRESENSI KELAS HARI INI
# ---------------------------------------------------------

@router.get("/student/today-attendance", summary="Status Kehadiran Guru di Kelas Siswa Hari Ini")
async def mobile_student_today_attendance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Melihat jadwal pelajaran kelas siswa hari ini secara langsung, lengkap dengan status apakah guru sudah hadir di kelas.
    """
    student = await StudentService.get_by_user_id(db, current_user.id)
    if not student or not student.classroom_id:
        raise HTTPException(status_code=404, detail="Data siswa atau rombongan belajar kelas belum ditetapkan.")

    active_ay = await AcademicYearService.get_active(db, student.school_id)
    if not active_ay:
        raise HTTPException(status_code=400, detail="Belum ada Tahun Pelajaran aktif.")

    class_schedules = await AttendanceService.get_student_class_today(
        db=db,
        school_id=student.school_id,
        academic_year_id=active_ay.id,
        classroom_id=student.classroom_id
    )

    items = []
    for item in class_schedules:
        sched = item["schedule"]
        att = item["attendance"]
        items.append({
            "schedule_id": str(sched.id),
            "period_number": sched.period_number,
            "start_time": sched.start_time.strftime("%H:%M"),
            "end_time": sched.end_time.strftime("%H:%M"),
            "subject_name": sched.subject.name if sched.subject else "-",
            "teacher_name": sched.teacher.name if sched.teacher else "-",
            "is_attended": item["is_attended"],
            "attendance_status": att.status.value if att else "belum_hadir",
            "check_in_time": att.check_in_time.strftime("%H:%M:%S") if (att and att.check_in_time) else None
        })

    return {
        "success": True,
        "classroom": {
            "id": str(student.classroom.id),
            "name": student.classroom.name,
            "grade_level": student.classroom.grade_level
        },
        "count": len(items),
        "data": items
    }


# ---------------------------------------------------------
# 4. GURU PIKET HARI INI
# ---------------------------------------------------------

@router.get("/duty-teachers/today", summary="Daftar Guru Piket Bertugas Hari Ini")
async def mobile_duty_teachers_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mendapatkan daftar nama guru piket yang bertugas pada hari ini di sekolah.
    """
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="Pengguna tidak terhubung ke sekolah.")

    active_ay = await AcademicYearService.get_active(db, current_user.school_id)
    if not active_ay:
        return {"success": True, "count": 0, "data": []}

    today_dow = AttendanceService.get_today_day_of_week(datetime.now().date())
    if not today_dow:
        return {"success": True, "count": 0, "data": []}

    duty_teachers, _, _ = await DutyTeacherService.get_list(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=active_ay.id,
        day_of_week=today_dow,
        limit=50
    )

    items = []
    for dt in duty_teachers:
        if dt.teacher:
            items.append({
                "id": str(dt.teacher.id),
                "name": dt.teacher.name,
                "nip": dt.teacher.nip,
                "phone": dt.teacher.phone,
                "notes": dt.notes
            })

    return {
        "success": True,
        "count": len(items),
        "data": items
    }

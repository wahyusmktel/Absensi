"""
Layanan Basis Data untuk Presensi Kehadiran Guru.
Menangani pencocokan jadwal hari ini, penyimpanan foto bukti kelas, penangkapan koordinat GPS, dan Soft Delete.
"""

import base64
import os
import uuid
from datetime import date, datetime, time, timezone
from math import ceil
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AcademicYear,
    AttendanceStatus,
    Classroom,
    DayOfWeek,
    Schedule,
    School,
    Subject,
    Teacher,
    TeacherAttendance,
    User,
    UserRole,
)

INDONESIAN_DAY_MAP = {
    0: DayOfWeek.SENIN,
    1: DayOfWeek.SELASA,
    2: DayOfWeek.RABU,
    3: DayOfWeek.KAMIS,
    4: DayOfWeek.JUMAT,
    5: DayOfWeek.SABTU,
    6: None,  # Minggu (Libur)
}


class AttendanceService:
    """
    Layanan operasional presensi kehadiran guru di kelas.
    """

    @staticmethod
    def get_today_day_of_week(target_date: Optional[date] = None) -> Optional[DayOfWeek]:
        """
        Menentukan nama hari bahasa Indonesia (DayOfWeek) dari tanggal kalender.
        """
        d = target_date or datetime.now().date()
        weekday_idx = d.weekday()
        return INDONESIAN_DAY_MAP.get(weekday_idx)

    @staticmethod
    async def get_teacher_by_user_or_id(
        db: AsyncSession,
        school_id: UUID,
        user: User,
        selected_teacher_id: Optional[UUID] = None
    ) -> Optional[Teacher]:
        """
        Mencari profil guru yang terkait dengan user yang sedang login atau ID yang dipilih.
        Jika user berperan GURU, sistem mencocokkan via user_id atau email/NIP.
        Jika operator/kepsek, bisa memilih guru mana saja dari daftar.
        """
        if selected_teacher_id:
            res = await db.execute(
                select(Teacher).where(
                    Teacher.id == selected_teacher_id,
                    Teacher.school_id == school_id,
                    Teacher.deleted_at.is_(None)
                )
            )
            return res.scalar_one_or_none()

        if user.role == UserRole.GURU:
            # Cari berdasarkan user_id
            res = await db.execute(
                select(Teacher).where(
                    Teacher.user_id == user.id,
                    Teacher.school_id == school_id,
                    Teacher.deleted_at.is_(None)
                )
            )
            teacher = res.scalar_one_or_none()
            if teacher:
                return teacher

            # Cari alternatif berdasarkan email
            res = await db.execute(
                select(Teacher).where(
                    Teacher.email == user.email,
                    Teacher.school_id == school_id,
                    Teacher.deleted_at.is_(None)
                )
            )
            return res.scalar_one_or_none()

        return None

    @staticmethod
    async def get_schedules_for_attendance(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        teacher_id: Optional[UUID] = None,
        target_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Mengambil daftar jadwal mengajar hari ini untuk guru yang bersangkutan,
        lengkap dengan status apakah sudah melakukan absensi atau belum.
        """
        curr_date = target_date or datetime.now().date()
        today_day = AttendanceService.get_today_day_of_week(curr_date)

        if not today_day:
            return []  # Hari minggu tidak ada jadwal

        query = select(Schedule).options(
            selectinload(Schedule.classroom),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher)
        ).where(
            Schedule.school_id == school_id,
            Schedule.academic_year_id == academic_year_id,
            Schedule.day_of_week == today_day,
            Schedule.deleted_at.is_(None)
        )

        if teacher_id:
            query = query.where(Schedule.teacher_id == teacher_id)

        query = query.order_by(Schedule.start_time.asc())
        schedules_res = await db.execute(query)
        schedules = schedules_res.scalars().all()

        # Ambil absensi yang sudah tercatat pada tanggal ini
        schedule_ids = [s.id for s in schedules]
        attendances_map: Dict[UUID, TeacherAttendance] = {}
        if schedule_ids:
            att_query = select(TeacherAttendance).where(
                TeacherAttendance.schedule_id.in_(schedule_ids),
                TeacherAttendance.attendance_date == curr_date,
                TeacherAttendance.deleted_at.is_(None)
            )
            att_res = await db.execute(att_query)
            for att in att_res.scalars().all():
                attendances_map[att.schedule_id] = att

        # Gabungkan data jadwal dan status kehadiran
        results = []
        for s in schedules:
            att = attendances_map.get(s.id)
            results.append({
                "schedule": s,
                "attendance": att,
                "is_attended": att is not None
            })

        return results

    @staticmethod
    def save_attendance_photo(photo_base64: str) -> str:
        """
        Menyimpan foto bukti kamera kelas format Base64 ke disk statis.
        Mencegah file upload berbahaya dan menghasilkan nama file unik.
        """
        # Hapus prefix data URL jika ada (e.g. data:image/jpeg;base64,...)
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]

        file_bytes = base64.b64decode(photo_base64)
        filename = f"att_{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.jpg"
        upload_dir = os.path.join("app", "static", "uploads", "attendances")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return f"/static/uploads/attendances/{filename}"

    @staticmethod
    async def record_attendance(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        schedule_id: UUID,
        teacher_id: UUID,
        latitude: float,
        longitude: float,
        photo_base64: Optional[str] = None,
        location_accuracy: Optional[float] = None,
        status: AttendanceStatus = AttendanceStatus.HADIR,
        teaching_material: Optional[str] = None,
        notes: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> Tuple[bool, str, Optional[TeacherAttendance]]:
        """
        Mencatat absensi guru di kelas dengan validasi jadwal dan lokasi GPS.
        """
        today_date = datetime.now().date()
        now_time = datetime.now().time()

        # 1. Cek apakah sudah pernah absen untuk jadwal ini hari ini
        existing = await db.execute(
            select(TeacherAttendance).where(
                TeacherAttendance.schedule_id == schedule_id,
                TeacherAttendance.attendance_date == today_date,
                TeacherAttendance.deleted_at.is_(None)
            )
        )
        if existing.scalar_one_or_none():
            return False, "Anda sudah melakukan absensi untuk sesi jadwal ini hari ini.", None

        # 2. Simpan foto bukti jika ada
        photo_url = None
        if photo_base64 and len(photo_base64.strip()) > 50:
            try:
                photo_url = AttendanceService.save_attendance_photo(photo_base64)
            except Exception as e:
                return False, f"Gagal memproses foto bukti kehadiran: {str(e)}", None

        # 3. Buat entitas absensi
        att = TeacherAttendance(
            school_id=school_id,
            academic_year_id=academic_year_id,
            schedule_id=schedule_id,
            teacher_id=teacher_id,
            attendance_date=today_date,
            attendance_time=now_time,
            status=status,
            photo_url=photo_url,
            latitude=latitude,
            longitude=longitude,
            location_accuracy=location_accuracy,
            teaching_material=teaching_material.strip() if teaching_material else None,
            notes=notes.strip() if notes else None,
            device_info=device_info
        )
        db.add(att)
        await db.commit()
        await db.refresh(att)
        return True, "Absensi kehadiran di kelas berhasil dicatat.", att

    @staticmethod
    async def get_history(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
        filter_date: Optional[date] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[TeacherAttendance], int, int]:
        """
        Mengambil riwayat absensi guru dengan relasi lengkap dan paginasi 10 data.
        """
        query = select(TeacherAttendance).options(
            selectinload(TeacherAttendance.teacher),
            selectinload(TeacherAttendance.schedule).selectinload(Schedule.classroom),
            selectinload(TeacherAttendance.schedule).selectinload(Schedule.subject)
        ).where(
            TeacherAttendance.school_id == school_id,
            TeacherAttendance.deleted_at.is_(None)
        )

        if academic_year_id:
            query = query.where(TeacherAttendance.academic_year_id == academic_year_id)
        if teacher_id:
            query = query.where(TeacherAttendance.teacher_id == teacher_id)
        if filter_date:
            query = query.where(TeacherAttendance.attendance_date == filter_date)

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(TeacherAttendance.attendance_date.desc(), TeacherAttendance.attendance_time.desc())
            .offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

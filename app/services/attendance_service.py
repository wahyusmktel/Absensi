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
from app.services.excel_service import ExcelExportService

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

    @staticmethod
    async def get_summary_stats(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        target_date: Optional[date] = None
    ) -> Dict:
        """
        Menghitung ringkasan KPI presensi hari ini untuk Kepala Sekolah & Operator:
        - Total jadwal mengajar hari ini
        - Total guru sudah hadir di kelas
        - Total guru izin / sakit / alpa
        - Total sesi yang belum melakukan absensi
        - Persentase kehadiran hari ini
        """
        curr_date = target_date or datetime.now().date()
        today_dow = AttendanceService.get_today_day_of_week(curr_date)

        if not today_dow or not academic_year_id:
            return {
                "total_schedules": 0,
                "total_present": 0,
                "total_permit": 0,
                "total_sick": 0,
                "total_alpha": 0,
                "total_pending": 0,
                "attendance_percentage": 0.0,
            }

        # 1. Total jadwal aktif hari ini
        sch_query = select(Schedule).where(
            Schedule.school_id == school_id,
            Schedule.academic_year_id == academic_year_id,
            Schedule.day_of_week == today_dow,
            Schedule.deleted_at.is_(None)
        )
        schedules_res = await db.execute(sch_query)
        schedules = schedules_res.scalars().all()
        total_schedules = len(schedules)
        sch_ids = [s.id for s in schedules]

        if not sch_ids:
            return {
                "total_schedules": 0,
                "total_present": 0,
                "total_permit": 0,
                "total_sick": 0,
                "total_alpha": 0,
                "total_pending": 0,
                "attendance_percentage": 100.0 if not today_dow else 0.0,
            }

        # 2. Ambil absensi tercatat hari ini untuk jadwal tersebut
        att_query = select(TeacherAttendance).where(
            TeacherAttendance.school_id == school_id,
            TeacherAttendance.schedule_id.in_(sch_ids),
            TeacherAttendance.attendance_date == curr_date,
            TeacherAttendance.deleted_at.is_(None)
        )
        att_res = await db.execute(att_query)
        attendances = att_res.scalars().all()

        present_cnt = sum(1 for a in attendances if a.status == AttendanceStatus.HADIR)
        permit_cnt = sum(1 for a in attendances if a.status == AttendanceStatus.IZIN)
        sick_cnt = sum(1 for a in attendances if a.status == AttendanceStatus.SAKIT)
        alpha_cnt = sum(1 for a in attendances if a.status == AttendanceStatus.ALPA)
        recorded_ids = {a.schedule_id for a in attendances}
        pending_cnt = max(0, total_schedules - len(recorded_ids))

        pct = round((present_cnt / total_schedules * 100), 1) if total_schedules > 0 else 0.0

        return {
            "total_schedules": total_schedules,
            "total_present": present_cnt,
            "total_permit": permit_cnt,
            "total_sick": sick_cnt,
            "total_alpha": alpha_cnt,
            "total_pending": pending_cnt,
            "attendance_percentage": pct,
        }

    @staticmethod
    async def get_rekap_report(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Menghasilkan rekapitulasi kehadiran per guru untuk laporan Kepala Sekolah / Pengawas.
        """
        # Ambil seluruh guru aktif di sekolah
        teachers_res = await db.execute(
            select(Teacher).where(
                Teacher.school_id == school_id,
                Teacher.deleted_at.is_(None)
            ).order_by(Teacher.name.asc())
        )
        teachers = teachers_res.scalars().all()

        # Ambil data absensi dalam rentang tanggal
        att_query = select(TeacherAttendance).where(
            TeacherAttendance.school_id == school_id,
            TeacherAttendance.deleted_at.is_(None)
        )
        if academic_year_id:
            att_query = att_query.where(TeacherAttendance.academic_year_id == academic_year_id)
        if start_date:
            att_query = att_query.where(TeacherAttendance.attendance_date >= start_date)
        if end_date:
            att_query = att_query.where(TeacherAttendance.attendance_date <= end_date)

        att_res = await db.execute(att_query)
        all_atts = att_res.scalars().all()

        rekap_list = []
        for t in teachers:
            t_atts = [a for a in all_atts if a.teacher_id == t.id]
            hadir = sum(1 for a in t_atts if a.status == AttendanceStatus.HADIR)
            izin = sum(1 for a in t_atts if a.status == AttendanceStatus.IZIN)
            sakit = sum(1 for a in t_atts if a.status == AttendanceStatus.SAKIT)
            alpa = sum(1 for a in t_atts if a.status == AttendanceStatus.ALPA)
            total_sesi = len(t_atts)
            pct = round((hadir / total_sesi * 100), 1) if total_sesi > 0 else 0.0

            rekap_list.append({
                "teacher": t,
                "hadir": hadir,
                "izin": izin,
                "sakit": sakit,
                "alpa": alpa,
                "total_sesi": total_sesi,
                "percentage": pct
            })

        return rekap_list

    @staticmethod
    def export_rekap_excel(
        school_name: str,
        period_label: str,
        rekap_data: List[Dict]
    ):
        """
        Mengekspor data rekapitulasi kehadiran guru ke file Excel berformat CoreUI institusional.
        """
        headers = [
            "No",
            "Nama Guru & Gelar",
            "NIP / NUPTK",
            "Status Pegawai",
            "Hadir (Sesi)",
            "Izin (Sesi)",
            "Sakit (Sesi)",
            "Alpa (Sesi)",
            "Total Pertemuan",
            "Persentase (%)"
        ]
        rows = []
        for idx, item in enumerate(rekap_data, start=1):
            t = item["teacher"]
            rows.append([
                idx,
                t.name,
                t.nip or "-",
                t.employment_status or "-",
                item["hadir"],
                item["izin"],
                item["sakit"],
                item["alpa"],
                item["total_sesi"],
                f"{item['percentage']}%"
            ])

        return ExcelExportService.create_styled_workbook(
            title=f"Rekapitulasi Kehadiran Guru - Periode {period_label}",
            school_name=school_name,
            headers=headers,
            rows=rows,
            sheet_name="Rekap Kehadiran"
        )

    @staticmethod
    async def get_student_class_today(
        db: AsyncSession,
        school_id: UUID,
        classroom_id: UUID,
        academic_year_id: UUID,
        target_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Mengambil jadwal kelas siswa hari ini beserta status kehadiran guru di kelas secara real-time.
        Digunakan oleh Portal Siswa untuk memantau apakah guru sudah hadir, izin, atau diganti guru piket.
        """
        curr_date = target_date or datetime.now().date()
        today_dow = AttendanceService.get_today_day_of_week(curr_date)

        if not today_dow:
            return []

        # Ambil jadwal kelas hari ini
        query = select(Schedule).options(
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher)
        ).where(
            Schedule.school_id == school_id,
            Schedule.classroom_id == classroom_id,
            Schedule.academic_year_id == academic_year_id,
            Schedule.day_of_week == today_dow,
            Schedule.deleted_at.is_(None)
        ).order_by(Schedule.start_time.asc())

        sch_res = await db.execute(query)
        schedules = sch_res.scalars().all()
        sch_ids = [s.id for s in schedules]

        # Ambil status absensi hari ini
        att_map = {}
        if sch_ids:
            att_query = select(TeacherAttendance).where(
                TeacherAttendance.schedule_id.in_(sch_ids),
                TeacherAttendance.attendance_date == curr_date,
                TeacherAttendance.deleted_at.is_(None)
            )
            att_res = await db.execute(att_query)
            for a in att_res.scalars().all():
                att_map[a.schedule_id] = a

        result = []
        for s in schedules:
            attendance = att_map.get(s.id)
            result.append({
                "schedule": s,
                "attendance": attendance,
                "is_attended": attendance is not None,
                "status_label": attendance.status.value if attendance else "Belum Hadir"
            })

        return result

"""
Pengujian Menyeluruh untuk Halaman Spesifik 5 Role, Import/Export Excel,
Format Cetak PDF, dan Endpoint RESTful API Mobile Smartphone.
"""

import base64
import io
import uuid
import datetime
import pytest
from httpx import AsyncClient, ASGITransport
from openpyxl import Workbook

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash, create_access_token
from app.models.models import (
    AcademicYear,
    Classroom,
    DayOfWeek,
    DutyTeacher,
    Schedule,
    School,
    Student,
    Subject,
    Teacher,
    User,
    UserRole,
)


@pytest.mark.asyncio
async def test_role_based_pages_and_excel_and_mobile():
    """
    Menguji workflow lengkap:
    1. Pembuatan data sekolah dan 5 peran pengguna.
    2. Verifikasi akses dashboard dan halaman khusus tiap peran.
    3. Verifikasi unduh template & ekspor file Excel.
    4. Verifikasi halaman cetak laporan PDF Kepala Sekolah.
    5. Verifikasi RESTful API Mobile untuk aplikasi smartphone.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        async with AsyncSessionLocal() as db_session:
            uid = uuid.uuid4().hex[:6]
            password_plain = "Password123!"
            password_hashed = get_password_hash(password_plain)

            # 1. Buat Sekolah
            school = School(
                npsn=f"NPSN_{uid}",
                name=f"SMP Negeri 1 RoleTest {uid}",
                address="Jl. Pendidikan No. 123",
                phone="021-12345678",
                email=f"smp_{uid}@sekolah.id",
                is_active=True
            )
            db_session.add(school)
            await db_session.flush()

            # Buat Tahun Pelajaran Aktif
            ay = AcademicYear(
                school_id=school.id,
                name=f"2026/2027-{uid}",
                semester="Ganjil",
                is_active=True
            )
            db_session.add(ay)
            await db_session.flush()

            # Buat Mata Pelajaran
            subject = Subject(
                school_id=school.id,
                code=f"MAT-{uid}",
                name="Matematika",
                grade_level="Semua"
            )
            db_session.add(subject)
            await db_session.flush()

            # Buat Guru
            teacher = Teacher(
                school_id=school.id,
                nip=f"19850101_{uid}",
                name=f"Guru Matematika {uid}",
                gender="L",
                phone="08123456789",
                employment_status="PNS",
                is_active=True
            )
            db_session.add(teacher)
            await db_session.flush()

            # Buat Akun Pengguna untuk Guru
            teacher_user = User(
                school_id=school.id,
                email=f"guru_{uid}@sekolah.id",
                hashed_password=password_hashed,
                full_name=teacher.name,
                role=UserRole.GURU,
                nip=teacher.nip,
                is_active=True
            )
            db_session.add(teacher_user)
            await db_session.flush()
            teacher.user_id = teacher_user.id

            # Buat Kelas
            classroom = Classroom(
                school_id=school.id,
                academic_year_id=ay.id,
                name=f"VII-A-{uid}",
                grade_level="7",
                homeroom_teacher_id=teacher.id,
                capacity=32,
                is_active=True
            )
            db_session.add(classroom)
            await db_session.flush()

            # Buat Siswa & Akun Siswa
            student_user = User(
                school_id=school.id,
                email=f"siswa_{uid}@sekolah.id",
                hashed_password=password_hashed,
                full_name=f"Siswa Budi {uid}",
                role=UserRole.SISWA,
                is_active=True
            )
            db_session.add(student_user)
            await db_session.flush()

            student = Student(
                school_id=school.id,
                classroom_id=classroom.id,
                user_id=student_user.id,
                nisn=f"00123{uid}",
                nis=f"1234{uid}",
                name=student_user.full_name,
                gender="L",
                is_active=True
            )
            db_session.add(student)
            await db_session.flush()

            # Buat Akun Kepala Sekolah
            principal_user = User(
                school_id=school.id,
                email=f"kepsek_{uid}@sekolah.id",
                hashed_password=password_hashed,
                full_name=f"Dr. H. Kepala Sekolah {uid}",
                role=UserRole.KEPALA_SEKOLAH,
                nip=f"19700101_{uid}",
                is_active=True
            )
            db_session.add(principal_user)

            # Buat Akun Operator Sekolah
            operator_user = User(
                school_id=school.id,
                email=f"operator_{uid}@sekolah.id",
                hashed_password=password_hashed,
                full_name=f"Operator SMP {uid}",
                role=UserRole.OPERATOR_SEKOLAH,
                is_active=True
            )
            db_session.add(operator_user)

            # Buat Jadwal Pelajaran (Senin)
            schedule = Schedule(
                school_id=school.id,
                academic_year_id=ay.id,
                classroom_id=classroom.id,
                subject_id=subject.id,
                teacher_id=teacher.id,
                day_of_week=DayOfWeek.SENIN,
                start_time=datetime.time(7, 30),
                end_time=datetime.time(9, 0),
                period_number=1,
                notes="Materi Aljabar"
            )
            db_session.add(schedule)

            # Buat Guru Piket (Senin)
            duty_teacher = DutyTeacher(
                school_id=school.id,
                academic_year_id=ay.id,
                teacher_id=teacher.id,
                day_of_week=DayOfWeek.SENIN,
                notes="Piket Gerbang Utama & Pagi"
            )
            db_session.add(duty_teacher)

            await db_session.commit()

            # Helper function untuk mendapatkan cookie autentikasi
            def get_auth_cookie(u: User):
                token = create_access_token(
                    subject=str(u.id),
                    extra_claims={"role": u.role.value, "school_id": str(u.school_id) if u.school_id else None}
                )
                return {"access_token": token}

            # =========================================================
            # A. PENGUJIAN AKSES PERAN OPERATOR SEKOLAH
            # =========================================================
            op_cookies = get_auth_cookie(operator_user)
            res_op_dash = await async_client.get("/dashboard", cookies=op_cookies)
            assert res_op_dash.status_code == 200
            assert "operator_sekolah" in res_op_dash.text or "Total Guru" in res_op_dash.text

            # Akses Halaman Siswa
            res_students = await async_client.get("/students", cookies=op_cookies)
            assert res_students.status_code == 200
            assert "Data Siswa" in res_students.text
            assert student.name in res_students.text

            # Unduh template sampel Excel Siswa
            res_student_sample = await async_client.get("/students/sample-excel", cookies=op_cookies)
            assert res_student_sample.status_code == 200
            assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res_student_sample.headers["content-type"]

            # Unduh template sampel Excel Guru
            res_teacher_sample = await async_client.get("/teachers/sample-excel", cookies=op_cookies)
            assert res_teacher_sample.status_code == 200

            # Ekspor Excel Siswa
            res_student_export = await async_client.get("/students/export-excel", cookies=op_cookies)
            assert res_student_export.status_code == 200

            # Ekspor Excel Guru
            res_teacher_export = await async_client.get("/teachers/export-excel", cookies=op_cookies)
            assert res_teacher_export.status_code == 200

            # Manajemen Pengguna Sekolah (/school/users)
            res_users = await async_client.get("/school/users", cookies=op_cookies)
            assert res_users.status_code == 200
            assert "Pengguna" in res_users.text

            # =========================================================
            # B. PENGUJIAN AKSES PERAN KEPALA SEKOLAH
            # =========================================================
            kepsek_cookies = get_auth_cookie(principal_user)
            res_kepsek_dash = await async_client.get("/dashboard", cookies=kepsek_cookies)
            assert res_kepsek_dash.status_code == 200
            assert "kepala_sekolah" in res_kepsek_dash.text or "Kepala Sekolah" in res_kepsek_dash.text

            # Laporan & Rekapitulasi Presensi
            res_reports = await async_client.get("/principal/reports", cookies=kepsek_cookies)
            assert res_reports.status_code == 200
            assert "Rekapitulasi Presensi" in res_reports.text

            # Halaman Cetak Dokumen PDF
            res_print = await async_client.get("/principal/reports/print", cookies=kepsek_cookies)
            assert res_print.status_code == 200
            assert "REKAPITULASI KEHADIRAN DAN PRESENSI GURU" in res_print.text

            # Ekspor Rekap Excel Kepala Sekolah
            res_rekap_excel = await async_client.get("/principal/reports/export-excel", cookies=kepsek_cookies)
            assert res_rekap_excel.status_code == 200

            # =========================================================
            # C. PENGUJIAN AKSES PERAN GURU
            # =========================================================
            guru_cookies = get_auth_cookie(teacher_user)
            res_guru_dash = await async_client.get("/dashboard", cookies=guru_cookies)
            assert res_guru_dash.status_code == 200
            assert "guru" in res_guru_dash.text or "Jadwal Mengajar Anda Hari Ini" in res_guru_dash.text

            # Jadwal Mengajar Saya
            res_my_sched = await async_client.get("/teacher/my-schedules", cookies=guru_cookies)
            assert res_my_sched.status_code == 200
            assert "Jadwal Mengajar Saya" in res_my_sched.text
            assert "Matematika" in res_my_sched.text

            # Riwayat Presensi Saya
            res_my_att = await async_client.get("/teacher/my-attendance", cookies=guru_cookies)
            assert res_my_att.status_code == 200
            assert "Riwayat Presensi" in res_my_att.text

            # =========================================================
            # D. PENGUJIAN AKSES PERAN SISWA
            # =========================================================
            siswa_cookies = get_auth_cookie(student_user)
            res_siswa_dash = await async_client.get("/dashboard", cookies=siswa_cookies)
            assert res_siswa_dash.status_code == 200
            assert "siswa" in res_siswa_dash.text or "Siswa Budi" in res_siswa_dash.text

            # Jadwal Pelajaran Kelas Siswa
            res_student_sched = await async_client.get("/student/my-class-schedule", cookies=siswa_cookies)
            assert res_student_sched.status_code == 200
            assert "Jadwal Pelajaran Kelas" in res_student_sched.text

            # =========================================================
            # E. PENGUJIAN API RESTFUL MOBILE (UNTUK SMARTPHONE)
            # =========================================================
            guru_token = create_access_token(
                subject=str(teacher_user.id),
                extra_claims={"role": teacher_user.role.value, "school_id": str(teacher_user.school_id)}
            )
            headers_guru = {"Authorization": f"Bearer {guru_token}"}

            # 1. Profile Mobile Guru
            res_m_profile = await async_client.get("/api/v1/mobile/profile", headers=headers_guru)
            assert res_m_profile.status_code == 200
            res_m_json = res_m_profile.json()
            assert res_m_json["success"] is True
            assert res_m_json["data"]["email"] == teacher_user.email
            assert res_m_json["data"]["teacher_info"]["nip"] == teacher.nip

            # 2. Today Schedules Guru via Mobile
            res_m_scheds = await async_client.get("/api/v1/mobile/teacher/today-schedules", headers=headers_guru)
            assert res_m_scheds.status_code == 200
            res_scheds_json = res_m_scheds.json()
            assert res_scheds_json["success"] is True

            # 3. Guru Piket Hari Ini via Mobile
            res_m_duty = await async_client.get("/api/v1/mobile/duty-teachers/today", headers=headers_guru)
            assert res_m_duty.status_code == 200
            assert res_m_duty.json()["success"] is True

            # 4. Profile Mobile Siswa
            siswa_token = create_access_token(
                subject=str(student_user.id),
                extra_claims={"role": student_user.role.value, "school_id": str(student_user.school_id)}
            )
            headers_siswa = {"Authorization": f"Bearer {siswa_token}"}
            res_m_siswa_profile = await async_client.get("/api/v1/mobile/profile", headers=headers_siswa)
            assert res_m_siswa_profile.status_code == 200
            assert res_m_siswa_profile.json()["data"]["student_info"]["nisn"] == student.nisn

            # 5. Today Class Attendance untuk Siswa via Mobile
            res_m_siswa_class = await async_client.get("/api/v1/mobile/student/today-attendance", headers=headers_siswa)
            assert res_m_siswa_class.status_code == 200
            assert res_m_siswa_class.json()["success"] is True

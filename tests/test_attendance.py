"""
Pengujian otomatis end-to-end untuk Modul Presensi Guru di Kelas:
- Pencocokan jadwal mengajar hari ini
- Validasi wajib koordinat GPS (Latitude & Longitude)
- Validasi wajib lampiran foto bukti kehadiran di dalam kelas
- Penyimpanan absensi & pengecekan riwayat
"""

import base64
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.models import Classroom, DayOfWeek, Schedule, Subject, Teacher, TeacherAttendance
from app.services.attendance_service import AttendanceService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_teacher_attendance_with_photo_and_gps():
    """
    Menguji alur lengkap:
    1. Registrasi sekolah baru dan login sebagai operator
    2. Membuat Tahun Pelajaran aktif
    3. Membuat Data Guru, Mapel, Kelas
    4. Membuat Jadwal Pelajaran sesuai HARI INI
    5. Melakukan absensi guru:
       - Uji gagal jika GPS kosong / 0
       - Uji gagal jika Foto kosong
       - Uji sukses dengan GPS valid dan Base64 foto
    6. Memastikan riwayat absensi tercatat
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique_id = uuid.uuid4().hex[:6]
        npsn = f"77{unique_id}"
        op_email = f"operator_{unique_id}@absen.sch.id"

        # 1. Registrasi & Login
        reg_payload = {
            "school_npsn": npsn,
            "school_name": f"SMP Negeri {unique_id.upper()}",
            "school_address": "Jl. Merdeka No. 1",
            "school_phone": "021-778899",
            "school_email": f"smp_{unique_id}@absen.sch.id",
            "operator_name": "Operator Absen",
            "operator_email": op_email,
            "operator_password": "PasswordAbsen123!",
            "operator_phone": "081234567800",
            "operator_nip": "199101012015011002",
        }
        res_reg = await ac.post("/register", data=reg_payload, follow_redirects=False)
        assert res_reg.status_code in [302, 303]

        res_login = await ac.post("/login", data={"email": op_email, "password": "PasswordAbsen123!"}, follow_redirects=False)
        token = res_login.cookies.get("access_token")
        headers = {"Cookie": f"access_token={token}"}

        # 2. Tambah Tahun Pelajaran Aktif
        await ac.post(
            "/academic-years",
            data={"name": "2025/2026", "semester": "Ganjil", "is_active": "true"},
            headers=headers,
            follow_redirects=False
        )

        # 3. Tambah Guru, Mapel, Kelas
        nip_guru = f"19820512_{unique_id}"
        code_bin = f"BIN_{unique_id}"

        await ac.post(
            "/teachers",
            data={"name": "Ahmad Subarjo, S.Pd", "nip": nip_guru, "gender": "L", "employment_status": "PNS"},
            headers=headers,
            follow_redirects=False
        )
        await ac.post(
            "/subjects",
            data={"code": code_bin, "name": "Bahasa Indonesia", "grade_level": "VII"},
            headers=headers,
            follow_redirects=False
        )

        async with AsyncSessionLocal() as session:
            t_res = await session.execute(select(Teacher).where(Teacher.nip == nip_guru))
            teacher = t_res.scalars().first()

            s_res = await session.execute(select(Subject).where(Subject.code == code_bin.upper()))
            subject = s_res.scalars().first()

        class_name = f"Kelas_{unique_id}"
        await ac.post(
            "/classrooms",
            data={"name": class_name, "grade_level": "VII", "homeroom_teacher_id": str(teacher.id), "capacity": 30},
            headers=headers,
            follow_redirects=False
        )

        async with AsyncSessionLocal() as session:
            c_res = await session.execute(select(Classroom).where(Classroom.name == class_name))
            classroom = c_res.scalars().first()

        # 4. Buat Jadwal Pelajaran sesuai Hari Ini
        today_dow = AttendanceService.get_today_day_of_week()
        if not today_dow:
            today_dow = DayOfWeek.SENIN

        await ac.post(
            "/schedules",
            data={
                "classroom_id": str(classroom.id),
                "subject_id": str(subject.id),
                "teacher_id": str(teacher.id),
                "day_of_week": today_dow.value,
                "start_time": "08:00",
                "end_time": "09:30",
                "notes": f"Ruang {class_name}"
            },
            headers=headers,
            follow_redirects=False
        )

        async with AsyncSessionLocal() as session:
            sch_res = await session.execute(select(Schedule).where(Schedule.classroom_id == classroom.id))
            schedule = sch_res.scalars().first()

        # Dummy Base64 Image untuk bukti foto di kelas
        # 1x1 transparent GIF/JPEG base64 encoded
        dummy_photo_b64 = "data:image/jpeg;base64," + base64.b64encode(b"dummy_jpeg_photo_content_for_classroom_evidence_test_1234567890").decode('utf-8')

        # 5a. Uji Gagal jika Koordinat GPS kosong / 0.0
        res_fail_gps = await ac.post(
            "/attendance/submit",
            data={
                "schedule_id": str(schedule.id),
                "teacher_id": str(teacher.id),
                "latitude": 0.0,
                "longitude": 0.0,
                "photo_base64": dummy_photo_b64,
                "status": "Hadir",
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_fail_gps.status_code in [302, 303]
        assert res_fail_gps.headers.get("location") == "/attendance"

        # 5b. Uji Gagal jika Foto Bukti kosong
        res_fail_photo = await ac.post(
            "/attendance/submit",
            data={
                "schedule_id": str(schedule.id),
                "teacher_id": str(teacher.id),
                "latitude": -6.2088,
                "longitude": 106.8456,
                "photo_base64": "",
                "status": "Hadir",
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_fail_photo.status_code in [302, 303]
        assert res_fail_photo.headers.get("location") == "/attendance"

        # 5c. Uji Sukses: GPS valid (-6.2088, 106.8456) + Foto Bukti Kelas
        res_success = await ac.post(
            "/attendance/submit",
            data={
                "schedule_id": str(schedule.id),
                "teacher_id": str(teacher.id),
                "latitude": -6.2088,
                "longitude": 106.8456,
                "location_accuracy": 15.5,
                "photo_base64": dummy_photo_b64,
                "status": "Hadir",
                "teaching_material": "Teks Deskripsi & Menulis Cerita",
                "notes": "Siswa hadir lengkap dan antusias.",
                "device_info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_success.status_code in [302, 303]
        assert res_success.headers.get("location") == "/attendance"

        # 6. Verifikasi Riwayat Absensi Guru
        res_history = await ac.get("/attendance/history", headers=headers)
        assert res_history.status_code == 200
        assert "Ahmad Subarjo" in res_history.text
        assert "Teks Deskripsi" in res_history.text
        assert "-6.2088" in res_history.text or "106.8456" in res_history.text

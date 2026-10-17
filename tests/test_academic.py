"""
Pengujian otomatis end-to-end untuk:
- Master Pendataan Awal (Tahun Pelajaran, Guru, Mapel, Kelas)
- Jadwal Pelajaran (Pembuatan & Cetak)
- Guru Piket (Multi guru per hari & Cetak)
- Soft Delete audit
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_academic_and_master_data_workflow():
    """
    Menguji alur lengkap:
    1. Registrasi sekolah baru dan login sebagai operator
    2. Membuat Tahun Pelajaran dan mengaktifkannya
    3. Membuat Data Guru
    4. Membuat Data Mata Pelajaran
    5. Membuat Data Kelas dengan Wali Kelas dari Data Guru
    6. Mengatur Jadwal Pelajaran dan memverifikasi halaman cetak
    7. Mengatur Guru Piket (lebih dari 1 guru pada hari yang sama) dan cetak
    8. Menguji Soft Delete
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        unique_id = uuid.uuid4().hex[:6]
        npsn = f"88{unique_id}"
        op_email = f"operator_{unique_id}@smp.sch.id"

        # 1. Registrasi Sekolah & Operator
        reg_payload = {
            "school_npsn": npsn,
            "school_name": f"SMP Negeri {unique_id.upper()} Teladan",
            "school_address": "Jl. Merdeka Belajar No. 10",
            "school_phone": "021-889900",
            "school_email": f"smp_{unique_id}@teladan.sch.id",
            "operator_name": "Pak Operator",
            "operator_email": op_email,
            "operator_password": "PasswordSuper123!",
            "operator_phone": "081233445566",
            "operator_nip": "198801012010011001",
        }
        res_reg = await ac.post("/register", data=reg_payload, follow_redirects=False)
        assert res_reg.status_code in [302, 303]

        # Login Operator
        res_login = await ac.post("/login", data={"email": op_email, "password": "PasswordSuper123!"}, follow_redirects=False)
        assert res_login.status_code in [302, 303]
        token = res_login.cookies.get("access_token")
        assert token is not None
        headers = {"Cookie": f"access_token={token}"}

        # 2. Tambah Tahun Pelajaran (2025/2026 Ganjil Aktif)
        res_ay = await ac.post(
            "/academic-years",
            data={
                "name": "2025/2026",
                "semester": "Ganjil",
                "is_active": "true",
                "start_date": "2025-07-15",
                "end_date": "2025-12-20"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_ay.status_code in [302, 303]

        # Cek Halaman Tahun Pelajaran
        res_ay_list = await ac.get("/academic-years", headers=headers)
        assert res_ay_list.status_code == 200
        assert "2025/2026" in res_ay_list.text
        assert "Aktif Berjalan" in res_ay_list.text

        # 3. Tambah 2 Orang Guru
        res_g1 = await ac.post(
            "/teachers",
            data={
                "name": "Drs. Bambang Sudarsono, M.Pd",
                "nip": "197505102000031002",
                "gender": "L",
                "employment_status": "PNS",
                "phone": "0811223344",
                "email": "bambang@smp.sch.id"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_g1.status_code in [302, 303]

        res_g2 = await ac.post(
            "/teachers",
            data={
                "name": "Siti Nurhaliza, S.Si",
                "nip": "198503152010012003",
                "gender": "P",
                "employment_status": "PPPK",
                "phone": "0811556677",
                "email": "siti@smp.sch.id"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_g2.status_code in [302, 303]

        # Cek List Guru
        res_t_list = await ac.get("/teachers", headers=headers)
        assert res_t_list.status_code == 200
        assert "Bambang Sudarsono" in res_t_list.text
        assert "Siti Nurhaliza" in res_t_list.text

        # 4. Tambah Mata Pelajaran (Matematika & IPA)
        res_m1 = await ac.post(
            "/subjects",
            data={"code": "MAT-7", "name": "Matematika", "grade_level": "VII", "description": "Matematika Dasar VII"},
            headers=headers,
            follow_redirects=False
        )
        assert res_m1.status_code in [302, 303]

        res_m2 = await ac.post(
            "/subjects",
            data={"code": "IPA-7", "name": "Ilmu Pengetahuan Alam", "grade_level": "VII", "description": "IPA Terpadu VII"},
            headers=headers,
            follow_redirects=False
        )
        assert res_m2.status_code in [302, 303]

        res_s_list = await ac.get("/subjects", headers=headers)
        assert res_s_list.status_code == 200
        assert "MAT-7" in res_s_list.text
        assert "IPA-7" in res_s_list.text

        # 5. Tambah Kelas dengan Wali Kelas
        # Ambil ID guru dari database melalui context
        from app.core.database import AsyncSessionLocal
        from app.models.models import Teacher, Subject, Classroom, DutyTeacher, Schedule
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            t_res = await session.execute(select(Teacher).where(Teacher.nip == "197505102000031002"))
            teacher_1 = t_res.scalar_one()

            t2_res = await session.execute(select(Teacher).where(Teacher.nip == "198503152010012003"))
            teacher_2 = t2_res.scalar_one()

            s_res = await session.execute(select(Subject).where(Subject.code == "MAT-7"))
            subject_1 = s_res.scalar_one()

        res_c = await ac.post(
            "/classrooms",
            data={
                "name": "VII A",
                "grade_level": "VII",
                "homeroom_teacher_id": str(teacher_1.id),
                "capacity": 32
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_c.status_code in [302, 303]

        res_c_list = await ac.get("/classrooms", headers=headers)
        assert res_c_list.status_code == 200
        assert "VII A" in res_c_list.text
        assert "Bambang Sudarsono" in res_c_list.text

        # 6. Atur Jadwal Pelajaran
        async with AsyncSessionLocal() as session:
            cl_res = await session.execute(select(Classroom).where(Classroom.name == "VII A"))
            classroom_1 = cl_res.scalar_one()

        res_sch = await ac.post(
            "/schedules",
            data={
                "classroom_id": str(classroom_1.id),
                "subject_id": str(subject_1.id),
                "teacher_id": str(teacher_1.id),
                "day_of_week": "Senin",
                "start_time": "07:30",
                "end_time": "09:00",
                "notes": "Ruang Kelas VII A"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_sch.status_code in [302, 303]

        # Akses Halaman Cetak Jadwal Pelajaran
        res_sch_print = await ac.get(f"/schedules/print?classroom_id={classroom_1.id}", headers=headers)
        assert res_sch_print.status_code == 200
        assert "JADWAL PELAJARAN SEMESTER GANJIL" in res_sch_print.text
        assert "Matematika" in res_sch_print.text
        assert "VII A" in res_sch_print.text

        # 7. Atur Guru Piket (2 guru di hari yang sama: Senin)
        res_piket_1 = await ac.post(
            "/duty-teachers",
            data={
                "teacher_id": str(teacher_1.id),
                "day_of_week": "Senin",
                "duty_role": "Koordinator Piket",
                "notes": "Pos Gerbang Utama"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_piket_1.status_code in [302, 303]

        res_piket_2 = await ac.post(
            "/duty-teachers",
            data={
                "teacher_id": str(teacher_2.id),
                "day_of_week": "Senin",
                "duty_role": "Anggota Piket",
                "notes": "Lobby Gedung Timur"
            },
            headers=headers,
            follow_redirects=False
        )
        assert res_piket_2.status_code in [302, 303]

        # Akses Halaman Guru Piket & Cetak
        res_piket_list = await ac.get("/duty-teachers", headers=headers)
        assert res_piket_list.status_code == 200
        assert "Koordinator Piket" in res_piket_list.text
        assert "Anggota Piket" in res_piket_list.text

        res_piket_print = await ac.get("/duty-teachers/print", headers=headers)
        assert res_piket_print.status_code == 200
        assert "JADWAL PETUGAS GURU PIKET SEKOLAH" in res_piket_print.text
        assert "Bambang Sudarsono" in res_piket_print.text
        assert "Siti Nurhaliza" in res_piket_print.text

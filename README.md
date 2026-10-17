# PresensiPintar - Sistem Absensi SMP Terpadu (Multi-Tenant)

Aplikasi Presensi Kehadiran Guru & Siswa Sekolah Menengah Pertama (SMP) berbasis Web dengan arsitektur modern super cepat, mengutamakan keamanan standar industri, dan mendukung multi-sekolah (multi-tenant).

## 🚀 Stack Teknologi
- **Backend**: Python 3.10+ & FastAPI (Asynchronous Web Framework)
- **Database**: PostgreSQL 16 dengan SQLAlchemy ORM (AsyncPG Engine)
- **UI / Frontend**: CoreUI Free Bootstrap Admin Template v5.5.0 + Jinja2 Template Engine
- **Keamanan**:
  - UUID v4 untuk Primary Key (Mencegah serangan ID enumeration)
  - Bcrypt password hashing
  - JWT (JSON Web Token) dengan HttpOnly Cookies & SameSite CSRF protection
  - Pydantic v2 DTO validation (Mencegah injection attack)
  - Role-Based Access Control (RBAC) 5 Level

## 👥 Peran Pengguna (Roles)
1. **Super Admin**: Otoritas global, mengelola semua data sekolah terdaftar.
2. **Operator Sekolah**: Administrator utama sekolah yang didaftarkan.
3. **Kepala Sekolah**: Akses monitoring kehadiran dan rekapitulasi.
4. **Guru**: Pencatatan presensi kehadiran dan pengajaran.
5. **Siswa**: Presensi kehadiran siswa (tahap lanjutan).

## 📁 Struktur Direktori
```text
aplikasi-absensi-untuk-smp/
├── app/
│   ├── api/
│   │   ├── deps.py              # Auth & RBAC Dependencies
│   │   └── v1/
│   │       └── auth.py          # RESTful JSON API
│   ├── core/
│   │   ├── config.py            # Konfigurasi Pydantic Settings & .env
│   │   ├── database.py          # SQLAlchemy AsyncPG & Sync Engine
│   │   ├── init_db.py           # Auto-migrate tabel & Seeder Superadmin
│   │   └── security.py          # Hashing bcrypt & JWT handler
│   ├── models/
│   │   └── models.py            # Model School & User (UUID v4)
│   ├── routers/
│   │   └── web_routes.py        # Web Controller (Login, Register, Dashboard, Schools)
│   ├── schemas/
│   │   └── schemas.py           # Pydantic v2 DTO Data Validation
│   ├── static/                  # Asset CoreUI (CSS, JS, Vendors, Icons)
│   └── templates/
│       ├── base.html            # Layout Utama CoreUI
│       ├── dashboard.html       # Dashboard Pengguna
│       ├── auth/
│       │   ├── login.html       # Halaman Login
│       │   └── register.html    # Halaman Registrasi Sekolah & Operator
│       └── schools/
│           └── list.html        # Daftar Sekolah (Paginasi 10 data/hlm)
├── tests/
│   ├── conftest.py              # Test Event-loop fixture
│   └── test_auth.py             # E2E Test Auth & Registration
├── .env.example                 # Template Environment Variable
├── requirements.txt             # Dependensi Python
└── README.md
```

## ⚙️ Cara Menjalankan Proyek

1. **Persiapan Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Pengaturan Konfigurasi (.env)**:
   Salin `.env.example` menjadi `.env` dan sesuaikan koneksi database PostgreSQL Anda.

3. **Jalankan Server Development**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Akses Aplikasi**:
   - Web App: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Swagger API Docs: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
   - Akun Bawaan Super Admin: `superadmin@absensi.go.id` / `SuperAdmin123!`

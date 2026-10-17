"""
Model-model basis data relasional menggunakan SQLAlchemy.
Menerapkan UUID v4 untuk identifikasi unik yang aman dan anti enumerasi.
Mendukung timestamp audit trail (created_at, updated_at) dan Soft Delete (deleted_at).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, Enum):
    """
    Daftar peran pengguna (Role-Based Access Control).
    """
    SUPERADMIN = "superadmin"
    OPERATOR_SEKOLAH = "operator_sekolah"
    KEPALA_SEKOLAH = "kepala_sekolah"
    GURU = "guru"
    SISWA = "siswa"


class DayOfWeek(str, Enum):
    """
    Hari dalam sepekan untuk jadwal pelajaran dan piket.
    """
    SENIN = "Senin"
    SELASA = "Selasa"
    RABU = "Rabu"
    KAMIS = "Kamis"
    JUMAT = "Jumat"
    SABTU = "Sabtu"


class AttendanceStatus(str, Enum):
    """
    Status kehadiran guru di kelas sesuai jadwal.
    """
    HADIR = "Hadir"
    IZIN = "Izin"
    SAKIT = "Sakit"
    ALPA = "Alpa"


class School(Base):
    """
    Tabel data sekolah yang terdaftar dalam sistem multi-tenant.
    """
    __tablename__ = "schools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    npsn = Column(String(20), unique=True, index=True, nullable=False)  # Nomor Pokok Sekolah Nasional
    name = Column(String(255), nullable=False)                         # Nama Sekolah
    education_level = Column(String(50), default="SMP", nullable=False) # Jenjang (SMP/MTs)
    address = Column(Text, nullable=True)                              # Alamat Lengkap
    phone = Column(String(30), nullable=True)                          # No Telepon Sekolah
    email = Column(String(255), nullable=True)                         # Email Resmi Sekolah
    is_active = Column(Boolean, default=True, nullable=False)          # Status Aktif Sekolah

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="school", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    classrooms = relationship("Classroom", back_populates="school", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="school", cascade="all, delete-orphan")
    duty_teachers = relationship("DutyTeacher", back_populates="school", cascade="all, delete-orphan")


class User(Base):
    """
    Tabel pengguna sistem dengan role-based access control.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Identitas & Autentikasi
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR_SEKOLAH, nullable=False, index=True)
    
    # Data Tambahan
    nip = Column(String(50), nullable=True, index=True)   # Nomor Induk Pegawai
    phone = Column(String(30), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # Status Akun
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="users")


class AcademicYear(Base):
    """
    Tabel data Tahun Pelajaran aktif satu tahunan (misal: 2024/2025).
    Menjadi acuan operasional absensi, jadwal pelajaran, dan piket.
    """
    __tablename__ = "academic_years"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(50), nullable=False)             # Contoh: "2024/2025"
    semester = Column(String(20), default="Ganjil", nullable=False) # "Ganjil" / "Genap"
    is_active = Column(Boolean, default=False, nullable=False, index=True) # Hanya 1 yang aktif per sekolah
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="academic_years")
    classrooms = relationship("Classroom", back_populates="academic_year", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="academic_year", cascade="all, delete-orphan")
    duty_teachers = relationship("DutyTeacher", back_populates="academic_year", cascade="all, delete-orphan")


class Teacher(Base):
    """
    Tabel data Guru di sekolah.
    """
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    nip = Column(String(50), nullable=True, index=True)   # NIP/NUPTK
    name = Column(String(255), nullable=False)           # Nama Guru Lengkap dengan Gelar
    gender = Column(String(10), nullable=True)           # L / P
    phone = Column(String(30), nullable=True)            # Kontak WA/Telp
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    employment_status = Column(String(50), default="PNS", nullable=True) # PNS / PPPK / Honorer
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="teachers")
    user = relationship("User")
    classrooms_as_wali = relationship("Classroom", back_populates="homeroom_teacher")
    schedules = relationship("Schedule", back_populates="teacher")
    duty_assignments = relationship("DutyTeacher", back_populates="teacher")


class Subject(Base):
    """
    Tabel data Mata Pelajaran (Mapel) SMP.
    """
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    code = Column(String(50), nullable=False, index=True) # Contoh: "BIN-7", "MAT-8"
    name = Column(String(255), nullable=False)           # Contoh: "Bahasa Indonesia", "Matematika"
    grade_level = Column(String(10), nullable=True)      # "VII", "VIII", "IX" atau "Semua"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="subjects")
    schedules = relationship("Schedule", back_populates="subject")


class Classroom(Base):
    """
    Tabel data Rombongan Belajar / Kelas SMP (VII A, VIII B, IX C, dsb).
    Wali kelas bersumber dari data guru (teacher).
    """
    __tablename__ = "classrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    homeroom_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(50), nullable=False)           # Contoh: "VII A", "VIII B", "IX 1"
    grade_level = Column(String(10), nullable=False)    # "VII", "VIII", "IX"
    capacity = Column(Integer, default=32, nullable=True) # Kapasitas siswa per kelas
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="classrooms")
    academic_year = relationship("AcademicYear", back_populates="classrooms")
    homeroom_teacher = relationship("Teacher", back_populates="classrooms_as_wali")
    schedules = relationship("Schedule", back_populates="classroom", cascade="all, delete-orphan")


class Schedule(Base):
    """
    Tabel data Jadwal Pelajaran (per Tahun Pelajaran aktif).
    Menghubungkan Hari, Jam, Kelas, Mata Pelajaran, dan Guru Pengampu.
    """
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)

    day_of_week = Column(SQLEnum(DayOfWeek), nullable=False, index=True) # Hari (Senin - Sabtu)
    start_time = Column(Time, nullable=False)                            # Contoh: 07:30
    end_time = Column(Time, nullable=False)                              # Contoh: 09:00
    period_number = Column(Integer, nullable=True)                       # Jam Ke- (1, 2, 3...)
    notes = Column(String(255), nullable=True)                           # Catatan tambahan / ruang lab dsb

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="schedules")
    academic_year = relationship("AcademicYear", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    subject = relationship("Subject", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")


class DutyTeacher(Base):
    """
    Tabel data Guru Piket Harian.
    Dapat diatur 1 guru atau lebih per hari pada Tahun Pelajaran aktif.
    """
    __tablename__ = "duty_teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)

    day_of_week = Column(SQLEnum(DayOfWeek), nullable=False, index=True) # Hari Piket (Senin - Sabtu)
    duty_role = Column(String(100), default="Guru Piket Utama", nullable=True) # Peran: Koordinator / Anggota
    notes = Column(String(255), nullable=True)

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School", back_populates="duty_teachers")
    academic_year = relationship("AcademicYear", back_populates="duty_teachers")
    teacher = relationship("Teacher", back_populates="duty_assignments")


class TeacherAttendance(Base):
    """
    Tabel data Presensi Kehadiran Guru di Kelas sesuai Jadwal Pelajaran.
    Dilengkapi bukti foto kamera langsung di dalam kelas dan auto geolocation (GPS).
    """
    __tablename__ = "teacher_attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)

    attendance_date = Column(Date, nullable=False, index=True)            # Tanggal presensi dilakukan
    attendance_time = Column(Time, nullable=False)                         # Waktu presensi dicatat
    status = Column(SQLEnum(AttendanceStatus), default=AttendanceStatus.HADIR, nullable=False)

    # Bukti Kehadiran Visual (Foto Kamera di Kelas)
    photo_url = Column(String(500), nullable=True)                        # Lokasi file foto bukti kehadiran

    # Geolocation GPS Koordinat (Otomatis ditangkap oleh sistem)
    latitude = Column(Float, nullable=False)                               # Titik Lintang GPS
    longitude = Column(Float, nullable=False)                              # Titik Bujur GPS
    location_accuracy = Column(Float, nullable=True)                       # Akurasi perangkat (dalam meter)
    device_info = Column(String(255), nullable=True)                       # User Agent / Device info

    teaching_material = Column(String(255), nullable=True)                 # Materi Pokok Pembelajaran
    notes = Column(Text, nullable=True)                                    # Catatan jurnal guru di kelas

    # Audit trail & Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relasi
    school = relationship("School")
    academic_year = relationship("AcademicYear")
    schedule = relationship("Schedule")
    teacher = relationship("Teacher")

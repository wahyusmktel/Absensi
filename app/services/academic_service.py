"""
Layanan Basis Data untuk Master Data (Pendataan Awal), Jadwal Pelajaran, dan Guru Piket.
Menerapkan Soft Delete, Filter Tenant Sekolah, dan Relasi Antar-Entitas.
"""

from datetime import datetime, time, timezone
from math import ceil
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AcademicYear,
    Classroom,
    DayOfWeek,
    DutyTeacher,
    Schedule,
    School,
    Subject,
    Teacher,
    User,
    UserRole,
)


class AcademicYearService:
    """
    Layanan pengelolaan data Tahun Pelajaran.
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[AcademicYear], int, int]:
        query = select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.deleted_at.is_(None)
        )
        if search:
            query = query.where(AcademicYear.name.ilike(f"%{search.strip()}%"))

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(AcademicYear.created_at.desc()).offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_active(db: AsyncSession, school_id: UUID) -> Optional[AcademicYear]:
        """
        Mengambil tahun pelajaran yang sedang aktif untuk sekolah tertentu.
        """
        query = select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_active.is_(True),
            AcademicYear.deleted_at.is_(None)
        )
        res = await db.execute(query)
        return res.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        name: str,
        semester: str,
        is_active: bool,
        start_date=None,
        end_date=None
    ) -> AcademicYear:
        # Jika diset aktif, nonaktifkan tahun pelajaran lain di sekolah yang sama
        if is_active:
            await db.execute(
                update(AcademicYear)
                .where(AcademicYear.school_id == school_id)
                .values(is_active=False)
            )

        ay = AcademicYear(
            school_id=school_id,
            name=name.strip(),
            semester=semester.strip(),
            is_active=is_active,
            start_date=start_date,
            end_date=end_date
        )
        db.add(ay)
        await db.commit()
        await db.refresh(ay)
        return ay

    @staticmethod
    async def set_active(db: AsyncSession, school_id: UUID, ay_id: UUID) -> bool:
        """
        Mengaktifkan satu tahun pelajaran dan menonaktifkan yang lain.
        """
        await db.execute(
            update(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .values(is_active=False)
        )
        await db.execute(
            update(AcademicYear)
            .where(AcademicYear.school_id == school_id, AcademicYear.id == ay_id)
            .values(is_active=True)
        )
        await db.commit()
        return True

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, ay_id: UUID) -> bool:
        query = select(AcademicYear).where(
            AcademicYear.id == ay_id,
            AcademicYear.school_id == school_id,
            AcademicYear.deleted_at.is_(None)
        )
        res = await db.execute(query)
        ay = res.scalar_one_or_none()
        if ay:
            ay.deleted_at = datetime.now(timezone.utc)
            if ay.is_active:
                ay.is_active = False
            await db.commit()
            return True
        return False


class TeacherService:
    """
    Layanan pengelolaan data Guru.
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[Teacher], int, int]:
        query = select(Teacher).where(
            Teacher.school_id == school_id,
            Teacher.deleted_at.is_(None)
        )
        if search:
            query = query.where(
                (Teacher.name.ilike(f"%{search.strip()}%")) |
                (Teacher.nip.ilike(f"%{search.strip()}%"))
            )

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(Teacher.name.asc()).offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_all_active(db: AsyncSession, school_id: UUID) -> List[Teacher]:
        """
        Mengambil semua guru aktif untuk opsi dropdown pilihan.
        """
        query = select(Teacher).where(
            Teacher.school_id == school_id,
            Teacher.is_active.is_(True),
            Teacher.deleted_at.is_(None)
        ).order_by(Teacher.name.asc())
        res = await db.execute(query)
        return res.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        name: str,
        nip: Optional[str] = None,
        gender: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        employment_status: Optional[str] = "PNS"
    ) -> Teacher:
        teacher = Teacher(
            school_id=school_id,
            name=name.strip(),
            nip=nip.strip() if nip else None,
            gender=gender,
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            address=address.strip() if address else None,
            employment_status=employment_status,
            is_active=True
        )
        db.add(teacher)
        await db.commit()
        await db.refresh(teacher)
        return teacher

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, teacher_id: UUID) -> bool:
        query = select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.school_id == school_id,
            Teacher.deleted_at.is_(None)
        )
        res = await db.execute(query)
        t = res.scalar_one_or_none()
        if t:
            t.deleted_at = datetime.now(timezone.utc)
            t.is_active = False
            await db.commit()
            return True
        return False


class SubjectService:
    """
    Layanan pengelolaan data Mata Pelajaran (Mapel).
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[Subject], int, int]:
        query = select(Subject).where(
            Subject.school_id == school_id,
            Subject.deleted_at.is_(None)
        )
        if search:
            query = query.where(
                (Subject.name.ilike(f"%{search.strip()}%")) |
                (Subject.code.ilike(f"%{search.strip()}%"))
            )

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(Subject.name.asc()).offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_all_active(db: AsyncSession, school_id: UUID) -> List[Subject]:
        query = select(Subject).where(
            Subject.school_id == school_id,
            Subject.is_active.is_(True),
            Subject.deleted_at.is_(None)
        ).order_by(Subject.name.asc())
        res = await db.execute(query)
        return res.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        code: str,
        name: str,
        grade_level: str = "Semua",
        description: Optional[str] = None
    ) -> Subject:
        subject = Subject(
            school_id=school_id,
            code=code.strip().upper(),
            name=name.strip(),
            grade_level=grade_level,
            description=description.strip() if description else None,
            is_active=True
        )
        db.add(subject)
        await db.commit()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, subject_id: UUID) -> bool:
        query = select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == school_id,
            Subject.deleted_at.is_(None)
        )
        res = await db.execute(query)
        s = res.scalar_one_or_none()
        if s:
            s.deleted_at = datetime.now(timezone.utc)
            s.is_active = False
            await db.commit()
            return True
        return False


class ClassroomService:
    """
    Layanan pengelolaan data Kelas dan penetapan Wali Kelas.
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[Classroom], int, int]:
        query = select(Classroom).options(
            selectinload(Classroom.homeroom_teacher),
            selectinload(Classroom.academic_year)
        ).where(
            Classroom.school_id == school_id,
            Classroom.deleted_at.is_(None)
        )
        if academic_year_id:
            query = query.where(Classroom.academic_year_id == academic_year_id)
        if search:
            query = query.where(Classroom.name.ilike(f"%{search.strip()}%"))

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(Classroom.grade_level.asc(), Classroom.name.asc()).offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_all_active(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> List[Classroom]:
        query = select(Classroom).where(
            Classroom.school_id == school_id,
            Classroom.is_active.is_(True),
            Classroom.deleted_at.is_(None)
        )
        if academic_year_id:
            query = query.where(Classroom.academic_year_id == academic_year_id)
        res = await db.execute(query.order_by(Classroom.grade_level.asc(), Classroom.name.asc()))
        return res.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        name: str,
        grade_level: str,
        homeroom_teacher_id: Optional[UUID] = None,
        capacity: int = 32
    ) -> Classroom:
        classroom = Classroom(
            school_id=school_id,
            academic_year_id=academic_year_id,
            name=name.strip(),
            grade_level=grade_level.strip(),
            homeroom_teacher_id=homeroom_teacher_id,
            capacity=capacity,
            is_active=True
        )
        db.add(classroom)
        await db.commit()
        await db.refresh(classroom)
        return classroom

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, classroom_id: UUID) -> bool:
        query = select(Classroom).where(
            Classroom.id == classroom_id,
            Classroom.school_id == school_id,
            Classroom.deleted_at.is_(None)
        )
        res = await db.execute(query)
        c = res.scalar_one_or_none()
        if c:
            c.deleted_at = datetime.now(timezone.utc)
            c.is_active = False
            await db.commit()
            return True
        return False


class ScheduleService:
    """
    Layanan pengelolaan data Jadwal Pelajaran (per Tahun Pelajaran aktif).
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        classroom_id: Optional[UUID] = None,
        day_of_week: Optional[DayOfWeek] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Schedule], int, int]:
        query = select(Schedule).options(
            selectinload(Schedule.classroom),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher)
        ).where(
            Schedule.school_id == school_id,
            Schedule.academic_year_id == academic_year_id,
            Schedule.deleted_at.is_(None)
        )
        if classroom_id:
            query = query.where(Schedule.classroom_id == classroom_id)
        if day_of_week:
            query = query.where(Schedule.day_of_week == day_of_week)

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(Schedule.day_of_week.asc(), Schedule.start_time.asc())
            .offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_all_for_print(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        classroom_id: Optional[UUID] = None
    ) -> List[Schedule]:
        """
        Mengambil jadwal pelajaran lengkap untuk halaman cetak.
        """
        query = select(Schedule).options(
            selectinload(Schedule.classroom),
            selectinload(Schedule.subject),
            selectinload(Schedule.teacher)
        ).where(
            Schedule.school_id == school_id,
            Schedule.academic_year_id == academic_year_id,
            Schedule.deleted_at.is_(None)
        )
        if classroom_id:
            query = query.where(Schedule.classroom_id == classroom_id)

        res = await db.execute(query.order_by(Schedule.day_of_week.asc(), Schedule.start_time.asc()))
        return res.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        classroom_id: UUID,
        subject_id: UUID,
        teacher_id: UUID,
        day_of_week: DayOfWeek,
        start_time: time,
        end_time: time,
        period_number: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Schedule:
        sched = Schedule(
            school_id=school_id,
            academic_year_id=academic_year_id,
            classroom_id=classroom_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            period_number=period_number,
            notes=notes.strip() if notes else None
        )
        db.add(sched)
        await db.commit()
        await db.refresh(sched)
        return sched

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, schedule_id: UUID) -> bool:
        query = select(Schedule).where(
            Schedule.id == schedule_id,
            Schedule.school_id == school_id,
            Schedule.deleted_at.is_(None)
        )
        res = await db.execute(query)
        s = res.scalar_one_or_none()
        if s:
            s.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        return False


class DutyTeacherService:
    """
    Layanan pengelolaan data Guru Piket Harian.
    Dapat diatur 1 guru atau lebih per hari pada Tahun Pelajaran aktif.
    """

    @staticmethod
    async def get_list(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        day_of_week: Optional[DayOfWeek] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[DutyTeacher], int, int]:
        query = select(DutyTeacher).options(
            selectinload(DutyTeacher.teacher)
        ).where(
            DutyTeacher.school_id == school_id,
            DutyTeacher.academic_year_id == academic_year_id,
            DutyTeacher.deleted_at.is_(None)
        )
        if day_of_week:
            query = query.where(DutyTeacher.day_of_week == day_of_week)

        total_res = await db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total_res.scalar() or 0
        total_pages = ceil(total_count / limit) if total_count > 0 else 1

        offset = (page - 1) * limit
        items_res = await db.execute(
            query.order_by(DutyTeacher.day_of_week.asc()).offset(offset).limit(limit)
        )
        return items_res.scalars().all(), total_count, total_pages

    @staticmethod
    async def get_all_for_print(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID
    ) -> List[DutyTeacher]:
        query = select(DutyTeacher).options(
            selectinload(DutyTeacher.teacher)
        ).where(
            DutyTeacher.school_id == school_id,
            DutyTeacher.academic_year_id == academic_year_id,
            DutyTeacher.deleted_at.is_(None)
        ).order_by(DutyTeacher.day_of_week.asc())
        res = await db.execute(query)
        return res.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession,
        school_id: UUID,
        academic_year_id: UUID,
        teacher_id: UUID,
        day_of_week: DayOfWeek,
        duty_role: str = "Guru Piket Utama",
        notes: Optional[str] = None
    ) -> DutyTeacher:
        duty = DutyTeacher(
            school_id=school_id,
            academic_year_id=academic_year_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            duty_role=duty_role.strip(),
            notes=notes.strip() if notes else None
        )
        db.add(duty)
        await db.commit()
        await db.refresh(duty)
        return duty

    @staticmethod
    async def soft_delete(db: AsyncSession, school_id: UUID, duty_id: UUID) -> bool:
        query = select(DutyTeacher).where(
            DutyTeacher.id == duty_id,
            DutyTeacher.school_id == school_id,
            DutyTeacher.deleted_at.is_(None)
        )
        res = await db.execute(query)
        d = res.scalar_one_or_none()
        if d:
            d.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        return False

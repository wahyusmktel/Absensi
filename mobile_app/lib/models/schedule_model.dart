/// Model Jadwal Mengajar Guru Hari Ini & Status Presensi
class TeacherTodayScheduleModel {
  final String scheduleId;
  final int? periodNumber;
  final String startTime;
  final String endTime;
  final String subjectName;
  final String classroomName;
  final String gradeLevel;
  final bool isAttended;
  final AttendanceSummary? attendance;

  TeacherTodayScheduleModel({
    required this.scheduleId,
    this.periodNumber,
    required this.startTime,
    required this.endTime,
    required this.subjectName,
    required this.classroomName,
    required this.gradeLevel,
    required this.isAttended,
    this.attendance,
  });

  factory TeacherTodayScheduleModel.fromJson(Map<String, dynamic> json) {
    return TeacherTodayScheduleModel(
      scheduleId: json['schedule_id'] ?? '',
      periodNumber: json['period_number'],
      startTime: json['start_time'] ?? '',
      endTime: json['end_time'] ?? '',
      subjectName: json['subject_name'] ?? '-',
      classroomName: json['classroom_name'] ?? '-',
      gradeLevel: json['grade_level'] ?? '-',
      isAttended: json['is_attended'] ?? false,
      attendance: json['attendance'] != null
          ? AttendanceSummary.fromJson(json['attendance'])
          : null,
    );
  }
}

class AttendanceSummary {
  final String? id;
  final String status;
  final String? checkInTime;
  final String? photoUrl;
  final String? teachingMaterial;

  AttendanceSummary({
    this.id,
    required this.status,
    this.checkInTime,
    this.photoUrl,
    this.teachingMaterial,
  });

  factory AttendanceSummary.fromJson(Map<String, dynamic> json) {
    return AttendanceSummary(
      id: json['id'],
      status: json['status'] ?? 'belum_hadir',
      checkInTime: json['check_in_time'],
      photoUrl: json['photo_url'],
      teachingMaterial: json['teaching_material'],
    );
  }
}

/// Model Jadwal Pelajaran Kelas untuk Siswa Hari Ini & Real-Time Status Guru
class StudentTodayClassModel {
  final String scheduleId;
  final int? periodNumber;
  final String startTime;
  final String endTime;
  final String subjectName;
  final String teacherName;
  final bool isAttended;
  final String attendanceStatus;
  final String? checkInTime;

  StudentTodayClassModel({
    required this.scheduleId,
    this.periodNumber,
    required this.startTime,
    required this.endTime,
    required this.subjectName,
    required this.teacherName,
    required this.isAttended,
    required this.attendanceStatus,
    this.checkInTime,
  });

  factory StudentTodayClassModel.fromJson(Map<String, dynamic> json) {
    return StudentTodayClassModel(
      scheduleId: json['schedule_id'] ?? '',
      periodNumber: json['period_number'],
      startTime: json['start_time'] ?? '',
      endTime: json['end_time'] ?? '',
      subjectName: json['subject_name'] ?? '-',
      teacherName: json['teacher_name'] ?? '-',
      isAttended: json['is_attended'] ?? false,
      attendanceStatus: json['attendance_status'] ?? 'belum_hadir',
      checkInTime: json['check_in_time'],
    );
  }
}

/// Model Riwayat Presensi Guru
class AttendanceHistoryModel {
  final String id;
  final String date;
  final String? checkInTime;
  final String status;
  final String? photoUrl;
  final String classroomName;
  final String subjectName;
  final String? teachingMaterial;
  final double? latitude;
  final double? longitude;
  final bool? isWithinRadius;

  AttendanceHistoryModel({
    required this.id,
    required this.date,
    this.checkInTime,
    required this.status,
    this.photoUrl,
    required this.classroomName,
    required this.subjectName,
    this.teachingMaterial,
    this.latitude,
    this.longitude,
    this.isWithinRadius,
  });

  factory AttendanceHistoryModel.fromJson(Map<String, dynamic> json) {
    return AttendanceHistoryModel(
      id: json['id'] ?? '',
      date: json['date'] ?? '',
      checkInTime: json['check_in_time'],
      status: json['status'] ?? 'Hadir',
      photoUrl: json['photo_url'],
      classroomName: json['classroom_name'] ?? '-',
      subjectName: json['subject_name'] ?? '-',
      teachingMaterial: json['teaching_material'],
      latitude: json['latitude'] != null ? (json['latitude'] as num).toDouble() : null,
      longitude: json['longitude'] != null ? (json['longitude'] as num).toDouble() : null,
      isWithinRadius: json['is_within_radius'],
    );
  }
}

/// Model Guru Piket Hari Ini
class DutyTeacherModel {
  final String id;
  final String name;
  final String? nip;
  final String? phone;
  final String? notes;

  DutyTeacherModel({
    required this.id,
    required this.name,
    this.nip,
    this.phone,
    this.notes,
  });

  factory DutyTeacherModel.fromJson(Map<String, dynamic> json) {
    return DutyTeacherModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      nip: json['nip'],
      phone: json['phone'],
      notes: json['notes'],
    );
  }
}

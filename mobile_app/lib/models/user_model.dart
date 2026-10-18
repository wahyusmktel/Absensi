/// Model Data Profil Pengguna (Guru / Siswa / Operator / Kepsek / Superadmin)
class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String role;
  final String? nip;
  final String? phone;
  final String? schoolId;
  final TeacherInfo? teacherInfo;
  final StudentInfo? studentInfo;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.nip,
    this.phone,
    this.schoolId,
    this.teacherInfo,
    this.studentInfo,
  });

  bool get isTeacher => role == "guru";
  bool get isStudent => role == "siswa";
  bool get isPrincipal => role == "kepala_sekolah";
  bool get isOperator => role == "operator_sekolah";

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? '',
      email: json['email'] ?? '',
      fullName: json['full_name'] ?? json['name'] ?? '',
      role: json['role'] ?? '',
      nip: json['nip'],
      phone: json['phone'],
      schoolId: json['school_id'],
      teacherInfo: json['teacher_info'] != null
          ? TeacherInfo.fromJson(json['teacher_info'])
          : null,
      studentInfo: json['student_info'] != null
          ? StudentInfo.fromJson(json['student_info'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'role': role,
      'nip': nip,
      'phone': phone,
      'school_id': schoolId,
      'teacher_info': teacherInfo?.toJson(),
      'student_info': studentInfo?.toJson(),
    };
  }
}

class TeacherInfo {
  final String id;
  final String? nip;
  final String name;
  final String? gender;
  final String? phone;
  final String? employmentStatus;

  TeacherInfo({
    required this.id,
    this.nip,
    required this.name,
    this.gender,
    this.phone,
    this.employmentStatus,
  });

  factory TeacherInfo.fromJson(Map<String, dynamic> json) {
    return TeacherInfo(
      id: json['id'] ?? '',
      nip: json['nip'],
      name: json['name'] ?? '',
      gender: json['gender'],
      phone: json['phone'],
      employmentStatus: json['employment_status'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nip': nip,
      'name': name,
      'gender': gender,
      'phone': phone,
      'employment_status': employmentStatus,
    };
  }
}

class StudentInfo {
  final String id;
  final String nisn;
  final String? nis;
  final String name;
  final String? gender;
  final String? classroomId;
  final String? classroomName;

  StudentInfo({
    required this.id,
    required this.nisn,
    this.nis,
    required this.name,
    this.gender,
    this.classroomId,
    this.classroomName,
  });

  factory StudentInfo.fromJson(Map<String, dynamic> json) {
    return StudentInfo(
      id: json['id'] ?? '',
      nisn: json['nisn'] ?? '',
      nis: json['nis'],
      name: json['name'] ?? '',
      gender: json['gender'],
      classroomId: json['classroom_id'],
      classroomName: json['classroom_name'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nisn': nisn,
      'nis': nis,
      'name': name,
      'gender': gender,
      'classroom_id': classroomId,
      'classroom_name': classroomName,
    };
  }
}

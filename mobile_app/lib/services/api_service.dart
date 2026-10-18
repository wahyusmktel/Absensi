import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/attendance_model.dart';
import '../models/schedule_model.dart';
import '../models/user_model.dart';

/// Layanan Komunikasi RESTful API Backend FastAPI
class ApiService {
  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.keyCustomBaseUrl) ?? AppConstants.defaultBaseUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.keyCustomBaseUrl, url.trim());
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.keyToken);
  }

  static Future<Map<String, String>> _getHeaders() async {
    final token = await getToken();
    return {
      "Content-Type": "application/json",
      "Accept": "application/json",
      if (token != null) "Authorization": "Bearer $token",
    };
  }

  /// Autentikasi Pengguna & Dapatkan JWT Token
  static Future<Map<String, dynamic>> login(String email, String password) async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/auth/login");

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"email": email.trim(), "password": password}),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
        final token = data['access_token'];
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConstants.keyToken, token);
        return {"success": true, "token": token, "user": data['user']};
      } else {
        return {
          "success": false,
          "message": data['detail'] ?? "Login gagal. Periksa kembali email dan password Anda."
        };
      }
    } catch (e) {
      return {"success": false, "message": "Gagal terhubung ke server backend: $e"};
    }
  }

  /// Ambil Profil Pengguna Lengkap
  static Future<UserModel?> getProfile() async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/profile");
    final headers = await _getHeaders();

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return UserModel.fromJson(data['data']);
        }
      }
    } catch (_) {}
    return null;
  }

  /// Ambil Jadwal Mengajar Guru Hari Ini
  static Future<List<TeacherTodayScheduleModel>> getTeacherTodaySchedules() async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/teacher/today-schedules");
    final headers = await _getHeaders();

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true && data['data'] != null) {
          final list = data['data'] as List;
          return list.map((item) => TeacherTodayScheduleModel.fromJson(item)).toList();
        }
      }
    } catch (_) {}
    return [];
  }

  /// Submit Presensi Guru di Kelas (Foto Base64 + Koordinat GPS Wajib)
  static Future<Map<String, dynamic>> submitAttendance({
    required String scheduleId,
    required double latitude,
    required double longitude,
    required double? locationAccuracy,
    required String photoBase64,
    required String attendanceStatus,
    String? teachingMaterial,
    String? notes,
  }) async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/teacher/attendance");
    final headers = await _getHeaders();

    final payload = {
      "schedule_id": scheduleId,
      "latitude": latitude,
      "longitude": longitude,
      "location_accuracy": locationAccuracy,
      "photo_base64": photoBase64,
      "attendance_status": attendanceStatus,
      "teaching_material": teachingMaterial,
      "notes": notes,
      "device_info": "Smartphone Android / iOS Flutter App",
    };

    try {
      final response = await http.post(url, headers: headers, body: jsonEncode(payload));
      final data = jsonDecode(response.body);
      if (response.statusCode == 200) {
        return {"success": true, "message": data['message'] ?? "Presensi berhasil dikirim!"};
      } else {
        return {"success": false, "message": data['detail'] ?? "Gagal mengirim data presensi."};
      }
    } catch (e) {
      return {"success": false, "message": "Kesalahan jaringan saat mengirim presensi: $e"};
    }
  }

  /// Ambil Riwayat Presensi Guru Pribadi
  static Future<List<AttendanceHistoryModel>> getTeacherAttendanceHistory({int page = 1}) async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/teacher/attendance/history?page=$page&limit=20");
    final headers = await _getHeaders();

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true && data['data'] != null) {
          final list = data['data'] as List;
          return list.map((item) => AttendanceHistoryModel.fromJson(item)).toList();
        }
      }
    } catch (_) {}
    return [];
  }

  /// Monitoring Siswa: Ambil Jadwal & Status Kehadiran Guru di Kelas Hari Ini
  static Future<List<StudentTodayClassModel>> getStudentTodayClasses() async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/student/today-attendance");
    final headers = await _getHeaders();

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true && data['data'] != null) {
          final list = data['data'] as List;
          return list.map((item) => StudentTodayClassModel.fromJson(item)).toList();
        }
      }
    } catch (_) {}
    return [];
  }

  /// Ambil Daftar Guru Piket Hari Ini
  static Future<List<DutyTeacherModel>> getDutyTeachersToday() async {
    final baseUrl = await getBaseUrl();
    final url = Uri.parse("$baseUrl/mobile/duty-teachers/today");
    final headers = await _getHeaders();

    try {
      final response = await http.get(url, headers: headers);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true && data['data'] != null) {
          final list = data['data'] as List;
          return list.map((item) => DutyTeacherModel.fromJson(item)).toList();
        }
      }
    } catch (_) {}
    return [];
  }
}

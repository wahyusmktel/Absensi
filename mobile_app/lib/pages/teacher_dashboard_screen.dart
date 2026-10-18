import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/attendance_model.dart';
import '../models/schedule_model.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../widgets/schedule_card.dart';
import '../widgets/user_menu_bar.dart';
import 'attendance_camera_screen.dart';

/// Halaman Dashboard Utama Khusus Pendidik / Guru
class TeacherDashboardScreen extends StatefulWidget {
  final UserModel user;

  const TeacherDashboardScreen({Key? key, required this.user}) : super(key: key);

  @override
  State<TeacherDashboardScreen> createState() => _TeacherDashboardScreenState();
}

class _TeacherDashboardScreenState extends State<TeacherDashboardScreen> {
  List<TeacherTodayScheduleModel> _schedules = [];
  List<DutyTeacherModel> _dutyTeachers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    final schedules = await ApiService.getTeacherTodaySchedules();
    final duties = await ApiService.getDutyTeachersToday();

    if (mounted) {
      setState(() {
        _schedules = schedules;
        _dutyTeachers = duties;
        _isLoading = false;
      });
    }
  }

  void _openAttendanceCamera([TeacherTodayScheduleModel? schedule]) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => AttendanceCameraScreen(selectedSchedule: schedule),
      ),
    );

    if (result == true) {
      _loadDashboardData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final attendedCount = _schedules.where((s) => s.isAttended).length;

    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadDashboardData,
          color: AppConstants.primaryColor,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 1. Menu Bar Profil Pengguna
                UserMenuBar(user: widget.user),
                const SizedBox(height: 20),

                // 2. Banner Sambutan Cepat & Tombol Presensi Kamera (UI Kits Style)
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppConstants.primaryColor, AppConstants.secondaryColor],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: AppConstants.primaryColor.withOpacity(0.3),
                        blurRadius: 18,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                "Presensi Kelas",
                                style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              "Waktunya Mengajar?",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              "Ambil foto di kelas & titik koordinat GPS terverifikasi.",
                              style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 12),
                            ),
                            const SizedBox(height: 14),
                            ElevatedButton.icon(
                              onPressed: () => _openAttendanceCamera(),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: AppConstants.primaryColor,
                                elevation: 0,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                              ),
                              icon: const Icon(Icons.camera_alt_rounded, size: 16),
                              label: const Text("Buka Kamera", style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      Image.asset(
                        "assets/images/home.png",
                        width: 90,
                        height: 90,
                        errorBuilder: (_, __, ___) => const Icon(Icons.class_rounded, size: 70, color: Colors.white70),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // 3. Ringkasan Status Jam Mengajar Hari Ini
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: AppConstants.dividerColor),
                          boxShadow: AppConstants.softCardShadow,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("Total Sesi Mengajar", style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor)),
                            const SizedBox(height: 4),
                            Text(
                              "${_schedules.length} Sesi",
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(color: AppConstants.dividerColor),
                          boxShadow: AppConstants.softCardShadow,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("Sudah Presensi", style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor)),
                            const SizedBox(height: 4),
                            Text(
                              "$attendedCount Selesai",
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppConstants.hadirColor),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // 4. Daftar Jadwal Pelajaran Hari Ini
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Jadwal Mengajar Hari Ini",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                    ),
                    if (_schedules.isNotEmpty)
                      Text(
                        "${_schedules.length} Jadwal",
                        style: const TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                      ),
                  ],
                ),
                const SizedBox(height: 12),

                if (_isLoading)
                  const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
                else if (_schedules.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppConstants.dividerColor),
                    ),
                    child: Column(
                      children: [
                        const Icon(Icons.free_breakfast_outlined, size: 48, color: AppConstants.captionTextColor),
                        const SizedBox(height: 10),
                        const Text(
                          "Tidak Ada Jadwal Mengajar Hari Ini",
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Selamat beristirahat atau mengerjakan administrasi lainnya.",
                          style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  )
                else
                  ..._schedules.map((s) {
                    final statusText = s.attendance?.status ?? (s.isAttended ? "Hadir" : "Belum Hadir");
                    return ScheduleCard(
                      periodText: "Jam ke-${s.periodNumber ?? 1}",
                      timeRange: "${s.startTime} - ${s.endTime} WIB",
                      subjectName: s.subjectName,
                      classroomOrTeacher: "Kelas ${s.classroomName} (Tingkat ${s.gradeLevel})",
                      status: statusText,
                      teachingMaterial: s.attendance?.teachingMaterial,
                      showAttendanceButton: !s.isAttended,
                      onAttendancePressed: () => _openAttendanceCamera(s),
                    );
                  }).toList(),

                const SizedBox(height: 20),

                // 5. Guru Piket Hari Ini
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Petugas Guru Piket Hari Ini",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                    ),
                    if (_dutyTeachers.isNotEmpty)
                      Text(
                        "${_dutyTeachers.length} Orang",
                        style: const TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                      ),
                  ],
                ),
                const SizedBox(height: 12),

                if (_dutyTeachers.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppConstants.dividerColor),
                    ),
                    child: const Text(
                      "Belum ada guru piket yang terjadwal untuk hari ini.",
                      style: TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                    ),
                  )
                else
                  ..._dutyTeachers.map((dt) {
                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppConstants.dividerColor),
                        boxShadow: AppConstants.softCardShadow,
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: const BoxDecoration(
                              color: Color(0xFFFEF3C7),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.shield_outlined, color: Color(0xFFD97706), size: 22),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  dt.name,
                                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  dt.notes ?? "Petugas Piket Gerbang & Ketertiban",
                                  style: const TextStyle(fontSize: 12, color: AppConstants.secondaryTextColor),
                                ),
                              ],
                            ),
                          ),
                          if (dt.phone != null && dt.phone!.isNotEmpty)
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: const Color(0xFFD1FAE5),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.call_outlined, color: Color(0xFF059669), size: 18),
                            ),
                        ],
                      ),
                    );
                  }).toList(),

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/attendance_model.dart';
import '../models/schedule_model.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../widgets/schedule_card.dart';
import '../widgets/user_menu_bar.dart';
import 'student_schedule_screen.dart';

/// Halaman Dashboard Siswa / Peserta Didik
class StudentDashboardScreen extends StatefulWidget {
  final UserModel user;

  const StudentDashboardScreen({Key? key, required this.user}) : super(key: key);

  @override
  State<StudentDashboardScreen> createState() => _StudentDashboardScreenState();
}

class _StudentDashboardScreenState extends State<StudentDashboardScreen> {
  List<StudentTodayClassModel> _todayClasses = [];
  List<DutyTeacherModel> _dutyTeachers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() => _isLoading = true);
    final classes = await ApiService.getStudentTodayClasses();
    final duties = await ApiService.getDutyTeachersToday();

    if (mounted) {
      setState(() {
        _todayClasses = classes;
        _dutyTeachers = duties;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final studentInfo = widget.user.studentInfo;

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
                // 1. Menu Bar Profil Siswa
                UserMenuBar(user: widget.user),
                const SizedBox(height: 20),

                // 2. Kartu Profil Siswa & Kelas (UI Kits Style)
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF3B82F6).withOpacity(0.3),
                        blurRadius: 18,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Text(
                              "Profil Pelajar",
                              style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                            ),
                          ),
                          Text(
                            studentInfo?.classroomName != null
                                ? "Kelas ${studentInfo!.classroomName}"
                                : "Rombel Siswa",
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        widget.user.fullName,
                        style: const TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        "NISN: ${studentInfo?.nisn ?? '-'}  •  NIS: ${studentInfo?.nis ?? '-'}",
                        style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 13),
                      ),
                      const SizedBox(height: 14),
                      InkWell(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const StudentScheduleScreen()),
                          );
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.calendar_month_rounded, size: 16, color: AppConstants.primaryColor),
                              SizedBox(width: 6),
                              Text(
                                "Lihat Jadwal Mingguan",
                                style: TextStyle(color: AppConstants.primaryColor, fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // 3. Header Jadwal Pelajaran Hari Ini
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Jadwal Kelas Hari Ini",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                    ),
                    Text(
                      "${_todayClasses.length} Mapel",
                      style: const TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 4. Daftar Mata Pelajaran Hari Ini & Status Kehadiran Guru
                if (_isLoading)
                  const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
                else if (_todayClasses.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppConstants.dividerColor),
                    ),
                    child: Column(
                      children: [
                        const Icon(Icons.menu_book_rounded, size: 48, color: AppConstants.captionTextColor),
                        const SizedBox(height: 10),
                        const Text(
                          "Tidak Ada Jam Pelajaran Hari Ini",
                          style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          "Hari ini tidak ada kegiatan belajar mengajar terjadwal.",
                          style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  )
                else
                  ..._todayClasses.map((item) {
                    final status = item.isAttended ? "Hadir" : item.attendanceStatus;
                    return ScheduleCard(
                      periodText: "Jam ke-${item.periodNumber ?? 1}",
                      timeRange: "${item.startTime} - ${item.endTime} WIB",
                      subjectName: item.subjectName,
                      classroomOrTeacher: "Guru: ${item.teacherName}",
                      status: status,
                    );
                  }).toList(),

                const SizedBox(height: 20),

                // 5. Guru Piket Hari Ini
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      "Guru Piket Hari Ini",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                    ),
                    if (_dutyTeachers.isNotEmpty)
                      Text(
                        "${_dutyTeachers.length} Guru",
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
                      "Tidak ada guru piket yang terjadwal hari ini.",
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
                              color: Color(0xFFE0E7FF),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.shield_outlined, color: AppConstants.primaryColor, size: 22),
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
                                  dt.notes ?? "Piket Harian Sekolah",
                                  style: const TextStyle(fontSize: 12, color: AppConstants.secondaryTextColor),
                                ),
                              ],
                            ),
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

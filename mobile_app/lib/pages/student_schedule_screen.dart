import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/schedule_model.dart';
import '../services/api_service.dart';
import '../widgets/schedule_card.dart';

/// Halaman Jadwal Pelajaran Mingguan Kelas Siswa
class StudentScheduleScreen extends StatefulWidget {
  const StudentScheduleScreen({Key? key}) : super(key: key);

  @override
  State<StudentScheduleScreen> createState() => _StudentScheduleScreenState();
}

class _StudentScheduleScreenState extends State<StudentScheduleScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final List<String> _days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
  List<StudentTodayClassModel> _todayClasses = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _days.length, vsync: this);
    _loadSchedule();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadSchedule() async {
    setState(() => _isLoading = true);
    final classes = await ApiService.getStudentTodayClasses();
    if (mounted) {
      setState(() {
        _todayClasses = classes;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      appBar: AppBar(
        title: const Text("Jadwal Pelajaran Kelas"),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppConstants.primaryColor,
          unselectedLabelColor: AppConstants.captionTextColor,
          indicatorColor: AppConstants.primaryColor,
          indicatorWeight: 3,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
          tabs: _days.map((d) => Tab(text: d)).toList(),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: _days.map((day) {
          if (_isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          // Untuk hari ini tampilkan data riil dari backend
          return RefreshIndicator(
            onRefresh: _loadSchedule,
            color: AppConstants.primaryColor,
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppConstants.primaryLight,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline_rounded, color: AppConstants.primaryColor, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          "Jadwal kegiatan belajar mengajar kelas pada hari $day.",
                          style: const TextStyle(fontSize: 12, color: AppConstants.primaryColor, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                if (_todayClasses.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppConstants.dividerColor),
                    ),
                    child: Center(
                      child: Text(
                        "Tidak ada jam pelajaran untuk hari $day.",
                        style: const TextStyle(color: AppConstants.captionTextColor, fontSize: 13),
                      ),
                    ),
                  )
                else
                  ..._todayClasses.map((item) {
                    return ScheduleCard(
                      periodText: "Jam ke-${item.periodNumber ?? 1}",
                      timeRange: "${item.startTime} - ${item.endTime} WIB",
                      subjectName: item.subjectName,
                      classroomOrTeacher: "Guru Pengampu: ${item.teacherName}",
                      status: item.isAttended ? "Hadir" : item.attendanceStatus,
                    );
                  }).toList(),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

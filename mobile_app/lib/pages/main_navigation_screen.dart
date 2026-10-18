import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/user_model.dart';
import 'attendance_camera_screen.dart';
import 'attendance_history_screen.dart';
import 'profile_screen.dart';
import 'student_dashboard_screen.dart';
import 'student_schedule_screen.dart';
import 'teacher_dashboard_screen.dart';

/// Halaman Navigasi Utama dengan Bottom Bar Dinamis Sesuai Role Pengguna
class MainNavigationScreen extends StatefulWidget {
  final UserModel user;

  const MainNavigationScreen({Key? key, required this.user}) : super(key: key);

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  late List<Widget> _pages;
  late List<BottomNavigationBarItem> _navItems;

  @override
  void initState() {
    super.initState();
    _setupRoleNavigation();
  }

  void _setupRoleNavigation() {
    if (widget.user.isTeacher) {
      _pages = [
        TeacherDashboardScreen(user: widget.user),
        const AttendanceCameraScreen(),
        const AttendanceHistoryScreen(),
        ProfileScreen(user: widget.user),
      ];
      _navItems = const [
        BottomNavigationBarItem(
          icon: Icon(Icons.dashboard_outlined),
          activeIcon: Icon(Icons.dashboard_rounded),
          label: "Dashboard",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.camera_alt_outlined),
          activeIcon: Icon(Icons.camera_alt_rounded),
          label: "Presensi",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.history_rounded),
          activeIcon: Icon(Icons.history_edu_rounded),
          label: "Riwayat",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline_rounded),
          activeIcon: Icon(Icons.person_rounded),
          label: "Profil",
        ),
      ];
    } else if (widget.user.isStudent) {
      _pages = [
        StudentDashboardScreen(user: widget.user),
        const StudentScheduleScreen(),
        ProfileScreen(user: widget.user),
      ];
      _navItems = const [
        BottomNavigationBarItem(
          icon: Icon(Icons.home_outlined),
          activeIcon: Icon(Icons.home_rounded),
          label: "Beranda",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.calendar_month_outlined),
          activeIcon: Icon(Icons.calendar_month_rounded),
          label: "Jadwal",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline_rounded),
          activeIcon: Icon(Icons.person_rounded),
          label: "Profil",
        ),
      ];
    } else {
      // Default untuk Operator Sekolah / Kepala Sekolah / Administrator
      _pages = [
        TeacherDashboardScreen(user: widget.user),
        const AttendanceHistoryScreen(),
        ProfileScreen(user: widget.user),
      ];
      _navItems = const [
        BottomNavigationBarItem(
          icon: Icon(Icons.dashboard_outlined),
          activeIcon: Icon(Icons.dashboard_rounded),
          label: "Dashboard",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.history_rounded),
          activeIcon: Icon(Icons.history_edu_rounded),
          label: "Monitoring",
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.person_outline_rounded),
          activeIcon: Icon(Icons.person_rounded),
          label: "Profil",
        ),
      ];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          border: const Border(top: BorderSide(color: AppConstants.dividerColor, width: 0.8)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 10,
              offset: const Offset(0, -3),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() => _currentIndex = index);
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          selectedItemColor: AppConstants.primaryColor,
          unselectedItemColor: AppConstants.captionTextColor,
          selectedFontSize: 12,
          unselectedFontSize: 12,
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold),
          unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500),
          elevation: 0,
          items: _navItems,
        ),
      ),
    );
  }
}

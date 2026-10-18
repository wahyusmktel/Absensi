import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/user_model.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../widgets/custom_text_field.dart';
import 'login_screen.dart';

/// Halaman Profil Akun Pengguna & Pengaturan Sistem
class ProfileScreen extends StatelessWidget {
  final UserModel user;

  const ProfileScreen({Key? key, required this.user}) : super(key: key);

  void _showServerDialog(BuildContext context) async {
    final currentUrl = await ApiService.getBaseUrl();
    final controller = TextEditingController(text: currentUrl);

    if (!context.mounted) return;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text("Pengaturan Alamat Server", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "Sesuaikan URL API jika backend dijalankan di IP LAN / VPS:",
              style: TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor),
            ),
            const SizedBox(height: 12),
            CustomTextField(
              controller: controller,
              hintText: "http://192.168.1.100:8000/api/v1",
              labelText: "API URL",
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Batal"),
          ),
          ElevatedButton(
            onPressed: () async {
              await ApiService.setBaseUrl(controller.text.trim());
              if (context.mounted) Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Alamat server backend berhasil diubah.")),
              );
            },
            child: const Text("Simpan"),
          ),
        ],
      ),
    );
  }

  void _handleLogout(BuildContext context) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text("Konfirmasi Keluar", style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text("Apakah Anda yakin ingin keluar dari akun PresensiPintar?"),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text("Batal"),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppConstants.sakitColor,
              foregroundColor: Colors.white,
            ),
            child: const Text("Keluar"),
          ),
        ],
      ),
    );

    if (confirm == true && context.mounted) {
      await AuthService.logout();
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      appBar: AppBar(
        title: const Text("Profil Akun Saya"),
        centerTitle: false,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // Kartu Profil Utama
            Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: AppConstants.softCardShadow,
                border: Border.all(color: AppConstants.dividerColor),
              ),
              child: Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppConstants.primaryLight,
                      border: Border.all(color: AppConstants.primaryColor, width: 2),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(40),
                      child: Image.asset(
                        user.isTeacher ? "assets/images/person-1.png" : "assets/images/profile.png",
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const Icon(Icons.person, size: 48, color: AppConstants.primaryColor),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    user.fullName,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user.email,
                    style: const TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppConstants.primaryLight,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      user.role.toUpperCase(),
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppConstants.primaryColor),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Rincian Data Pegawai / Siswa
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: AppConstants.softCardShadow,
                border: Border.all(color: AppConstants.dividerColor),
              ),
              child: Column(
                children: [
                  if (user.isTeacher) ...[
                    _buildInfoRow(Icons.badge_outlined, "NIP / NUPTK", user.teacherInfo?.nip ?? user.nip ?? "-"),
                    _buildDivider(),
                    _buildInfoRow(Icons.work_outline_rounded, "Status Kepegawaian", user.teacherInfo?.employmentStatus ?? "PNS / PPPK"),
                    _buildDivider(),
                    _buildInfoRow(Icons.phone_outlined, "Kontak WA", user.phone ?? "-"),
                  ] else if (user.isStudent) ...[
                    _buildInfoRow(Icons.badge_outlined, "NISN", user.studentInfo?.nisn ?? "-"),
                    _buildDivider(),
                    _buildInfoRow(Icons.numbers_rounded, "NIS", user.studentInfo?.nis ?? "-"),
                    _buildDivider(),
                    _buildInfoRow(Icons.meeting_room_outlined, "Rombel Kelas", "Kelas ${user.studentInfo?.classroomName ?? '-'}"),
                  ] else ...[
                    _buildInfoRow(Icons.badge_outlined, "NIP / Identitas", user.nip ?? "-"),
                    _buildDivider(),
                    _buildInfoRow(Icons.phone_outlined, "No. Telepon", user.phone ?? "-"),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Menu Pengaturan & Bantuan
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: AppConstants.softCardShadow,
                border: Border.all(color: AppConstants.dividerColor),
              ),
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.dns_rounded, color: AppConstants.primaryColor),
                    title: const Text("Pengaturan Alamat Server", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                    subtitle: const Text("Atur IP host backend FastAPI", style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor)),
                    trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppConstants.captionTextColor),
                    onTap: () => _showServerDialog(context),
                  ),
                  _buildDivider(),
                  ListTile(
                    leading: const Icon(Icons.info_outline_rounded, color: AppConstants.secondaryColor),
                    title: const Text("Tentang Aplikasi", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                    subtitle: const Text("${AppConstants.appName} v${AppConstants.appVersion}", style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor)),
                  ),
                  _buildDivider(),
                  ListTile(
                    leading: const Icon(Icons.logout_rounded, color: AppConstants.sakitColor),
                    title: const Text("Keluar dari Akun", style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppConstants.sakitColor)),
                    onTap: () => _handleLogout(context),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppConstants.primaryColor),
          const SizedBox(width: 12),
          Text(label, style: const TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor)),
          const Spacer(),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor)),
        ],
      ),
    );
  }

  Widget _buildDivider() {
    return const Divider(height: 1, color: AppConstants.dividerColor);
  }
}

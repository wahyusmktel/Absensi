import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../core/constants.dart';
import '../models/user_model.dart';

/// Header Profil Pengguna di Atas Dashboard (UI Kits Style)
class UserMenuBar extends StatelessWidget {
  final UserModel user;
  final VoidCallback? onNotificationPressed;

  const UserMenuBar({
    Key? key,
    required this.user,
    this.onNotificationPressed,
  }) : super(key: key);

  String _formatRoleName(String role) {
    switch (role.toLowerCase()) {
      case 'guru':
        return 'Pendidik / Guru';
      case 'siswa':
        return 'Peserta Didik (Siswa)';
      case 'kepala_sekolah':
        return 'Kepala Sekolah';
      case 'operator_sekolah':
        return 'Operator Sekolah';
      case 'superadmin':
        return 'Super Administrator';
      default:
        return role.toUpperCase();
    }
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final dateStr = DateFormat('EEEE, d MMMM yyyy', 'id_ID').format(now);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: AppConstants.softCardShadow,
      ),
      child: Row(
        children: [
          // Foto Profil / Avatar
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppConstants.primaryLight,
              border: Border.all(color: AppConstants.primaryColor, width: 1.5),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(30),
              child: Image.asset(
                user.isTeacher
                    ? "assets/images/person-1.png"
                    : "assets/images/profile.png",
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.person,
                  size: 30,
                  color: AppConstants.primaryColor,
                ),
              ),
            ),
          ),
          const SizedBox(width: 14),
          // Info User & Role
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppConstants.primaryColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        _formatRoleName(user.role),
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: AppConstants.primaryColor,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 3),
                Text(
                  user.fullName,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppConstants.primaryTextColor,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  dateStr,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppConstants.captionTextColor,
                  ),
                ),
              ],
            ),
          ),
          // Notifikasi / Tombol Cepat
          IconButton(
            onPressed: onNotificationPressed,
            icon: Stack(
              children: [
                const Icon(
                  Icons.notifications_none_rounded,
                  size: 26,
                  color: AppConstants.primaryTextColor,
                ),
                Positioned(
                  top: 2,
                  right: 2,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppConstants.accentColor,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

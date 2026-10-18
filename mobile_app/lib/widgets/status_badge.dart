import 'package:flutter/material.dart';
import '../core/constants.dart';

/// Badge Status Kehadiran Presensi
class StatusBadge extends StatelessWidget {
  final String status;

  const StatusBadge({Key? key, required this.status}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;
    IconData icon;

    final lower = status.toLowerCase();
    if (lower == 'hadir') {
      bg = const Color(0xFFD1FAE5); // Emerald-100
      fg = const Color(0xFF065F46); // Emerald-800
      label = "Hadir di Kelas";
      icon = Icons.check_circle_rounded;
    } else if (lower == 'izin') {
      bg = const Color(0xFFFEF3C7); // Amber-100
      fg = const Color(0xFF92400E); // Amber-800
      label = "Izin (Piket)";
      icon = Icons.mail_rounded;
    } else if (lower == 'sakit') {
      bg = const Color(0xFFFEE2E2); // Rose-100
      fg = const Color(0xFF991B1B); // Rose-800
      label = "Sakit";
      icon = Icons.favorite_rounded;
    } else if (lower == 'alpa') {
      bg = const Color(0xFFF1F5F9); // Slate-100
      fg = const Color(0xFF475569); // Slate-600
      label = "Alpa";
      icon = Icons.cancel_rounded;
    } else {
      bg = const Color(0xFFF1F5F9);
      fg = const Color(0xFF64748B);
      label = "Belum Presensi";
      icon = Icons.schedule_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(30),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: fg),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}

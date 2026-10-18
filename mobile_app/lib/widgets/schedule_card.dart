import 'package:flutter/material.dart';
import '../core/constants.dart';
import 'status_badge.dart';

/// Kartu Jadwal Interaktif (UI Kits Standard)
class ScheduleCard extends StatelessWidget {
  final String periodText;
  final String timeRange;
  final String subjectName;
  final String classroomOrTeacher;
  final String status;
  final String? teachingMaterial;
  final VoidCallback? onAttendancePressed;
  final bool showAttendanceButton;

  const ScheduleCard({
    Key? key,
    required this.periodText,
    required this.timeRange,
    required this.subjectName,
    required this.classroomOrTeacher,
    required this.status,
    this.teachingMaterial,
    this.onAttendancePressed,
    this.showAttendanceButton = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppConstants.dividerColor, width: 0.9),
        boxShadow: AppConstants.softCardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Bar: Jam Pelajaran & Status Badge
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppConstants.primaryLight,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      periodText,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: AppConstants.primaryColor,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    timeRange,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppConstants.secondaryTextColor,
                    ),
                  ),
                ],
              ),
              StatusBadge(status: status),
            ],
          ),
          const SizedBox(height: 12),

          // Judul Mata Pelajaran & Kelas / Guru
          Text(
            subjectName,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.bold,
              color: AppConstants.primaryTextColor,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Icon(Icons.meeting_room_outlined, size: 16, color: AppConstants.captionTextColor),
              const SizedBox(width: 5),
              Text(
                classroomOrTeacher,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: AppConstants.secondaryTextColor,
                ),
              ),
            ],
          ),

          // Jika ada materi ajar
          if (teachingMaterial != null && teachingMaterial!.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(Icons.menu_book_rounded, size: 16, color: AppConstants.primaryColor),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "Materi: $teachingMaterial",
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppConstants.secondaryTextColor,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Tombol Presensi Cepat
          if (showAttendanceButton) ...[
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              height: 44,
              child: ElevatedButton.icon(
                onPressed: onAttendancePressed,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppConstants.primaryColor,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                icon: const Icon(Icons.camera_alt_rounded, size: 18),
                label: const Text(
                  "Presensi di Kelas Ini (Foto & GPS)",
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

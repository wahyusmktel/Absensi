import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../models/attendance_model.dart';
import '../services/api_service.dart';
import '../widgets/status_badge.dart';

/// Halaman Riwayat Presensi Mengajar Guru Pribadi
class AttendanceHistoryScreen extends StatefulWidget {
  const AttendanceHistoryScreen({Key? key}) : super(key: key);

  @override
  State<AttendanceHistoryScreen> createState() => _AttendanceHistoryScreenState();
}

class _AttendanceHistoryScreenState extends State<AttendanceHistoryScreen> {
  List<AttendanceHistoryModel> _historyList = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() => _isLoading = true);
    final list = await ApiService.getTeacherAttendanceHistory();
    if (mounted) {
      setState(() {
        _historyList = list;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      appBar: AppBar(
        title: const Text("Riwayat Presensi Saya"),
        centerTitle: false,
      ),
      body: RefreshIndicator(
        onRefresh: _loadHistory,
        color: AppConstants.primaryColor,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _historyList.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: AppConstants.primaryLight,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.history_rounded, size: 48, color: AppConstants.primaryColor),
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          "Belum Ada Riwayat Presensi",
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          "Presensi mengajar yang Anda submit akan tampil di sini.",
                          style: TextStyle(fontSize: 13, color: AppConstants.captionTextColor),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    itemCount: _historyList.length,
                    itemBuilder: (context, index) {
                      final item = _historyList[index];
                      return Container(
                        margin: const EdgeInsets.only(bottom: 16),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppConstants.dividerColor),
                          boxShadow: AppConstants.softCardShadow,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Tanggal, Jam & Badge Status
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.calendar_today_rounded, size: 14, color: AppConstants.primaryColor),
                                    const SizedBox(width: 6),
                                    Text(
                                      item.date,
                                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                                    ),
                                    if (item.checkInTime != null) ...[
                                      const SizedBox(width: 6),
                                      Text(
                                        "• ${item.checkInTime} WIB",
                                        style: const TextStyle(fontSize: 12, color: AppConstants.secondaryTextColor),
                                      ),
                                    ],
                                  ],
                                ),
                                StatusBadge(status: item.status),
                              ],
                            ),
                            const Divider(height: 22, color: AppConstants.dividerColor),

                            // Foto Kelas & Info Mapel
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Thumbnail Foto
                                Container(
                                  width: 68,
                                  height: 68,
                                  decoration: BoxDecoration(
                                    color: AppConstants.primaryLight,
                                    borderRadius: BorderRadius.circular(14),
                                    border: Border.all(color: AppConstants.dividerColor),
                                  ),
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(14),
                                    child: item.photoUrl != null && item.photoUrl!.isNotEmpty
                                        ? Image.network(
                                            item.photoUrl!,
                                            fit: BoxFit.cover,
                                            errorBuilder: (_, __, ___) => const Icon(Icons.image_not_supported_rounded, color: AppConstants.captionTextColor),
                                          )
                                        : const Icon(Icons.camera_alt_outlined, color: AppConstants.captionTextColor),
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        item.subjectName,
                                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                                      ),
                                      const SizedBox(height: 3),
                                      Text(
                                        "Kelas ${item.classroomName}",
                                        style: const TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor),
                                      ),
                                      if (item.teachingMaterial != null && item.teachingMaterial!.isNotEmpty) ...[
                                        const SizedBox(height: 6),
                                        Text(
                                          "Materi: ${item.teachingMaterial}",
                                          style: const TextStyle(fontSize: 12, color: AppConstants.primaryColor, fontWeight: FontWeight.w500),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            ),

                            // Info Koordinat & Radius GPS
                            if (item.latitude != null && item.longitude != null) ...[
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF8FAFC),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  children: [
                                    Icon(
                                      Icons.location_on_rounded,
                                      size: 14,
                                      color: item.isWithinRadius == true ? AppConstants.hadirColor : AppConstants.captionTextColor,
                                    ),
                                    const SizedBox(width: 6),
                                    Expanded(
                                      child: Text(
                                        "GPS: ${item.latitude?.toStringAsFixed(5)}, ${item.longitude?.toStringAsFixed(5)} ${item.isWithinRadius == true ? '(Radius Valid)' : ''}",
                                        style: const TextStyle(fontSize: 11, color: AppConstants.captionTextColor),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
      ),
    );
  }
}

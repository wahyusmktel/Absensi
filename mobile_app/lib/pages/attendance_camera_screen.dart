import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/constants.dart';
import '../models/schedule_model.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';
import '../widgets/custom_text_field.dart';
import '../widgets/primary_button.dart';

/// Halaman Presensi Mengajar Guru di Kelas (Kamera Foto Wajib + Titik Koordinat GPS Otomatis)
class AttendanceCameraScreen extends StatefulWidget {
  final TeacherTodayScheduleModel? selectedSchedule;

  const AttendanceCameraScreen({Key? key, this.selectedSchedule}) : super(key: key);

  @override
  State<AttendanceCameraScreen> createState() => _AttendanceCameraScreenState();
}

class _AttendanceCameraScreenState extends State<AttendanceCameraScreen> {
  final _picker = ImagePicker();
  final _materialController = TextEditingController();
  final _notesController = TextEditingController();

  Uint8List? _imageBytes;
  String? _photoBase64;
  double? _latitude;
  double? _longitude;
  double? _accuracy;
  bool _isLoadingGps = false;
  bool _isSubmitting = false;
  String? _gpsStatusText;
  String _selectedStatus = "hadir";

  List<TeacherTodayScheduleModel> _todaySchedules = [];
  TeacherTodayScheduleModel? _activeSchedule;
  bool _isLoadingSchedules = false;

  @override
  void initState() {
    super.initState();
    _activeSchedule = widget.selectedSchedule;
    if (_activeSchedule == null) {
      _loadSchedules();
    }
    _fetchGpsLocation();
  }

  @override
  void dispose() {
    _materialController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _loadSchedules() async {
    setState(() => _isLoadingSchedules = true);
    final list = await ApiService.getTeacherTodaySchedules();
    if (mounted) {
      setState(() {
        _todaySchedules = list;
        _isLoadingSchedules = false;
        if (list.isNotEmpty && _activeSchedule == null) {
          _activeSchedule = list.first;
        }
      });
    }
  }

  Future<void> _fetchGpsLocation() async {
    setState(() {
      _isLoadingGps = true;
      _gpsStatusText = "Mendeteksi koordinat GPS satelit...";
    });

    final res = await LocationService.getCurrentLocation();
    if (!mounted) return;

    if (res.success) {
      setState(() {
        _latitude = res.latitude;
        _longitude = res.longitude;
        _accuracy = res.accuracy;
        _isLoadingGps = false;
        _gpsStatusText = "Koordinat terkunci (${_latitude?.toStringAsFixed(6)}, ${_longitude?.toStringAsFixed(6)}) • Akurasi ±${_accuracy?.toStringAsFixed(1)}m";
      });
    } else {
      setState(() {
        _isLoadingGps = false;
        _gpsStatusText = res.errorMessage ?? "Gagal mendapatkan lokasi GPS.";
      });
    }
  }

  Future<void> _takePhoto(ImageSource source) async {
    try {
      final picked = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 80,
      );

      if (picked != null) {
        final bytes = await picked.readAsBytes();
        final base64String = base64Encode(bytes);

        setState(() {
          _imageBytes = bytes;
          _photoBase64 = "data:image/jpeg;base64,$base64String";
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Gagal membuka kamera: $e")),
      );
    }
  }

  Future<void> _submitAttendance() async {
    if (_activeSchedule == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Pilih jadwal pelajaran yang akan diabsen.")),
      );
      return;
    }

    if (_photoBase64 == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Harap ambil foto selfie/kondisi kelas sebagai bukti kehadiran!")),
      );
      return;
    }

    if (_latitude == null || _longitude == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Koordinat GPS belum terdeteksi. Silakan segarkan GPS!")),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final res = await ApiService.submitAttendance(
      scheduleId: _activeSchedule!.scheduleId,
      latitude: _latitude!,
      longitude: _longitude!,
      locationAccuracy: _accuracy,
      photoBase64: _photoBase64!,
      attendanceStatus: _selectedStatus,
      teachingMaterial: _materialController.text.trim(),
      notes: _notesController.text.trim(),
    );

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    if (res['success'] == true) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Color(0xFFD1FAE5),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.check_circle_rounded, color: Color(0xFF059669), size: 54),
              ),
              const SizedBox(height: 18),
              const Text(
                "Presensi Berhasil!",
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
              ),
              const SizedBox(height: 8),
              Text(
                res['message'] ?? "Kehadiran Anda telah terekam dan disinkronkan ke server sekolah.",
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor),
              ),
              const SizedBox(height: 24),
              PrimaryButton(
                text: "Selesai",
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.pop(context, true);
                },
              ),
            ],
          ),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(res['message'] ?? "Gagal merekam presensi.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Presensi Kehadiran di Kelas"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Pemilihan Sesi Mengajar
            if (widget.selectedSchedule == null) ...[
              const Text(
                "Pilih Jadwal Mengajar Sesi Ini",
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
              ),
              const SizedBox(height: 8),
              if (_isLoadingSchedules)
                const LinearProgressIndicator()
              else if (_todaySchedules.isEmpty)
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text("Tidak ada jadwal mengajar pada hari ini."),
                )
              else
                DropdownButtonFormField<TeacherTodayScheduleModel>(
                  value: _activeSchedule,
                  decoration: InputDecoration(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(color: AppConstants.dividerColor),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                  ),
                  items: _todaySchedules.map((s) {
                    return DropdownMenuItem(
                      value: s,
                      child: Text("${s.startTime}-${s.endTime} • ${s.subjectName} (${s.classroomName})"),
                    );
                  }).toList(),
                  onChanged: (val) {
                    setState(() => _activeSchedule = val);
                  },
                ),
              const SizedBox(height: 18),
            ] else ...[
              // Kartu Ringkasan Sesi Terpilih
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppConstants.primaryLight,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppConstants.primaryColor.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.school_rounded, color: AppConstants.primaryColor, size: 36),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.selectedSchedule!.subjectName,
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Kelas ${widget.selectedSchedule!.classroomName} • Jam ${widget.selectedSchedule!.startTime} - ${widget.selectedSchedule!.endTime} WIB",
                            style: const TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
            ],

            // 1. Box Kamera Bukti Kehadiran
            const Text(
              "Foto Bukti Kehadiran di Kelas (Wajib)",
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
            ),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () => _takePhoto(ImageSource.camera),
              child: Container(
                height: 220,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: _imageBytes != null ? AppConstants.primaryColor : AppConstants.dividerColor,
                    width: 1.5,
                  ),
                  boxShadow: AppConstants.softCardShadow,
                ),
                child: _imageBytes != null
                    ? Stack(
                        fit: StackFit.expand,
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(18),
                            child: Image.memory(_imageBytes!, fit: BoxFit.cover),
                          ),
                          Positioned(
                            bottom: 12,
                            right: 12,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.7),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.refresh, color: Colors.white, size: 16),
                                  SizedBox(width: 4),
                                  Text("Ambil Ulang", style: TextStyle(color: Colors.white, fontSize: 12)),
                                ],
                              ),
                            ),
                          ),
                        ],
                      )
                    : Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppConstants.primaryLight,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.camera_alt_rounded,
                              size: 40,
                              color: AppConstants.primaryColor,
                            ),
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            "Ketuk untuk Ambil Foto Kelas / Selfie",
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: AppConstants.primaryTextColor,
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            "Kamera depan/belakang wajib digunakan sebagai bukti otentik",
                            style: TextStyle(fontSize: 12, color: AppConstants.captionTextColor),
                          ),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 18),

            // 2. Kotak Status GPS Geolokasi
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _latitude != null ? const Color(0xFF10B981) : AppConstants.dividerColor,
                ),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: _latitude != null ? const Color(0xFFD1FAE5) : const Color(0xFFF1F5F9),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.location_on_rounded,
                      color: _latitude != null ? const Color(0xFF059669) : AppConstants.captionTextColor,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Lokasi Absensi (GPS Koordinat)",
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _gpsStatusText ?? "Menunggu GPS...",
                          style: TextStyle(
                            fontSize: 12,
                            color: _latitude != null ? const Color(0xFF065F46) : AppConstants.captionTextColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: _isLoadingGps ? null : _fetchGpsLocation,
                    icon: _isLoadingGps
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.refresh_rounded, color: AppConstants.primaryColor),
                    tooltip: "Perbarui GPS",
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // 3. Pilihan Status Kehadiran
            const Text(
              "Status Kehadiran",
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppConstants.primaryTextColor),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _buildStatusChoiceChip("Hadir", "hadir", Icons.check_circle_outline),
                const SizedBox(width: 8),
                _buildStatusChoiceChip("Izin", "izin", Icons.mail_outline),
                const SizedBox(width: 8),
                _buildStatusChoiceChip("Sakit", "sakit", Icons.favorite_border),
              ],
            ),
            const SizedBox(height: 18),

            // 4. Input Materi Pembelajaran
            CustomTextField(
              controller: _materialController,
              labelText: "Materi Pokok Pembelajaran",
              hintText: "Contoh: Persamaan Linear Satu Variabel...",
              prefixIcon: const Icon(Icons.book_outlined, color: AppConstants.captionTextColor),
            ),
            const SizedBox(height: 14),

            // 5. Input Catatan Kelas
            CustomTextField(
              controller: _notesController,
              labelText: "Catatan Pembelajaran (Opsional)",
              hintText: "Contoh: Siswa aktif berdiskusi kelompok...",
              maxLines: 2,
              prefixIcon: const Icon(Icons.notes_rounded, color: AppConstants.captionTextColor),
            ),
            const SizedBox(height: 28),

            // Tombol Kirim Presensi
            PrimaryButton(
              text: "Kirim Presensi Sekarang",
              onPressed: _submitAttendance,
              isLoading: _isSubmitting,
              icon: Icons.send_rounded,
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChoiceChip(String label, String value, IconData icon) {
    final isSelected = _selectedStatus == value;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() => _selectedStatus = value);
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppConstants.primaryColor : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppConstants.primaryColor : AppConstants.dividerColor,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 16, color: isSelected ? Colors.white : AppConstants.secondaryTextColor),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: isSelected ? Colors.white : AppConstants.secondaryTextColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

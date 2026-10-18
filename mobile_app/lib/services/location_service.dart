import 'package:geolocator/geolocator.dart';

/// Hasil Geolokasi GPS
class LocationResult {
  final bool success;
  final double? latitude;
  final double? longitude;
  final double? accuracy;
  final String? errorMessage;

  LocationResult({
    required this.success,
    this.latitude,
    this.longitude,
    this.accuracy,
    this.errorMessage,
  });
}

/// Layanan Pengambilan Titik Koordinat GPS Smartphone
class LocationService {
  /// Mendapatkan titik koordinat lokasi saat ini dengan akurasi tinggi
  static Future<LocationResult> getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    // Periksa apakah layanan GPS aktif di perangkat
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return LocationResult(
        success: false,
        errorMessage: "Layanan GPS perangkat belum aktif. Harap aktifkan GPS Anda di Pengaturan.",
      );
    }

    // Periksa hak akses lokasi
    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return LocationResult(
          success: false,
          errorMessage: "Izin lokasi ditolak. Izin lokasi wajib diberikan untuk presensi.",
        );
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return LocationResult(
        success: false,
        errorMessage: "Izin lokasi diblokir permanen. Harap aktifkan secara manual dari Pengaturan Aplikasi.",
      );
    }

    try {
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 15),
      );

      return LocationResult(
        success: true,
        latitude: position.latitude,
        longitude: position.longitude,
        accuracy: position.accuracy,
      );
    } catch (e) {
      // Fallback ke posisi terakhir jika timeout
      try {
        final lastPos = await Geolocator.getLastKnownPosition();
        if (lastPos != null) {
          return LocationResult(
            success: true,
            latitude: lastPos.latitude,
            longitude: lastPos.longitude,
            accuracy: lastPos.accuracy,
          );
        }
      } catch (_) {}

      return LocationResult(
        success: false,
        errorMessage: "Gagal mendeteksi koordinat GPS: $e",
      );
    }
  }
}

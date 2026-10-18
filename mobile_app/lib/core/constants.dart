import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Konfigurasi Konstanta Aplikasi Mobile PresensiPintar SMP
/// Mengadaptasi desain modern dari Olayemii Flutter UI Kits & CoreUI.
class AppConstants {
  // Nama & Identitas Aplikasi
  static const String appName = "PresensiPintar";
  static const String appTagline = "Sistem Presensi Guru & Siswa SMP Terpadu";
  static const String appVersion = "1.0.0";

  // URL Dasar RESTful API FastAPI
  // Otomatis: localhost untuk Web/Chrome, 10.0.2.2 untuk Android Emulator.
  static String get defaultBaseUrl {
    if (kIsWeb) {
      return "http://localhost:8000/api/v1";
    }
    return "http://10.0.2.2:8000/api/v1";
  }

  // Key Penyimpanan Lokal SharedPreferences
  static const String keyToken = "auth_jwt_token";
  static const String keyUserRole = "auth_user_role";
  static const String keyUserData = "auth_user_json";
  static const String keyCustomBaseUrl = "custom_backend_url";

  // Palet Warna UI Kits (Harmonisasi Language Learning UI Kit & CoreUI)
  static const Color primaryColor = Color(0xFF2A52BE);      // Royal Education Blue
  static const Color primaryDark = Color(0xFF1E3A8A);       // Deep Navy
  static const Color primaryLight = Color(0xFFEEF2FF);      // Soft Blue-Indigo
  static const Color accentColor = Color(0xFFFF6380);       // Warm Coral (UI Kit Accent)
  static const Color secondaryColor = Color(0xFF4F46E5);    // Modern Indigo
  static const Color backgroundColor = Color(0xFFF8FAFC);   // Clean Slate White
  static const Color cardBackgroundColor = Colors.white;

  // Warna Teks
  static const Color primaryTextColor = Color(0xFF1E293B);   // Slate 800
  static const Color secondaryTextColor = Color(0xFF475569); // Slate 600
  static const Color captionTextColor = Color(0xFF94A3B8);   // Slate 400
  static const Color dividerColor = Color(0xFFE2E8F0);       // Slate 200

  // Warna Status Presensi
  static const Color hadirColor = Color(0xFF10B981);         // Emerald Green
  static const Color izinColor = Color(0xFFF59E0B);          // Amber Orange
  static const Color sakitColor = Color(0xFFEF4444);         // Rose Red
  static const Color alpaColor = Color(0xFF64748B);          // Slate Gray

  // Shadow Halus (UI Kits Standard)
  static List<BoxShadow> softCardShadow = [
    BoxShadow(
      color: const Color(0xFF1E293B).withOpacity(0.06),
      spreadRadius: 0,
      blurRadius: 16,
      offset: const Offset(0, 4),
    ),
  ];

  static List<BoxShadow> primaryButtonShadow = [
    BoxShadow(
      color: primaryColor.withOpacity(0.35),
      spreadRadius: 0,
      blurRadius: 14,
      offset: const Offset(0, 6),
    ),
  ];
}

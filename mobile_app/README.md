# 📱 PresensiPintar SMP - Mobile Application (Flutter)

Aplikasi mobile smartphone untuk **Sistem Absensi Guru & Siswa SMP Terpadu**, dibangun menggunakan framework **Flutter** dengan desain antarmuka modern yang diadaptasi dari [Olayemii Flutter UI Kits](https://github.com/olayemii/flutter-ui-kits) dan diselaraskan dengan estetika CoreUI.

---

## ✨ Fitur Utama Aplikasi Mobile

### 👨‍🏫 Fitur Pendidik (Guru)
1. **Dashboard Pendidik**:
   - Kartu sambutan profil guru (Nama, NIP/NUPTK, status kepegawaian).
   - Metrik jam mengajar hari ini.
   - Daftar jadwal mengajar interaktif dengan status presensi langsung.
   - Monitoring daftar guru piket yang bertugas hari ini.
2. **Presensi di Kelas (Kamera Wajib + Geolokasi GPS)**:
   - Pengambilan foto langsung bukti kehadiran di kelas (selfie / suasana kelas).
   - Pendeteksian koordinat GPS satelit otomatis (Latitude, Longitude, & radius akurasi meter).
   - Input materi pokok pembelajaran & catatan guru.
   - Pilihan status kehadiran: *Hadir*, *Izin*, atau *Sakit*.
3. **Riwayat Presensi Guru**:
   - Dokumentasi foto kelas, waktu *check-in*, materi ajar, dan status verifikasi radius sekolah.

### 🎒 Fitur Peserta Didik (Siswa)
1. **Dashboard Siswa**:
   - Profil siswa (NISN, NIS, rombongan belajar kelas).
   - Jadwal mata pelajaran kelas hari ini dengan **status real-time kehadiran guru di kelas**.
   - Monitoring daftar guru piket harian.
2. **Jadwal Pelajaran Kelas Mingguan**:
   - Alokasi mata pelajaran dan guru pengampu dari hari Senin sampai Sabtu.

### ⚙️ Pengaturan & Fleksibilitas
- **Pengaturan URL Server Backend**: Memungkinkan pengguna/guru mengganti alamat IP atau domain backend FastAPI (`http://10.0.2.2:8000/api/v1` untuk emulator Android, atau IP LAN `http://192.168.x.x:8000/api/v1` untuk smartphone fisik).
- **Keamanan Token JWT**: Penyimpanan token terisolasi dan aman di perangkat lokal (`SharedPreferences`).

---

## 🚀 Panduan Menjalankan Aplikasi

### 1. Prasyarat
- [Flutter SDK](https://docs.flutter.dev/get-started/install) (versi 3.0.0 atau lebih tinggi).
- Android Studio / VS Code dengan ekstensi Flutter & Dart.
- Backend FastAPI (PresensiPintar) berjalan di port 8000:
  ```bash
  # Dari root folder project backend:
  .\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

### 2. Mengunduh Dependencies
Masuk ke folder `mobile_app`:
```bash
cd mobile_app
flutter pub get
```

### 3. Menjalankan di Emulator / Perangkat Fisik
```bash
flutter run
```

### 4. Membangun Berkas APK Rilis (Android)
```bash
flutter build apk --release
```
Berkas APK siap install akan berada di `mobile_app/build/app/outputs/flutter-apk/app-release.apk`.

---

## 📂 Struktur Proyek Mobile

```text
mobile_app/
├── assets/
│   └── images/              # Ilustrasi & avatar dari Flutter UI Kits
├── lib/
│   ├── core/
│   │   ├── constants.dart   # Konstanta warna, key, dan URL backend
│   │   └── app_theme.dart   # Tema Material 3 & tipografi Google Fonts
│   ├── models/
│   │   ├── user_model.dart
│   │   ├── schedule_model.dart
│   │   └── attendance_model.dart
│   ├── services/
│   │   ├── api_service.dart      # Klien REST API FastAPI
│   │   ├── auth_service.dart     # Manajemen sesi & token JWT
│   │   └── location_service.dart # Layanan koordinat GPS Geolocator
│   ├── widgets/
│   │   ├── custom_text_field.dart
│   │   ├── primary_button.dart
│   │   ├── user_menu_bar.dart
│   │   ├── schedule_card.dart
│   │   └── status_badge.dart
│   ├── pages/
│   │   ├── splash_screen.dart
│   │   ├── login_screen.dart
│   │   ├── main_navigation_screen.dart
│   │   ├── teacher_dashboard_screen.dart
│   │   ├── attendance_camera_screen.dart
│   │   ├── attendance_history_screen.dart
│   │   ├── student_dashboard_screen.dart
│   │   ├── student_schedule_screen.dart
│   │   └── profile_screen.dart
│   └── main.dart            # Titik masuk utama aplikasi Flutter
└── pubspec.yaml             # Manifest package & aset Flutter
```

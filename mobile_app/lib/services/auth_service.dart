import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/user_model.dart';
import 'api_service.dart';

/// Layanan Autentikasi Pengguna & Manajemen Sesi Lokal
class AuthService {
  static Future<bool> isLoggedIn() async {
    final token = await ApiService.getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<UserModel?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString(AppConstants.keyUserData);
    if (userJson != null) {
      try {
        return UserModel.fromJson(jsonDecode(userJson));
      } catch (_) {}
    }
    // Refresh dari backend
    final user = await ApiService.getProfile();
    if (user != null) {
      await prefs.setString(AppConstants.keyUserData, jsonEncode(user.toJson()));
      await prefs.setString(AppConstants.keyUserRole, user.role);
    }
    return user;
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final result = await ApiService.login(email, password);
    if (result['success'] == true) {
      // Ambil data profil setelah login
      final profile = await ApiService.getProfile();
      if (profile != null) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(AppConstants.keyUserData, jsonEncode(profile.toJson()));
        await prefs.setString(AppConstants.keyUserRole, profile.role);
      }
    }
    return result;
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.keyToken);
    await prefs.remove(AppConstants.keyUserData);
    await prefs.remove(AppConstants.keyUserRole);
  }
}

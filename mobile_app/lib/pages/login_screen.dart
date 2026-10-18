import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../widgets/custom_text_field.dart';
import '../widgets/primary_button.dart';
import 'main_navigation_screen.dart';

/// Halaman Login Mobile Berdesain UI Kits Modern
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await AuthService.login(
      _emailController.text.trim(),
      _passwordController.text,
    );

    if (!mounted) return;

    if (res['success'] == true) {
      final user = await AuthService.getCurrentUser();
      if (user != null && mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => MainNavigationScreen(user: user)),
        );
      }
    } else {
      setState(() {
        _errorMessage = res['message'] ?? "Login gagal. Silakan coba kembali.";
        _isLoading = false;
      });
    }
  }

  void _showServerConfigDialog() async {
    final currentUrl = await ApiService.getBaseUrl();
    final urlController = TextEditingController(text: currentUrl);

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.settings_rounded, color: AppConstants.primaryColor),
            SizedBox(width: 8),
            Text("Pengaturan Server", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Tentukan alamat IP / Domain backend FastAPI Anda:",
              style: TextStyle(fontSize: 13, color: AppConstants.secondaryTextColor),
            ),
            const SizedBox(height: 12),
            CustomTextField(
              controller: urlController,
              hintText: "Contoh: http://192.168.1.100:8000/api/v1",
              labelText: "API Base URL",
              prefixIcon: const Icon(Icons.link_rounded, color: AppConstants.primaryColor),
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
              await ApiService.setBaseUrl(urlController.text.trim());
              if (mounted) Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("Alamat server backend berhasil diperbarui.")),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppConstants.primaryColor,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text("Simpan"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppConstants.backgroundColor,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 16),
                // Tombol Pengaturan Server di Pojok Kanan Atas
                Align(
                  alignment: Alignment.topRight,
                  child: IconButton(
                    onPressed: _showServerConfigDialog,
                    tooltip: "Atur Server URL",
                    icon: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppConstants.dividerColor),
                      ),
                      child: const Icon(Icons.settings_outlined, size: 20, color: AppConstants.secondaryTextColor),
                    ),
                  ),
                ),
                const SizedBox(height: 10),

                // Logo & Ilustrasi Header
                Center(
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      color: AppConstants.primaryLight,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: AppConstants.primaryColor.withOpacity(0.12),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.fingerprint_rounded,
                      size: 50,
                      color: AppConstants.primaryColor,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  "Selamat Datang Kembali",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppConstants.primaryTextColor,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  "Masuk untuk melakukan presensi dan melihat jadwal sekolah",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: AppConstants.captionTextColor,
                  ),
                ),
                const SizedBox(height: 32),

                // Alert Error
                if (_errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEE2E2),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFF87171)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.error_outline_rounded, color: Color(0xFFDC2626), size: 22),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _errorMessage!,
                            style: const TextStyle(fontSize: 13, color: Color(0xFF991B1B)),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                // Input Email
                CustomTextField(
                  controller: _emailController,
                  labelText: "Email Akun Sekolah",
                  hintText: "nama@sekolah.sch.id",
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: const Icon(Icons.alternate_email_rounded, color: AppConstants.captionTextColor),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return "Email wajib diisi";
                    if (!v.contains("@")) return "Format email tidak valid";
                    return null;
                  },
                ),
                const SizedBox(height: 18),

                // Input Password
                CustomTextField(
                  controller: _passwordController,
                  labelText: "Kata Sandi (Password)",
                  hintText: "Masukkan kata sandi...",
                  obscureText: _obscurePassword,
                  prefixIcon: const Icon(Icons.lock_outline_rounded, color: AppConstants.captionTextColor),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      color: AppConstants.captionTextColor,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscurePassword = !_obscurePassword;
                      });
                    },
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return "Kata sandi wajib diisi";
                    return null;
                  },
                ),
                const SizedBox(height: 30),

                // Tombol Masuk
                PrimaryButton(
                  text: "Masuk ke Sistem",
                  onPressed: _handleLogin,
                  isLoading: _isLoading,
                  icon: Icons.login_rounded,
                ),
                const SizedBox(height: 24),

                // Footer Informasi
                Center(
                  child: Text(
                    "${AppConstants.appName} v${AppConstants.appVersion} • CoreUI Mobile Edition",
                    style: const TextStyle(fontSize: 12, color: AppConstants.captionTextColor),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

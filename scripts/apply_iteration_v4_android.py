#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "RASTACODER_V4_ANDROID"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def write(path, text):
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_required(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing v4 Android anchor: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ARM64-only application packaging. Keep every feature/library; only remove
# irrelevant CPU architectures from the APK.
# ---------------------------------------------------------------------------
gradle_path = "android/app/build.gradle"
gradle = read(gradle_path)
if MARKER not in gradle:
    gradle = replace_required(
        gradle,
        '            abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"\n',
        '            // RASTACODER_V4_ANDROID: modern Android/MLC test line is ARM64-only.\n'
        '            // All Python, FFmpeg, ML Kit and MLC capabilities remain enabled.\n'
        '            abiFilters "arm64-v8a"\n',
        "arm64 abiFilters",
    )
    write(gradle_path, gradle)

# ---------------------------------------------------------------------------
# Google Sign-In: diagnose ApiException 10 with the exact Android OAuth values
# needed in Google Cloud. A Web client ID remains configurable, but Google also
# requires an Android OAuth client for this package/signing SHA-1.
# ---------------------------------------------------------------------------
auth_path = "lib/core/services/auth_service.dart"
auth = read(auth_path)
if MARKER not in auth:
    auth = replace_required(
        auth,
        "import 'package:flutter/foundation.dart';\n",
        "import 'package:flutter/foundation.dart';\nimport 'package:flutter/services.dart';\n",
        "PlatformException import",
    )
    auth = replace_required(
        auth,
        "  static const _clientIdKey = 'google_oauth_server_client_id';\n",
        "  // RASTACODER_V4_ANDROID\n"
        "  static const rastaAndroidPackage = 'ai.navixmind';\n"
        "  static const rastaSigningSha1 = '74:5D:97:54:87:32:A9:DE:D0:96:6E:A5:58:8E:78:68:8F:85:31:B6';\n"
        "  static const _clientIdKey = 'google_oauth_server_client_id';\n",
        "OAuth identity constants",
    )
    auth = replace_required(
        auth,
        '''    } catch (e) {
      await AnalyticsService.instance.googleSignInCompleted(success: false);
      rethrow;
    }
  }
''',
        '''    } on PlatformException catch (e) {
      await AnalyticsService.instance.googleSignInCompleted(success: false);
      final details = '${e.code} ${e.message ?? ''} ${e.details ?? ''}';
      if (e.code == 'sign_in_failed' &&
          (details.contains('ApiException: 10') || details.contains('DEVELOPER_ERROR'))) {
        throw StateError(
          'Google OAuth 配置错误（DEVELOPER_ERROR / ApiException 10）。'
          '请在与当前 Web OAuth Client ID 相同的 Google Cloud 项目中创建或核对 Android OAuth Client：'
          '包名 $rastaAndroidPackage；签名 SHA-1 $rastaSigningSha1。'
          '同时启用 Gmail API 和 Google Calendar API，并完成 OAuth consent screen/test user 配置。'
          '只填写 Web Client ID 仍不足以通过 Android Google Sign-In 校验。',
        );
      }
      throw StateError('Google 登录失败：${e.code}${e.message != null ? ' - ${e.message}' : ''}');
    } catch (e) {
      await AnalyticsService.instance.googleSignInCompleted(success: false);
      rethrow;
    }
  }
''',
        "Google signIn diagnostics",
    )
    write(auth_path, auth)

settings_path = "lib/features/settings/settings_screen.dart"
settings = read(settings_path)
if MARKER not in settings:
    settings = settings.replace(
        "class _SettingsScreenState",
        "// RASTACODER_V4_ANDROID\nclass _SettingsScreenState",
        1,
    ) if "class _SettingsScreenState" in settings else settings.replace(
        "class SettingsScreen",
        "// RASTACODER_V4_ANDROID\nclass SettingsScreen",
        1,
    )
    settings = replace_required(
        settings,
        "原作者的 OAuth Client 可能只允许其测试账号登录。这里可以填写您自己的 Google OAuth Web Client ID；留空则恢复上游默认值。",
        "这里填写 Google OAuth Web Client ID。Google Android 登录还要求同一 Google Cloud 项目中存在 Android OAuth Client，并登记包名 ai.navixmind 与当前 RastaCoder 签名 SHA-1：74:5D:97:54:87:32:A9:DE:D0:96:6E:A5:58:8E:78:68:8F:85:31:B6。留空会恢复上游 Web Client，但上游配置可能与 RastaCoder 签名不匹配。",
        "OAuth settings explanatory copy",
    )
    settings = replace_required(
        settings,
        "? '已配置独立 OAuth Client'\n                : '当前使用上游 OAuth Client（可能受测试用户限制）'",
        "? '已配置 Web Client；还需匹配 Android 包名与签名 SHA-1'\n                : '当前使用上游 Web Client；可能与 RastaCoder 签名不匹配'",
        "OAuth settings subtitle",
    )
    write(settings_path, settings)

# ---------------------------------------------------------------------------
# Native multimedia implementation: honor the documented extract_audio format,
# validate common aspect-ratio spellings, and preserve requested PNG output.
# ---------------------------------------------------------------------------
native_path = "lib/core/services/native_tool_executor.dart"
native = read(native_path)
if MARKER not in native:
    # Add marker near class declaration without changing behavior.
    native = replace_required(
        native,
        "class NativeToolExecutor {\n",
        "// RASTACODER_V4_ANDROID\nclass NativeToolExecutor {\n",
        "native marker",
    )

    native = replace_required(
        native,
        '''      case 'extract_audio':
        final format = params['format'] ?? 'mp3';
        final bitrate = params['bitrate'] ?? '192k';
        command = '-y -i "$inputPath" -vn -acodec libmp3lame -ab $bitrate "$outputPath"';
        break;
''',
        '''      case 'extract_audio':
        final format = (params['format'] ?? 'mp3').toString().toLowerCase().replaceAll('.', '');
        final bitrate = params['bitrate'] ?? '192k';
        switch (format) {
          case 'mp3':
            command = '-y -i "$inputPath" -vn -c:a libmp3lame -b:a $bitrate "$outputPath"';
            break;
          case 'aac':
          case 'm4a':
            command = '-y -i "$inputPath" -vn -c:a aac -b:a $bitrate "$outputPath"';
            break;
          case 'wav':
            command = '-y -i "$inputPath" -vn -c:a pcm_s16le "$outputPath"';
            break;
          case 'flac':
            command = '-y -i "$inputPath" -vn -c:a flac "$outputPath"';
            break;
          case 'ogg':
          case 'opus':
            command = '-y -i "$inputPath" -vn -c:a libopus -b:a $bitrate "$outputPath"';
            break;
          default:
            throw ArgumentError('Unsupported audio format: $format. Use mp3, aac/m4a, wav, flac, ogg, or opus.');
        }
        break;
''',
        "extract_audio codec",
    )

    native = replace_required(
        native,
        '''    final targetAspectRatio = args['aspect_ratio'] as String? ?? '9:16';

    if (inputPath == null || outputPath == null) {
      throw ArgumentError('Missing input_path or output_path parameter');
    }

    // Parse aspect ratio
    final parts = targetAspectRatio.split(':');
    final targetWidth = int.parse(parts[0]);
    final targetHeight = int.parse(parts[1]);
''',
        '''    final rawAspectRatio = args['aspect_ratio']?.toString() ?? '9:16';

    if (inputPath == null || outputPath == null) {
      throw ArgumentError('Missing input_path or output_path parameter');
    }

    // Accept common small-model variants: 9:16, 9/16, 9x16.
    final targetAspectRatio = rawAspectRatio.toLowerCase().replaceAll('x', ':').replaceAll('/', ':').replaceAll(' ', '');
    final parts = targetAspectRatio.split(':');
    if (parts.length != 2) {
      throw ArgumentError('Invalid aspect_ratio: $rawAspectRatio. Expected width:height, e.g. 9:16.');
    }
    final targetWidth = int.tryParse(parts[0]);
    final targetHeight = int.tryParse(parts[1]);
    if (targetWidth == null || targetHeight == null || targetWidth <= 0 || targetHeight <= 0) {
      throw ArgumentError('Invalid aspect_ratio: $rawAspectRatio. Values must be positive integers.');
    }
''',
        "aspect ratio validation",
    )

    native = replace_required(
        native,
        '''        final outputFile = File(outputPath);
        await outputFile.writeAsBytes(img.encodeJpg(cropped, quality: 90));

        return {
''',
        '''        final outputFile = File(outputPath);
        final lowerOutput = outputPath.toLowerCase();
        if (lowerOutput.endsWith('.png')) {
          await outputFile.writeAsBytes(img.encodePng(cropped));
        } else {
          await outputFile.writeAsBytes(img.encodeJpg(cropped, quality: 90));
        }

        return {
''',
        "smart crop output encoding",
    )
    write(native_path, native)

print("RastaCoder v4 Android/ARM64/media/Google patches applied successfully.")

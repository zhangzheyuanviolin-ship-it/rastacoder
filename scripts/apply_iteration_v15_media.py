from pathlib import Path

ROOT = Path('.')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_once(path, old, new):
    text = read(path)
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'V15 anchor not found in {path}: {old[:140]!r}')
    write(path, text.replace(old, new, 1))


# download_media: reject non-media inputs explicitly and use a real browser
# impersonation backend for both yt-dlp extraction and the final CDN stream.
media_path = 'python/navixmind/tools/media.py'
media_text = read(media_path)
start = media_text.index('def download_media(')
download_media_block = r'''def download_media(
    url: str,
    format: str = "video",
    output_path: str = None,
    _output_dir: str = None,
) -> dict:
    """Download an actual audio/video stream using browser impersonation."""
    import re
    import yt_dlp

    if is_blocked_domain(url):
        raise ToolError(
            "YouTube downloads are not supported due to platform policies. "
            "Try TikTok, Instagram, or other supported platforms."
        )
    requested_format = str(format or "video").lower()
    if requested_format not in {"video", "audio"}:
        raise ToolError("download_media format must be video or audio")

    bridge = get_bridge()
    bridge.log("Extracting media info...")
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        try:
            from yt_dlp.networking.impersonate import ImpersonateTarget
            ydl_opts['impersonate'] = ImpersonateTarget(client='chrome')
        except Exception:
            # The final CDN request below still requires curl-cffi, so a missing
            # yt-dlp helper cannot silently degrade the actual transfer.
            pass

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not isinstance(info, dict):
                raise ToolError("This URL did not resolve to an audio/video item.")

            extractor = str(info.get('extractor', '')).lower()
            if 'youtube' in extractor:
                raise ToolError("This link redirects to YouTube, which is not supported.")
            final_url = info.get('webpage_url', url)
            if is_blocked_domain(final_url):
                raise ToolError("This link redirects to a blocked platform.")

            title = info.get('title', 'download')
            duration = info.get('duration', 0)
            bridge.log(f"Found: {title} ({duration}s)")

            raw_formats = info.get('formats') or []
            formats = [
                f for f in raw_formats
                if isinstance(f, dict) and f.get('url') and (
                    f.get('acodec') not in (None, 'none')
                    or f.get('vcodec') not in (None, 'none')
                )
            ]
            if not formats and info.get('url') and (
                info.get('acodec') not in (None, 'none')
                or info.get('vcodec') not in (None, 'none')
            ):
                formats = [info]
            if not formats:
                raise ToolError(
                    "download_media only supports video/audio URLs; no downloadable "
                    "audio or video stream was found."
                )

            if requested_format == 'audio':
                candidates = [
                    f for f in formats
                    if f.get('acodec') not in (None, 'none')
                    and f.get('vcodec') in (None, 'none')
                ]
                if not candidates:
                    candidates = [f for f in formats if f.get('acodec') not in (None, 'none')]
            else:
                candidates = [f for f in formats if f.get('vcodec') not in (None, 'none')]
            if not candidates:
                raise ToolError(f"No downloadable {requested_format} stream was found for this URL.")

            best_format = candidates[-1]
            download_url = best_format.get('url')
            ext = str(best_format.get('ext') or ('mp3' if requested_format == 'audio' else 'mp4'))
            if not download_url:
                raise ToolError("Could not extract a downloadable audio/video URL.")

            safe_title = re.sub(r'[^\w\-. ()\[\]]+', '_', str(title)).strip(' ._') or 'download'
            if output_path:
                final_path = output_path
            else:
                root = _output_dir or os.getcwd()
                os.makedirs(root, exist_ok=True)
                final_path = os.path.join(root, f"{safe_title}.{ext}")
            parent = os.path.dirname(final_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            request_headers = best_format.get('http_headers') or info.get('http_headers') or {}

            try:
                from curl_cffi import requests as browser_requests
            except ImportError as exc:
                raise ToolError(
                    "Browser impersonation runtime is unavailable; curl-cffi must be bundled "
                    "for download_media."
                ) from exc

            response = browser_requests.get(
                download_url,
                headers=request_headers,
                impersonate='chrome',
                stream=True,
                timeout=60,
            )
            try:
                response.raise_for_status()
                content_type = str(response.headers.get('content-type', '')).lower()
                if content_type.startswith('image/') or content_type.startswith('text/html'):
                    raise ToolError(
                        "Resolved URL is not an audio/video stream; download_media only "
                        "supports video/audio."
                    )
                with open(final_path, 'wb') as out:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            out.write(chunk)
            finally:
                response.close()

            size_bytes = os.path.getsize(final_path)
            if size_bytes <= 0:
                raise ToolError("Downloaded media file is empty.")
            return {
                "title": title,
                "duration": duration,
                "output_path": final_path,
                "size_bytes": size_bytes,
                "format": requested_format,
                "extension": ext,
                "extractor": extractor,
                "success": True,
                "browser_impersonation": "chrome/curl-cffi",
            }
    except ToolError:
        raise
    except yt_dlp.DownloadError as e:
        raise ToolError(f"Failed to extract media: {str(e)}")
    except Exception as e:
        raise ToolError(f"Media download failed: {str(e)}")
'''
write(media_path, media_text[:start] + download_media_block + '\n')


# FFmpeg: codec choice follows the output container. Numeric mix duration means
# a time limit in seconds; amix itself still receives a valid enum mode.
native = 'lib/core/services/native_tool_executor.dart'
replace_once(
    native,
    '''  /// Execute FFmpeg operation\n  Future<Map<String, dynamic>> _executeFFmpeg(Map<String, dynamic> args) async {''',
    r'''  String _extensionOf(String path) {
    final slash = path.lastIndexOf('/');
    final dot = path.lastIndexOf('.');
    return dot > slash ? path.substring(dot).toLowerCase() : '';
  }

  bool _isAudioOnlyOutput(String path) => const <String>{
    '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.wma', '.amr'
  }.contains(_extensionOf(path));

  String _audioCodecArgs(String outputPath, Map<String, dynamic> params) {
    final bitrate = params['bitrate'] ?? params['audio_bitrate'] ?? '192k';
    final ext = _extensionOf(outputPath);
    switch (ext) {
      case '.mp3':
        return '-c:a libmp3lame -b:a $bitrate';
      case '.wav':
        return '-c:a pcm_s16le';
      case '.flac':
        return '-c:a flac';
      case '.ogg':
      case '.opus':
        return '-c:a libopus -b:a $bitrate';
      case '.aac':
      case '.m4a':
        return '-c:a aac -b:a $bitrate';
      default:
        return '-c:a aac -b:a $bitrate';
    }
  }

  /// Execute FFmpeg operation
  Future<Map<String, dynamic>> _executeFFmpeg(Map<String, dynamic> args) async {''',
)

replace_once(
    native,
    '''        final durationMode = (params['duration'] ?? 'longest').toString();\n        command = '-y $inputs -filter_complex "${labels}amix=inputs=${effectiveInputs.length}:duration=$durationMode:normalize=0[a]" -map "[a]" "$outputPath"';''',
    '''        final rawDuration = params['duration'];\n        final requestedMode = (params['duration_mode'] ?? 'longest').toString().toLowerCase();\n        const modes = <String>{'longest', 'shortest', 'first'};\n        String durationMode;\n        String durationLimit = '';\n        if (rawDuration is num ||\n            (rawDuration is String && double.tryParse(rawDuration) != null)) {\n          final seconds = rawDuration is num\n              ? rawDuration.toDouble()\n              : double.parse(rawDuration.toString());\n          if (!seconds.isFinite || seconds <= 0) {\n            throw ArgumentError('mix_audio numeric duration must be greater than 0 seconds');\n          }\n          if (!modes.contains(requestedMode)) {\n            throw ArgumentError('mix_audio duration_mode must be longest, shortest, or first');\n          }\n          durationMode = requestedMode;\n          durationLimit = '-t $seconds';\n        } else {\n          durationMode = (rawDuration ?? requestedMode).toString().toLowerCase();\n          if (!modes.contains(durationMode)) {\n            throw ArgumentError('mix_audio duration accepts seconds or longest/shortest/first');\n          }\n        }\n        final audioCodec = _audioCodecArgs(outputPath, params);\n        command = '-y $inputs -filter_complex "${labels}amix=inputs=${effectiveInputs.length}:duration=$durationMode:normalize=0[a]" -map "[a]" $durationLimit $audioCodec "$outputPath"';''',
)

replace_once(
    native,
    '''      case 'convert':\n        final codec = params['codec'];\n        final quality = params['quality'] ?? 23;\n        // Ensure quality is a valid integer for CRF\n        final crf = (quality is int) ? quality : int.tryParse(quality.toString()) ?? 23;\n        if (codec != null) {\n          command = '-y -i "$inputPath" -c:v $codec -pix_fmt yuv420p -crf $crf -c:a aac "$outputPath"';\n        } else {\n          command = '-y -i "$inputPath" -c:v libx264 -pix_fmt yuv420p -crf $crf -c:a aac "$outputPath"';\n        }\n        break;''',
    '''      case 'convert':\n        final codec = params['codec'];\n        final quality = params['quality'] ?? 23;\n        final crf = (quality is int) ? quality : int.tryParse(quality.toString()) ?? 23;\n        final audioCodec = _audioCodecArgs(outputPath, params);\n        if (_isAudioOnlyOutput(outputPath)) {\n          command = '-y -i "$inputPath" -vn $audioCodec "$outputPath"';\n        } else {\n          final videoCodec = codec ?? 'libx264';\n          command = '-y -i "$inputPath" -c:v $videoCodec -pix_fmt yuv420p -crf $crf $audioCodec "$outputPath"';\n        }\n        break;''',
)

old_filter_tail = '''        // When video uses select (time-based frame selection), use filter_complex\n        // with explicit mapping to guarantee both A/V streams are filtered\n        if (vf != null && vf.toString().contains('select')) {\n          // Auto-generate matching audio filter if not provided\n          if (af == null) {\n            // Extract only select/setpts parts from vf for audio — strip\n            // video-only filters (hue, eq, colorbalance, etc.)\n            final vfParts = vf.toString().split(',');\n            final audioParts = <String>[];\n            for (final part in vfParts) {\n              if (part.contains('select')) {\n                audioParts.add(part.replaceAll('select=', 'aselect='));\n              } else if (part.contains('setpts')) {\n                audioParts.add(part\n                    .replaceAll('setpts=N/FRAME_RATE/TB', 'asetpts=N/SR/TB')\n                    .replaceAll('setpts=', 'asetpts='));\n              }\n              // Skip video-only filters (hue, eq, format, colorbalance, etc.)\n            }\n            af = audioParts.isNotEmpty ? audioParts.join(',') : null;\n            if (!vf.toString().contains('setpts')) {\n              vf = "$vf,setpts=N/FRAME_RATE/TB";\n            }\n            if (af != null && !af.toString().contains('asetpts')) {\n              af = "$af,asetpts=N/SR/TB";\n            }\n            if (af == null) {\n              af = "aselect='1',asetpts=N/SR/TB";\n            }\n          }\n          // Use filter_complex with explicit stream mapping\n          command = '-y -i "$inputPath" -filter_complex "[0:v]$vf[v];[0:a]$af[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 23 -c:a aac "$outputPath"';\n        } else if (vf != null && af != null) {\n          command = '-y -i "$inputPath" -vf "$vf" -af "$af" -c:v libx264 -pix_fmt yuv420p -crf 23 -c:a aac "$outputPath"';\n        } else if (vf != null) {\n          command = '-y -i "$inputPath" -vf "$vf" -c:v libx264 -pix_fmt yuv420p -crf 23 -c:a aac "$outputPath"';\n        } else {\n          command = '-y -i "$inputPath" -c:v copy -af "$af" -c:a aac "$outputPath"';\n        }\n        break;'''
new_filter_tail = '''        final audioCodec = _audioCodecArgs(outputPath, params);\n        final audioOnlyOutput = _isAudioOnlyOutput(outputPath);\n        if (audioOnlyOutput && vf != null) {\n          throw ArgumentError('A video filter cannot be written to an audio-only output file');\n        }\n        if (audioOnlyOutput) {\n          command = '-y -i "$inputPath" -vn -af "$af" $audioCodec "$outputPath"';\n        } else if (vf != null && vf.toString().contains('select')) {\n          if (af == null) {\n            final vfParts = vf.toString().split(',');\n            final audioParts = <String>[];\n            for (final part in vfParts) {\n              if (part.contains('select')) {\n                audioParts.add(part.replaceAll('select=', 'aselect='));\n              } else if (part.contains('setpts')) {\n                audioParts.add(part\n                    .replaceAll('setpts=N/FRAME_RATE/TB', 'asetpts=N/SR/TB')\n                    .replaceAll('setpts=', 'asetpts='));\n              }\n            }\n            af = audioParts.isNotEmpty ? audioParts.join(',') : null;\n            if (!vf.toString().contains('setpts')) {\n              vf = "$vf,setpts=N/FRAME_RATE/TB";\n            }\n            if (af != null && !af.toString().contains('asetpts')) {\n              af = "$af,asetpts=N/SR/TB";\n            }\n            if (af == null) {\n              af = "aselect='1',asetpts=N/SR/TB";\n            }\n          }\n          command = '-y -i "$inputPath" -filter_complex "[0:v]$vf[v];[0:a]$af[a]" -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -crf 23 $audioCodec "$outputPath"';\n        } else if (vf != null && af != null) {\n          command = '-y -i "$inputPath" -vf "$vf" -af "$af" -c:v libx264 -pix_fmt yuv420p -crf 23 $audioCodec "$outputPath"';\n        } else if (vf != null) {\n          command = '-y -i "$inputPath" -vf "$vf" -c:v libx264 -pix_fmt yuv420p -crf 23 $audioCodec "$outputPath"';\n        } else {\n          command = '-y -i "$inputPath" -c:v copy -af "$af" $audioCodec "$outputPath"';\n        }\n        break;'''
replace_once(native, old_filter_tail, new_filter_tail)

# OCR: successful OCR with no detected text carries an explicit machine-readable signal.
replace_once(
    native,
    '''      return {\n        'success': true,\n        'text': recognizedText.text,\n        'blocks': blocks,\n        'block_count': recognizedText.blocks.length,\n      };''',
    '''      final textDetected = recognizedText.text.trim().isNotEmpty;\n      return {\n        'success': true,\n        'text': recognizedText.text,\n        'text_detected': textDetected,\n        if (!textDetected) 'reason': 'no_text_detected',\n        'blocks': blocks,\n        'block_count': recognizedText.blocks.length,\n      };''',
)

print('V15 media patch applied.')

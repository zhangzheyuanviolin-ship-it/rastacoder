"""
Media Tools - Video/audio download and processing
"""

import os
from urllib.parse import urlparse

from ..bridge import ToolError, get_bridge
from ..utils.security import is_blocked_domain


def download_media(
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
            except (ImportError, OSError) as exc:
                detail = str(exc)
                if 'libc++_shared' in detail or 'dlopen' in detail.lower():
                    raise ToolError(
                        "Browser impersonation native runtime is incomplete: " + detail
                    ) from exc
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


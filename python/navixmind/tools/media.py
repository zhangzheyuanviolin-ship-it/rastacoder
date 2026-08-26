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
    """
    Download media from supported platforms.

    Args:
        url: URL of the media
        format: "video" or "audio"

    Returns:
        Dict with download result
    """
    import yt_dlp

    # Check for blocked domains (YouTube)
    if is_blocked_domain(url):
        raise ToolError(
            "YouTube downloads are not supported due to platform policies. "
            "Try TikTok, Instagram, or other supported platforms."
        )

    bridge = get_bridge()
    bridge.log("Extracting media info...")

    try:
        # Configure yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)

            # Check if it redirected to YouTube
            extractor = info.get('extractor', '').lower()
            if 'youtube' in extractor:
                raise ToolError(
                    "This link redirects to YouTube, which is not supported."
                )

            final_url = info.get('webpage_url', url)
            if is_blocked_domain(final_url):
                raise ToolError(
                    "This link redirects to a blocked platform."
                )

            # Get best format
            title = info.get('title', 'download')
            duration = info.get('duration', 0)

            bridge.log(f"Found: {title} ({duration}s)")

            # Request Flutter to perform the actual download
            # (yt-dlp extraction + native download for reliability)
            formats = info.get('formats', [])

            if format == "audio":
                # Find best audio format
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if not audio_formats:
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                best_format = audio_formats[-1] if audio_formats else formats[-1]
            else:
                # Find best video format
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                best_format = video_formats[-1] if video_formats else formats[-1]

            download_url = best_format.get('url')
            ext = best_format.get('ext', 'mp4')

            if not download_url:
                raise ToolError("Could not extract download URL")

            # Actually save the resolved media file. Earlier builds returned
            # download_url here even though no Flutter/native download handler existed.
            # Stream with the extractor-provided request headers when available.
            import re
            import requests
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
            request_headers = best_format.get('http_headers') or headers
            with requests.get(download_url, headers=request_headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                with open(final_path, 'wb') as out:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            out.write(chunk)
            return {
                "title": title,
                "duration": duration,
                "output_path": final_path,
                "size_bytes": os.path.getsize(final_path),
                "format": format,
                "extension": ext,
                "extractor": extractor,
                "success": True,
            }

    except yt_dlp.DownloadError as e:
        raise ToolError(f"Failed to extract media: {str(e)}")
    except Exception as e:
        raise ToolError(f"Media download failed: {str(e)}")

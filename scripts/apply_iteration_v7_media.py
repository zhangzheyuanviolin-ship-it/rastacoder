#!/usr/bin/env python3
from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v7 media anchor missing: {label}')
    return text.replace(old, new, 1)

# Make download_media perform the actual final HTTP transfer after yt-dlp has
# resolved a platform-specific media URL.
p = Path('python/navixmind/tools/media.py')
text = p.read_text()
text = replace_once(
    text,
    '''def download_media(\n    url: str,\n    format: str = "video"\n) -> dict:\n''',
    '''def download_media(\n    url: str,\n    format: str = "video",\n    output_path: str = None,\n    _output_dir: str = None,\n) -> dict:\n''',
    'download_media signature',
)
old_return = '''            return {\n                "title": title,\n                "duration": duration,\n                "download_url": download_url,\n                "format": format,\n                "extension": ext,\n                "extractor": extractor,\n            }\n'''
new_return = '''            # Actually save the resolved media file. Earlier builds returned\n            # download_url here even though no Flutter/native download handler existed.\n            # Stream with the extractor-provided request headers when available.\n            import re\n            import requests\n            safe_title = re.sub(r'[^\\w\\-. ()\\[\\]]+', '_', str(title)).strip(' ._') or 'download'\n            if output_path:\n                final_path = output_path\n            else:\n                root = _output_dir or os.getcwd()\n                os.makedirs(root, exist_ok=True)\n                final_path = os.path.join(root, f"{safe_title}.{ext}")\n            parent = os.path.dirname(final_path)\n            if parent:\n                os.makedirs(parent, exist_ok=True)\n            request_headers = best_format.get('http_headers') or headers\n            with requests.get(download_url, headers=request_headers, stream=True, timeout=60) as response:\n                response.raise_for_status()\n                with open(final_path, 'wb') as out:\n                    for chunk in response.iter_content(chunk_size=1024 * 1024):\n                        if chunk:\n                            out.write(chunk)\n            return {\n                "title": title,\n                "duration": duration,\n                "output_path": final_path,\n                "size_bytes": os.path.getsize(final_path),\n                "format": format,\n                "extension": ext,\n                "extractor": extractor,\n                "success": True,\n            }\n'''
text = replace_once(text, old_return, new_return, 'actual media transfer')
p.write_text(text)

# Add output_path to the schema and pass the app workspace to the Python tool.
p = Path('python/navixmind/tools/__init__.py')
text = p.read_text()
anchor = '''# Local inference and tool locality are independent. Expose these app-side\n'''
mutation = '''# RASTACODER_V7_MEDIA_DOWNLOAD\nfor _tool in TOOLS_SCHEMA:\n    if _tool.get("name") == "download_media":\n        _tool["description"] = "Resolve and actually download video/audio from supported platforms into the app workspace (not YouTube)."\n        _tool["input_schema"]["properties"]["output_path"] = {"type": "string", "description": "Optional output filename/path"}\n        break\n\n'''
text = replace_once(text, anchor, mutation + anchor, 'media schema mutation')
text = replace_once(
    text,
    '    if tool_name in {"list_files", "file_manage", "extract_zip", "pdf_manage"} and output_dir:\n'
    '        args["_output_dir"] = output_dir\n',
    '    if tool_name in {"list_files", "file_manage", "extract_zip", "pdf_manage", "download_media"} and output_dir:\n'
    '        args["_output_dir"] = output_dir\n',
    'media workspace injection',
)
p.write_text(text)

p = Path('lib/core/models/tool_skill.dart')
text = p.read_text()
text = text.replace(
    "capabilities: ['视频资源解析', '纯音频资源解析', '媒体元信息', '列出/管理下载结果'],",
    "capabilities: ['视频资源解析并实际下载', '纯音频资源解析并实际下载', '自动文件命名', '媒体元信息', '列出/管理下载结果'],",
)
p.write_text(text)
print('Applied v7 actual media download patch')

#!/usr/bin/env python3
"""Apply RastaCoder v6 local-tool reliability hardening.

This patch intentionally targets the v5 persisted source and is designed to be
idempotent enough for CI replay from the known-good v5 state.
"""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Replace the compatibility layer with a context-aware small-model repairer.
# ---------------------------------------------------------------------------
compat = r'''"""Tool-call compatibility helpers for local/small LLMs.

Canonical schemas remain strict. This module repairs common surface mistakes
from 3B-4B models before schema validation while recording every repair.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


# Canonical function-name aliases that are safe without argument context.
TOOL_ALIASES = {
    "python": "python_execute",
    "run_python": "python_execute",
    "python_exec": "python_execute",
    "python_tool": "python_execute",
    "ffmpeg": "ffmpeg_process",
    "ffmpeg_tool": "ffmpeg_process",
    "video_edit": "ffmpeg_process",
    "video_editor": "ffmpeg_process",
    "audio_edit": "ffmpeg_process",
    "audio_editor": "ffmpeg_process",
    "audio_convert": "ffmpeg_process",
    "video_convert": "ffmpeg_process",
    "ocr": "ocr_image",
    "image_ocr": "ocr_image",
    "browser": "headless_browser",
    "browse": "headless_browser",
    "dynamic_browser": "headless_browser",
    "convert_file": "convert_document",
    "document_convert": "convert_document",
    "doc_convert": "convert_document",
    "create_word": "create_docx",
    "create_word_document": "create_docx",
    "write_docx": "create_docx",
    "new_docx": "create_docx",
    "read_word": "read_docx",
    "read_word_document": "read_docx",
    "edit_word": "modify_docx",
    "modify_word": "modify_docx",
    "read_powerpoint": "read_pptx",
    "read_presentation": "read_pptx",
    "edit_powerpoint": "modify_pptx",
    "modify_powerpoint": "modify_pptx",
    "read_excel": "read_xlsx",
    "read_spreadsheet": "read_xlsx",
    "edit_excel": "modify_xlsx",
    "modify_excel": "modify_xlsx",
    "calendar": "google_calendar",
    "google_calendar_tool": "google_calendar",
    "email": "gmail",
    "google_mail": "gmail",
    "zip": "create_zip",
    "zip_files": "create_zip",
}

# v5 exposed these UI Skill IDs to the model. v6 no longer does that, but the
# compatibility layer deliberately accepts them so old conversation history or
# a hallucinated Skill name cannot break execution.
SINGLE_TOOL_SKILL_ALIASES = {
    "zip_archive": "create_zip",
    "pdf_read": "read_pdf",
    "pdf_create": "create_pdf",
    "document_convert": "convert_document",
    "ocr": "ocr_image",
    "image_processing": "smart_crop",
    "video_processing": "ffmpeg_process",
    "audio_processing": "ffmpeg_process",
    "media_download": "download_media",
    "dynamic_web": "headless_browser",
    "basic_calculation": "python_execute",
    "scientific_calculation": "python_execute",
    "data_analysis": "python_execute",
    "charts": "python_execute",
}

AUDIO_EXTS = {"mp3", "wav", "m4a", "aac", "flac", "ogg", "opus", "wma", "amr"}
VIDEO_EXTS = {"mp4", "mkv", "mov", "avi", "webm", "m4v", "3gp", "ts"}
IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "bmp", "gif", "heic", "heif"}
DOC_EXTS = {"txt", "docx", "pdf", "html", "htm"}


def _token(name: Any) -> str:
    value = str(name or "").strip().lower().replace("-", "_").replace(" ", "_")
    if value.endswith("()"):
        value = value[:-2]
    return value


def normalize_tool_name(name: Any) -> str:
    value = _token(name)
    value = TOOL_ALIASES.get(value, value)
    return SINGLE_TOOL_SKILL_ALIASES.get(value, value)


def _move_alias(args: Dict[str, Any], target: str, aliases: Iterable[str], notes: List[str]) -> None:
    if target in args and args[target] not in (None, ""):
        return
    for alias in aliases:
        if alias in args and args[alias] not in (None, ""):
            args[target] = args.pop(alias)
            notes.append(f"{alias}->{target}")
            return


def _freeform(args: Dict[str, Any]) -> str:
    for key in ("param", "request", "instruction", "command"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _contains_any(text: str, words: Iterable[str]) -> bool:
    lower = text.lower()
    return any(word in lower for word in words)


def _route_ambiguous_skill(name: str, args: Dict[str, Any], notes: List[str]) -> str:
    """Map UI-only multi-tool Skill names using deterministic argument intent."""
    if name not in {"text_files", "word", "powerpoint", "excel"}:
        return name
    free = _freeform(args).lower()
    keys = set(args)

    if name == "text_files":
        if keys & {"content", "text", "body"} or _contains_any(free, ("write", "create", "save", "写入", "创建", "保存")):
            routed = "write_file"
        elif _contains_any(free, ("info", "metadata", "size", "stat", "信息", "大小")):
            routed = "file_info"
        else:
            routed = "read_file"
    elif name == "word":
        if keys & {"operations", "operation"} or _contains_any(free, ("modify", "edit", "replace", "修改", "替换", "编辑")):
            routed = "modify_docx"
        elif keys & {"docx_path", "extract"} or _contains_any(free, ("read", "extract", "inspect", "读取", "提取")):
            routed = "read_docx"
        else:
            routed = "create_docx"
    elif name == "powerpoint":
        if keys & {"operations", "operation"} or _contains_any(free, ("modify", "edit", "replace", "修改", "替换", "编辑")):
            routed = "modify_pptx"
        else:
            routed = "read_pptx"
    else:  # excel
        if keys & {"operations", "operation"} or _contains_any(free, ("modify", "edit", "set", "add", "delete", "修改", "编辑", "新增", "删除")):
            routed = "modify_xlsx"
        else:
            routed = "read_xlsx"

    notes.append(f"skill:{name}->{routed}")
    return routed


def _extract_file_tokens(text: str) -> List[str]:
    results: List[str] = []
    # Quoted paths can contain spaces.
    for m in re.finditer(r'''["']([^"']+\.[A-Za-z0-9]{1,6})["']''', text):
        results.append(m.group(1).strip())
    # Common unquoted Android/model basenames.
    for m in re.finditer(r'''(?<![\w])([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]{1,6})(?![\w])''', text):
        value = m.group(1).strip().rstrip(".,;:)")
        if value not in results:
            results.append(value)
    return results


def _extract_url(text: str) -> Optional[str]:
    m = re.search(r'''https?://[^\s<>"']+''', text)
    return m.group(0).rstrip(".,;)") if m else None


def _target_format(text: str) -> Optional[str]:
    patterns = (
        r'''\b(?:to|into|as)\s+\.?([A-Za-z0-9]{2,5})\b''',
        r'''(?:转成|转换成|转为|转换为)\s*\.?([A-Za-z0-9]{2,5})\b''',
    )
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).lower().lstrip(".")
    return None


def _extension(path: Any) -> str:
    if not isinstance(path, str):
        return ""
    return os.path.splitext(path)[1].lower().lstrip(".")


def _derive_output(input_path: str, suffix: str, extension: Optional[str] = None) -> str:
    base = os.path.basename(input_path)
    stem, ext = os.path.splitext(base)
    out_ext = (extension or ext.lstrip(".") or "out").lstrip(".")
    return f"{stem}_{suffix}.{out_ext}"


def _apply_freeform(name: str, args: Dict[str, Any], free: str, notes: List[str]) -> None:
    if not free:
        return
    files = _extract_file_tokens(free)
    url = _extract_url(free)

    if name in {"read_pdf", "read_docx", "read_pptx", "read_xlsx", "ocr_image", "read_file", "file_info"} and files:
        key = {
            "read_pdf": "pdf_path", "read_docx": "docx_path", "read_pptx": "pptx_path",
            "read_xlsx": "xlsx_path", "ocr_image": "image_path", "read_file": "file_path",
            "file_info": "file_path",
        }[name]
        if key not in args:
            args[key] = files[0]
            notes.append(f"freeform->{key}")

    if name in {"ffmpeg_process", "smart_crop", "convert_document", "modify_docx", "modify_pptx", "modify_xlsx"} and files:
        if "input_path" not in args:
            args["input_path"] = files[0]
            notes.append("freeform->input_path")

    if name == "create_zip" and files and "file_paths" not in args:
        args["file_paths"] = files
        notes.append("freeform->file_paths")

    if name in {"web_fetch", "headless_browser", "download_media"} and url and "url" not in args:
        args["url"] = url
        notes.append("freeform->url")

    if name == "python_execute" and "code" not in args:
        args["code"] = free
        notes.append("param->code")

    if name == "convert_document":
        fmt = _target_format(free)
        if fmt and "output_format" not in args:
            args["output_format"] = fmt
            notes.append("freeform->output_format")

    if name == "ffmpeg_process":
        fmt = _target_format(free)
        if fmt:
            params = args.get("params") if isinstance(args.get("params"), dict) else {}
            params = dict(params)
            input_ext = _extension(args.get("input_path"))
            # Audio-output conversion is deliberately routed through the native
            # extract_audio branch. The native 'convert' branch is video-oriented.
            if fmt in AUDIO_EXTS:
                args["operation"] = "extract_audio"
                params["format"] = fmt
                notes.append(f"audio-target->{fmt}:extract_audio")
            elif "operation" not in args:
                args["operation"] = "convert"
                notes.append("freeform->operation:convert")
            if "output_path" not in args and isinstance(args.get("input_path"), str):
                suffix = "audio" if fmt in AUDIO_EXTS else "converted"
                args["output_path"] = _derive_output(args["input_path"], suffix, fmt)
                notes.append("derived:output_path")
            if params:
                args["params"] = params
        elif "operation" not in args:
            lower = free.lower()
            if _contains_any(lower, ("trim", "cut", "clip", "裁剪", "截取")):
                args["operation"] = "trim"
                notes.append("freeform->operation:trim")
            elif _contains_any(lower, ("extract audio", "audio only", "提取音频")):
                args["operation"] = "extract_audio"
                notes.append("freeform->operation:extract_audio")
            elif _contains_any(lower, ("convert", "transcode", "转换")):
                args["operation"] = "convert"
                notes.append("freeform->operation:convert")

    if name == "google_calendar" and "action" not in args:
        lower = free.lower()
        if _contains_any(lower, ("delete", "remove", "删除")):
            args["action"] = "delete"
        elif _contains_any(lower, ("create", "add", "new", "创建", "新增")):
            args["action"] = "create"
        elif _contains_any(lower, ("list", "show", "events", "查看", "列出")):
            args["action"] = "list"
        if "action" in args:
            notes.append("freeform->action")

    if name == "gmail" and "action" not in args:
        lower = free.lower()
        if _contains_any(lower, ("read", "open", "读取", "打开")):
            args["action"] = "read"
        elif _contains_any(lower, ("list", "search", "find", "列出", "搜索")):
            args["action"] = "list"
        if "action" in args:
            notes.append("freeform->action")


def _current_files(context: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(context, dict):
        return []
    values = context.get("_current_files")
    if isinstance(values, list):
        return [str(v) for v in values if isinstance(v, str) and v]
    return []


def _known_files(context: Optional[Dict[str, Any]]) -> List[str]:
    current = _current_files(context)
    if current:
        return current
    if not isinstance(context, dict):
        return []
    file_map = context.get("_file_map")
    if isinstance(file_map, dict):
        values: List[str] = []
        for value in file_map.values():
            if isinstance(value, str) and value and value not in values:
                values.append(value)
        return values
    return []


def _unique_matching(context: Optional[Dict[str, Any]], extensions: Optional[set[str]] = None) -> Optional[str]:
    candidates = _known_files(context)
    if extensions is not None:
        candidates = [p for p in candidates if _extension(p) in extensions]
    return candidates[0] if len(candidates) == 1 else None


def _repair_with_context(name: str, args: Dict[str, Any], context: Optional[Dict[str, Any]], notes: List[str]) -> None:
    if not isinstance(context, dict):
        return

    path_requirements = {
        "read_pdf": ("pdf_path", {"pdf"}),
        "read_docx": ("docx_path", {"docx"}),
        "read_pptx": ("pptx_path", {"pptx"}),
        "read_xlsx": ("xlsx_path", {"xlsx"}),
        "ocr_image": ("image_path", IMAGE_EXTS),
        "read_file": ("file_path", None),
        "file_info": ("file_path", None),
        "ffmpeg_process": ("input_path", AUDIO_EXTS | VIDEO_EXTS),
        "smart_crop": ("input_path", IMAGE_EXTS | VIDEO_EXTS),
        "convert_document": ("input_path", DOC_EXTS),
        "modify_docx": ("input_path", {"docx"}),
        "modify_pptx": ("input_path", {"pptx"}),
        "modify_xlsx": ("input_path", {"xlsx"}),
    }
    spec = path_requirements.get(name)
    if spec:
        key, exts = spec
        if not args.get(key):
            inferred = _unique_matching(context, exts)
            if inferred:
                args[key] = inferred
                notes.append(f"inferred:{key}:unique_attachment")

    current = _current_files(context)
    if name == "create_zip" and not args.get("file_paths"):
        if current:
            args["file_paths"] = list(current)
            notes.append("inferred:file_paths:current_attachments")
        else:
            only = _unique_matching(context, None)
            if only:
                args["file_paths"] = [only]
                notes.append("inferred:file_paths:unique_known_file")

    if name == "create_pdf" and not args.get("content") and not args.get("image_paths"):
        images = [p for p in current if _extension(p) in IMAGE_EXTS]
        if images:
            args["image_paths"] = images
            notes.append("inferred:image_paths:current_images")

    if name == "python_execute" and "file_paths" not in args and current:
        args["file_paths"] = list(current)
        notes.append("inferred:file_paths:current_attachments")

    # Safe output-name synthesis. These are always new output names and are
    # subsequently resolved under the app's writable output directory.
    if name == "create_docx" and not args.get("output_path") and args.get("content") is not None:
        args["output_path"] = "document.docx"
        notes.append("default:output_path=document.docx")
    elif name == "create_pdf" and not args.get("output_path") and (args.get("content") or args.get("image_paths")):
        args["output_path"] = "document.pdf"
        notes.append("default:output_path=document.pdf")
    elif name == "write_file" and not args.get("output_path") and args.get("content") is not None:
        args["output_path"] = "output.txt"
        notes.append("default:output_path=output.txt")
    elif name == "create_zip" and not args.get("output_path") and args.get("file_paths"):
        args["output_path"] = "archive.zip"
        notes.append("default:output_path=archive.zip")

    if name in {"modify_docx", "modify_pptx", "modify_xlsx"} and not args.get("output_path") and isinstance(args.get("input_path"), str):
        ext = {"modify_docx": "docx", "modify_pptx": "pptx", "modify_xlsx": "xlsx"}[name]
        args["output_path"] = _derive_output(args["input_path"], "modified", ext)
        notes.append("derived:output_path")

    if name == "smart_crop" and not args.get("output_path") and isinstance(args.get("input_path"), str):
        ext = _extension(args["input_path"]) or "mp4"
        args["output_path"] = _derive_output(args["input_path"], "cropped", ext)
        notes.append("derived:output_path")

    if name == "ffmpeg_process" and isinstance(args.get("input_path"), str):
        params = args.get("params") if isinstance(args.get("params"), dict) else {}
        params = dict(params)
        in_ext = _extension(args["input_path"])
        out_ext = _extension(args.get("output_path"))
        requested_fmt = str(params.get("format") or "").lower().lstrip(".")

        # Correct a common small-model choice: audio conversion should use the
        # native audio branch, which handles WAV/MP3/AAC/FLAC/OGG reliably.
        target_audio = requested_fmt if requested_fmt in AUDIO_EXTS else (out_ext if out_ext in AUDIO_EXTS else "")
        if target_audio and (in_ext in AUDIO_EXTS or out_ext in AUDIO_EXTS):
            if args.get("operation") in (None, "convert", "extract_audio"):
                if args.get("operation") != "extract_audio":
                    notes.append(f"operation:{args.get('operation')}->extract_audio")
                args["operation"] = "extract_audio"
                params["format"] = target_audio
        if args.get("operation") == "extract_audio":
            fmt = str(params.get("format") or out_ext or "mp3").lower().lstrip(".")
            params["format"] = fmt
            if not args.get("output_path"):
                args["output_path"] = _derive_output(args["input_path"], "audio", fmt)
                notes.append("derived:output_path")
        elif args.get("operation") and not args.get("output_path"):
            ext = out_ext or in_ext or "mp4"
            args["output_path"] = _derive_output(args["input_path"], str(args["operation"]), ext)
            notes.append("derived:output_path")
        if params or "params" in args:
            args["params"] = params


def normalize_tool_call(
    tool_name: Any,
    raw_args: Any,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], List[str]]:
    notes: List[str] = []
    original_name = str(tool_name or "")
    raw_token = _token(original_name)

    if isinstance(raw_args, dict):
        args = dict(raw_args)
    elif isinstance(raw_args, str) and raw_args.strip():
        args = {"param": raw_args.strip()}
        notes.append("string_args->param")
    else:
        args = {}

    # Some small models wrap arguments one level too deeply.
    for wrapper in ("arguments", "args", "parameters", "input"):
        nested = args.get(wrapper)
        if isinstance(nested, dict) and len(args) == 1:
            args = dict(nested)
            notes.append(f"unwrapped:{wrapper}")
            break

    name = TOOL_ALIASES.get(raw_token, raw_token)
    name = SINGLE_TOOL_SKILL_ALIASES.get(name, name)
    name = _route_ambiguous_skill(name, args, notes)
    if name != raw_token and not any(n.startswith("skill:") for n in notes):
        notes.append(f"tool:{original_name}->{name}")

    read_path_key = {
        "read_pdf": "pdf_path", "read_docx": "docx_path", "read_pptx": "pptx_path",
        "read_xlsx": "xlsx_path", "ocr_image": "image_path", "read_file": "file_path",
        "file_info": "file_path",
    }.get(name)
    if read_path_key:
        _move_alias(args, read_path_key, ["file", "path", "source", "source_path", "input", "input_file", "filename"], notes)

    if name in {"ffmpeg_process", "smart_crop", "convert_document", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "input_path", ["file", "path", "source", "source_path", "input", "input_file", "filename"], notes)

    if name in {"ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file", "create_zip", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "output_path", ["output", "destination", "dest", "target", "target_path", "output_file", "filename_out"], notes)

    free = _freeform(args)
    _apply_freeform(name, args, free, notes)

    if name == "convert_document":
        _move_alias(args, "output_format", ["format", "target_format", "to", "to_format"], notes)
        _move_alias(args, "output_path", ["output", "destination", "dest", "target_path", "output_file"], notes)
        if "output_format" in args:
            raw = str(args["output_format"]).strip().lower()
            aliases = {
                "word": "docx", "microsoft word": "docx", "msword": "docx", ".docx": "docx",
                "text": "txt", "plain text": "txt", ".txt": "txt",
                "htm": "html", ".html": "html", ".htm": "html", ".pdf": "pdf",
            }
            normalized = aliases.get(raw, raw.lstrip("."))
            if normalized != raw:
                notes.append(f"output_format:{raw}->{normalized}")
            args["output_format"] = normalized

    if name == "create_docx":
        _move_alias(args, "content", ["text", "body", "document_text", "document_content"], notes)

    if name == "create_pdf":
        _move_alias(args, "content", ["text", "body", "document_text", "document_content"], notes)
        if "image_path" in args and "image_paths" not in args:
            args["image_paths"] = [args.pop("image_path")]
            notes.append("image_path->image_paths")
        if isinstance(args.get("image_paths"), str):
            args["image_paths"] = [args["image_paths"]]
            notes.append("image_paths:string->list")

    if name == "write_file":
        _move_alias(args, "content", ["text", "body", "data"], notes)

    if name == "create_zip":
        _move_alias(args, "file_paths", ["files", "inputs", "paths"], notes)
        if isinstance(args.get("file_paths"), str):
            args["file_paths"] = [args["file_paths"]]
            notes.append("file_paths:string->list")

    if name == "ffmpeg_process":
        _move_alias(args, "operation", ["action", "op", "task"], notes)
        if "operation" in args:
            raw = str(args["operation"]).strip().lower().replace("-", "_").replace(" ", "_")
            aliases = {
                "cut": "trim", "clip": "trim", "crop_video": "crop",
                "scale": "resize", "rescale": "resize",
                "effects": "filter", "effect": "filter",
                "audio": "extract_audio", "extractaudio": "extract_audio", "extract_sound": "extract_audio",
                "frame": "extract_frame", "screenshot": "extract_frame",
                "transcode": "convert", "conversion": "convert",
            }
            normalized = aliases.get(raw, raw)
            if normalized != raw:
                notes.append(f"operation:{raw}->{normalized}")
            args["operation"] = normalized

        params = args.get("params")
        if not isinstance(params, dict):
            params = {}
        for key in ("start", "end", "duration", "width", "height", "x", "y", "vf", "af", "video_filter", "audio_filter", "format", "bitrate", "timestamp", "codec", "quality", "args"):
            if key in args and key not in params:
                params[key] = args.pop(key)
                notes.append(f"top-level:{key}->params.{key}")
        if "codec" in params:
            codec_raw = str(params["codec"]).lower().strip()
            codec = {"h264": "libx264", "avc": "libx264", "h265": "libx265", "hevc": "libx265"}.get(codec_raw, codec_raw)
            if codec != codec_raw:
                notes.append(f"codec:{codec_raw}->{codec}")
            params["codec"] = codec
        if params or "params" in args:
            args["params"] = params

    if name == "smart_crop" and "aspect_ratio" in args:
        original = str(args["aspect_ratio"]).strip()
        ratio = original.lower().replace("x", ":").replace("/", ":")
        if ratio != original:
            notes.append(f"aspect_ratio:{original}->{ratio}")
        args["aspect_ratio"] = ratio

    if name in {"modify_docx", "modify_pptx", "modify_xlsx"}:
        if isinstance(args.get("operations"), dict):
            args["operations"] = [args["operations"]]
            notes.append("operations:object->list")
        if "operation" in args and "operations" not in args and isinstance(args["operation"], dict):
            args["operations"] = [args.pop("operation")]
            notes.append("operation->operations")

    if name == "google_calendar":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "date_range", ["date", "range", "time_range"], notes)
        _move_alias(args, "event_id", ["id", "calendar_event_id"], notes)
        if "action" in args:
            action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {"get": "list", "show": "list", "list_events": "list", "add": "create", "new": "create", "create_event": "create", "remove": "delete", "delete_event": "delete"}.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    if name == "gmail":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "message_id", ["id", "email_id", "mail_id"], notes)
        if "action" in args:
            action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {"get": "read", "open": "read", "read_message": "read", "search": "list", "find": "list", "list_messages": "list"}.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    # Generic free-form keys are compatibility scaffolding, never canonical
    # tool arguments. Remove them after extracting deterministic information.
    for key in ("param", "request", "instruction", "command"):
        if key in args:
            args.pop(key, None)
            notes.append(f"removed:{key}")

    _repair_with_context(name, args, context, notes)
    return name, args, notes
'''
Path('python/navixmind/tools/compat.py').write_text(compat, encoding='utf-8')


# ---------------------------------------------------------------------------
# 2) Make Skill IDs UI-only and inject only canonical callable signatures.
# ---------------------------------------------------------------------------
tools_path = Path('python/navixmind/tools/__init__.py')
tools_text = tools_path.read_text(encoding='utf-8')
start = tools_text.index('# RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM')
end = tools_text.index('# Import-time invariant:', start)
new_skill_block = r'''# RASTACODER_V6_TOOL_RELIABILITY
# Skill IDs are UI-only. They are deliberately never shown to the model.
# The model sees canonical callable function names only.
LOCAL_SKILLS = {
    "text_files": {"tools": ("read_file", "write_file", "file_info")},
    "zip_archive": {"tools": ("create_zip", "file_info")},
    "pdf_read": {"tools": ("read_pdf", "file_info")},
    "pdf_create": {"tools": ("create_pdf",)},
    "document_convert": {"tools": ("convert_document",)},
    "word": {"tools": ("create_docx", "read_docx", "modify_docx")},
    "powerpoint": {"tools": ("read_pptx", "modify_pptx")},
    "excel": {"tools": ("read_xlsx", "modify_xlsx")},
    "ocr": {"tools": ("ocr_image",)},
    "image_processing": {"tools": ("smart_crop",)},
    "video_processing": {"tools": ("ffmpeg_process",)},
    "audio_processing": {"tools": ("ffmpeg_process",)},
    "media_download": {"tools": ("download_media",)},
    "web_fetch": {"tools": ("web_fetch",)},
    "dynamic_web": {"tools": ("headless_browser",)},
    "basic_calculation": {"tools": ("python_execute",)},
    "scientific_calculation": {"tools": ("python_execute",)},
    "data_analysis": {"tools": ("python_execute",)},
    "charts": {"tools": ("python_execute",)},
    "gmail": {"tools": ("gmail",)},
    "google_calendar": {"tools": ("google_calendar",)},
}

ALL_LOCAL_SKILL_IDS = tuple(LOCAL_SKILLS.keys())

LOCAL_TOOL_PROMPT_HINTS = {
    "read_file": "read_file(file_path)",
    "write_file": "write_file(output_path, content)",
    "file_info": "file_info(file_path)",
    "create_zip": "create_zip(output_path, file_paths, compression?)",
    "read_pdf": "read_pdf(pdf_path, pages?)",
    "create_pdf": "create_pdf(output_path, content?, title?, image_paths?)",
    "convert_document": "convert_document(input_path, output_format, output_path?) ; output_format=pdf|html|txt|docx",
    "create_docx": "create_docx(output_path, content, title?)",
    "read_docx": "read_docx(docx_path, extract?)",
    "modify_docx": "modify_docx(input_path, output_path, operations)",
    "read_pptx": "read_pptx(pptx_path, extract?)",
    "modify_pptx": "modify_pptx(input_path, output_path, operations)",
    "read_xlsx": "read_xlsx(xlsx_path, sheet?, range?, extract?)",
    "modify_xlsx": "modify_xlsx(input_path, output_path, operations)",
    "ocr_image": "ocr_image(image_path)",
    "smart_crop": "smart_crop(input_path, output_path, aspect_ratio?)",
    "ffmpeg_process": "ffmpeg_process(input_path, output_path, operation, params?) ; operations=trim|crop|resize|filter|extract_audio|extract_frame|convert ; for MP3/WAV/M4A/AAC/FLAC/OGG audio output use operation=extract_audio and params.format",
    "download_media": "download_media(url, format?)",
    "web_fetch": "web_fetch(url, extract_mode?)",
    "headless_browser": "headless_browser(url, wait_seconds?, extract_selector?)",
    "python_execute": "python_execute(code, file_paths?)",
    "gmail": "gmail(action, query?, message_id?) ; action=list|read",
    "google_calendar": "google_calendar(action, date_range?, event?, event_id?) ; action=list|create|delete",
}


def _offline_tool_names():
    return {tool["name"] for tool in OFFLINE_TOOLS_SCHEMA}


def get_enabled_tool_names(skill_ids=None):
    if skill_ids is None:
        skill_ids = ALL_LOCAL_SKILL_IDS
    enabled = set()
    for skill_id in skill_ids:
        skill = LOCAL_SKILLS.get(str(skill_id))
        if skill:
            enabled.update(skill["tools"])
    return enabled


def get_offline_tools_for_skills(skill_ids=None):
    enabled = get_enabled_tool_names(skill_ids)
    return [tool for tool in OFFLINE_TOOLS_SCHEMA if tool["name"] in enabled]


def build_offline_skill_prompt(skill_ids=None):
    ids = ALL_LOCAL_SKILL_IDS if skill_ids is None else tuple(str(x) for x in skill_ids)
    selected = [skill_id for skill_id in ids if skill_id in LOCAL_SKILLS]
    base = (
        "You are RastaCoder, an AI assistant on Android. Tool availability is manually selected by the user. "
        "UI Skill/category labels are not callable functions and are intentionally omitted from this prompt."
    )
    if not selected:
        return base + " No tools are enabled. Answer directly and never emit a tool call."

    enabled_tools = get_enabled_tool_names(selected)
    ordered_tools = [t["name"] for t in OFFLINE_TOOLS_SCHEMA if t["name"] in enabled_tools]
    lines = [
        base,
        "When a tool is needed, output ONLY this XML wrapper with valid JSON inside:",
        "<tool_call>",
        '{"name":"CANONICAL_FUNCTION_NAME","arguments":{"exact_parameter_name":"value"}}',
        "</tool_call>",
        "CALLABLE FUNCTIONS (these exact names only):",
    ]
    for tool_name in ordered_tools:
        lines.append(f"- {LOCAL_TOOL_PROMPT_HINTS[tool_name]}")
    lines.extend([
        "STRICT TOOL-CALL RULES:",
        "- The name field MUST be one canonical function name listed above. Never call a Skill/category label.",
        "- arguments MUST use the exact parameter names shown in that function signature.",
        "- Never invent generic argument keys such as param, request, instruction, or command.",
        "- Use attached file basenames exactly as shown in the user message; the app resolves them to real paths.",
        "- Choose a sensible output filename yourself. Do not ask the user for an output path when a filename can be chosen safely.",
        "- Do not place prose before or after a tool call. After the tool result, give the concise final answer.",
        "- Use only the callable functions listed above.",
    ])
    return "\n".join(lines)


'''
tools_text = tools_text[:start] + new_skill_block + tools_text[end:]

# Execute-time normalization must be context-aware so it can infer a unique
# attachment and safe output filename before strict schema validation.
tools_text = replace_once(
    tools_text,
    'tool_name, args, compatibility_notes = normalize_tool_call(tool_name, args)',
    'tool_name, args, compatibility_notes = normalize_tool_call(tool_name, args, context=context)',
    'context-aware normalize_tool_call',
)

# Move the manual Skill boundary before schema validation and add diagnostics.
old = r'''    # Validate required parameters and top-level enum values using the canonical
    # schema before calling implementation code.
    schema_entry = next((t for t in TOOLS_SCHEMA if t.get("name") == tool_name), None)
    if schema_entry:
        input_schema = schema_entry.get("input_schema", {})
        missing = [
            key for key in input_schema.get("required", [])
            if key not in args or args.get(key) is None
        ]
        if missing:
            raise ToolError(
                f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name} missing required "
                f"parameter(s): {', '.join(missing)}. Received: {sorted(args.keys())}"
            )
        for key, spec in input_schema.get("properties", {}).items():
            if key in args and isinstance(spec, dict) and spec.get("enum"):
                if args[key] not in spec["enum"]:
                    raise ToolError(
                        f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name}.{key} received "
                        f"{args[key]!r}; allowed values: {spec['enum']}"
                    )

    # Manual skill boundary: a hallucinated disabled tool is rejected even
    # if the small model remembers its name from earlier conversation.
    allowed_tools = context.get('_allowed_tools')
    if allowed_tools is not None and tool_name not in set(allowed_tools):
        raise ToolError(
            f"[MODEL_TOOL_DISABLED] Tool '{tool_name}' is not enabled for this conversation."
        )
'''
new = r'''    # Manual Skill boundary comes before schema validation. A hallucinated
    # disabled tool must never be repaired into an executable call.
    allowed_tools = context.get('_allowed_tools')
    if allowed_tools is not None and tool_name not in set(allowed_tools):
        _record_tool_diag(context, "disabled", tool=tool_name, original_tool=original_tool_name)
        raise ToolError(
            f"[MODEL_TOOL_DISABLED] Tool '{tool_name}' is not enabled for this conversation."
        )

    _record_tool_diag(
        context, "normalized", tool=tool_name, original_tool=original_tool_name,
        args=_safe_diag_value(args), repairs=compatibility_notes,
    )

    # Validate required parameters and top-level enum values only after the
    # compatibility layer has synthesized deterministic safe defaults.
    schema_entry = next((t for t in TOOLS_SCHEMA if t.get("name") == tool_name), None)
    if schema_entry:
        input_schema = schema_entry.get("input_schema", {})
        missing = [
            key for key in input_schema.get("required", [])
            if key not in args or args.get(key) is None or args.get(key) == ""
        ]
        if missing:
            _record_tool_diag(context, "schema_error", tool=tool_name, missing=missing, args=_safe_diag_value(args))
            raise ToolError(
                f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name} missing required "
                f"parameter(s): {', '.join(missing)}. Received: {sorted(args.keys())}. "
                "Retry the same enabled tool with corrected arguments; choose a sensible output filename yourself when only output_path is missing."
            )
        for key, spec in input_schema.get("properties", {}).items():
            if key in args and isinstance(spec, dict) and spec.get("enum"):
                if args[key] not in spec["enum"]:
                    _record_tool_diag(context, "enum_error", tool=tool_name, key=key, value=args[key])
                    raise ToolError(
                        f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name}.{key} received "
                        f"{args[key]!r}; allowed values: {spec['enum']}. Retry with one allowed value."
                    )
'''
tools_text = replace_once(tools_text, old, new, 'schema/skill boundary')

# Add diagnostics helpers before execute_tool.
anchor = '\ndef execute_tool(\n'
diag_helpers = r'''

def _safe_diag_value(value: Any) -> Any:
    """Redact secrets and bound large diagnostic payloads."""
    secret_words = {"api_key", "access_token", "google_access_token", "authorization", "token", "password"}
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_s = str(key)
            if key_s.lower() in secret_words or key_s == "_context":
                out[key_s] = "[REDACTED]"
            else:
                out[key_s] = _safe_diag_value(item)
        return out
    if isinstance(value, list):
        return [_safe_diag_value(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + "...[truncated]"
    return value


def _record_tool_diag(context: Dict[str, Any], stage: str, **fields: Any) -> None:
    if not isinstance(context, dict):
        return
    events = context.setdefault('_diagnostics', [])
    if not isinstance(events, list):
        return
    event = {"stage": stage}
    event.update({k: _safe_diag_value(v) for k, v in fields.items()})
    events.append(event)

'''
if diag_helpers.strip() not in tools_text:
    tools_text = tools_text.replace(anchor, diag_helpers + anchor, 1)

# Record resolved paths and executor outcome vicinity. Resolution happens after
# strict validation because defaults are already synthesized; basename mapping
# then produces the real Android paths.
old = r'''    # Add context to args for tools that need it
    if tool_name in ["google_calendar", "gmail"]:
        args["_context"] = context
'''
new = r'''    _record_tool_diag(context, "paths_resolved", tool=tool_name, args=_safe_diag_value(args))

    # Add context to args for tools that need it
    if tool_name in ["google_calendar", "gmail"]:
        args["_context"] = context
'''
tools_text = replace_once(tools_text, old, new, 'paths diagnostic')

tools_path.write_text(tools_text, encoding='utf-8')


# ---------------------------------------------------------------------------
# 3) Agent parser: normalize Skill aliases before known-name rejection, retain
#    reasoning separately, prevent raw tool tags leaking into final prose, and
#    return copyable structured diagnostics.
# ---------------------------------------------------------------------------
agent_path = Path('python/navixmind/agent.py')
agent = agent_path.read_text(encoding='utf-8')

old = r'''def _build_tool_use(name: Any, arguments: Any, source: str, index: int) -> Optional[dict]:
    canonical = normalize_tool_name(name)
    known = {t['name'] for t in TOOLS_SCHEMA}
    if canonical not in known:
        return None
    args = _coerce_tool_args(arguments)
    canonical, args, _ = normalize_tool_call(canonical, args)
'''
new = r'''def _build_tool_use(name: Any, arguments: Any, source: str, index: int) -> Optional[dict]:
    # Normalize with arguments BEFORE checking the canonical-name set. This is
    # required for v5 UI Skill IDs such as audio_processing and word.
    args = _coerce_tool_args(arguments)
    canonical, args, _ = normalize_tool_call(name, args)
    known = {t['name'] for t in TOOLS_SCHEMA}
    if canonical not in known:
        return None
'''
agent = replace_once(agent, old, new, 'parser normalize-before-known')

# Function-call syntax needs the same argument-aware normalization.
old = r'''        name = normalize_tool_name(node.func.id)
        if name not in known:
            continue
        args = {}
        valid = True
'''
new = r'''        raw_name = node.func.id
        args = {}
        valid = True
'''
agent = replace_once(agent, old, new, 'function syntax name precheck')
old = r'''        if valid:
            return _build_tool_use(name, args, raw, index)
'''
new = r'''        if valid:
            return _build_tool_use(raw_name, args, raw, index)
'''
agent = replace_once(agent, old, new, 'function syntax build')

# Add reasoning capture immediately after response JSON parsing and before any
# tool-call parser removes <think> blocks.
old = r'''        # Validate tool calls — small models may produce invalid JSON for tool inputs
        content = response.get('content', [])
'''
new = r'''        # Preserve local reasoning separately before tool-call normalization. It
        # is kept out of model history but returned to Flutter for the user's
        # expandable Thinking panel.
        response['_reasoning'] = _extract_reasoning_blocks(response.get('content', []))

        # Validate tool calls — small models may produce invalid JSON for tool inputs
        content = response.get('content', [])
'''
agent = replace_once(agent, old, new, 'reasoning capture')

# If a tool wrapper exists but cannot be parsed, flag it for a model retry
# instead of returning literal <tool_call> XML as normal assistant prose.
old = r'''            if tool_blocks:
                found = True
                if remaining:
                    new_content.append({"type": "text", "text": remaining})
                new_content.extend(tool_blocks)
            else:
                new_content.append(block)

        if found:
            response['content'] = new_content
            response['stop_reason'] = 'tool_use'
        return response
'''
new = r'''            if tool_blocks:
                found = True
                if remaining:
                    new_content.append({"type": "text", "text": remaining})
                new_content.extend(tool_blocks)
            elif tag_matches:
                # Recognizable tool-call wrapper, invalid payload/name. Never
                # leak it into final prose; let the ReAct loop request a retry.
                response['_tool_parse_error'] = tagged[:1500] if tag_matches else original[:1500]
                new_content.append({"type": "text", "text": remaining}) if remaining else None
            else:
                new_content.append(block)

        if found:
            response['content'] = new_content
            response['stop_reason'] = 'tool_use'
        elif response.get('_tool_parse_error'):
            response['content'] = new_content
            response['stop_reason'] = 'tool_parse_error'
        return response
'''
agent = replace_once(agent, old, new, 'tool leak prevention')

# Helper for extracting <think> content without exposing it to subsequent model
# history. Insert before LocalLLMClient.
anchor = '\n\nclass LocalLLMClient:'
helper = r'''

def _extract_reasoning_blocks(content_blocks: List[Dict[str, Any]]) -> str:
    import re
    parts = []
    for block in content_blocks or []:
        if not isinstance(block, dict) or block.get('type') != 'text':
            continue
        text = str(block.get('text', ''))
        for match in re.finditer(r'<think>([\s\S]*?)</think>', text, flags=re.IGNORECASE):
            value = match.group(1).strip()
            if value:
                parts.append(value)
        # Defensive open-tag recovery when generation ends before </think>.
        open_match = re.search(r'<think>([\s\S]*)$', text, flags=re.IGNORECASE)
        if open_match:
            value = open_match.group(1).strip()
            if value:
                parts.append(value)
    return '\n\n'.join(parts)


def _strip_reasoning_from_blocks(content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import re
    cleaned = []
    for block in content_blocks or []:
        if not isinstance(block, dict) or block.get('type') != 'text':
            cleaned.append(block)
            continue
        text = str(block.get('text', ''))
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<think>[\s\S]*$', '', text, flags=re.IGNORECASE)
        if text.strip():
            copy = dict(block)
            copy['text'] = text.strip()
            cleaned.append(copy)
    return cleaned
'''
if helper.strip() not in agent:
    agent = agent.replace(anchor, helper + anchor, 1)

# Initialize diagnostics/current attachments/reasoning at request start.
old = r'''    context = context or {}

    # Get API key (from global storage or environment)
'''
new = r'''    context = context or {}
    context['_diagnostics'] = []
    context['_current_files'] = list(files or [])
    reasoning_parts: List[str] = []
    parse_retry_count = 0

    # Get API key (from global storage or environment)
'''
agent = replace_once(agent, old, new, 'query diagnostics init')

# Add diagnostic configuration after local client is configured.
old = r'''        bridge.log(
            f"Using on-device inference; skills={len(enabled_skills)}/21, tools={len(enabled_tools)}/23",
            level="info"
        )
'''
new = r'''        bridge.log(
            f"Using on-device inference; skills={len(enabled_skills)}/21, tools={len(enabled_tools)}/23",
            level="info"
        )
        context['_diagnostics'].append({
            'stage': 'query_config',
            'enabled_skills': list(enabled_skills),
            'allowed_tools': sorted(enabled_tools),
            'thinking_mode': local_thinking_mode,
            'temperature': local_temperature,
            'top_p': local_top_p,
            'current_files': [os.path.basename(p) for p in (files or [])],
        })
'''
agent = replace_once(agent, old, new, 'query config diag')

# Capture reasoning and response shape after every local generation.
old = r'''        # Get stop reason and content
        stop_reason = response.get('stop_reason')
        content_blocks = response.get('content', [])
'''
new = r'''        # Get stop reason and content
        stop_reason = response.get('stop_reason')
        content_blocks = response.get('content', [])
        if is_offline:
            reasoning = str(response.get('_reasoning') or '').strip()
            if reasoning:
                reasoning_parts.append(reasoning)
            context['_diagnostics'].append({
                'stage': 'model_response',
                'stop_reason': stop_reason,
                'reasoning_chars': len(reasoning),
                'content_types': [b.get('type') for b in content_blocks if isinstance(b, dict)],
                'tool_parse_error': bool(response.get('_tool_parse_error')),
            })
'''
agent = replace_once(agent, old, new, 'response diagnostics')

# Add parse-error retry case before end_turn handling.
marker = r'''        # Case 1: Agent finished (end_turn)
        if stop_reason == 'end_turn':
'''
retry_case = r'''        # Local small-model recovery: a literal <tool_call> wrapper was
        # detected but its payload could not be parsed. Ask the same model to
        # repair the call instead of leaking XML into the final answer.
        if is_offline and stop_reason == 'tool_parse_error':
            parse_retry_count += 1
            raw_bad = str(response.get('_tool_parse_error') or '')[:1000]
            context['_diagnostics'].append({
                'stage': 'tool_parse_retry', 'attempt': parse_retry_count,
                'raw_preview': raw_bad,
            })
            if parse_retry_count <= 2:
                messages.append({
                    'role': 'user',
                    'content': (
                        '[Tool call format error] The previous tool call was not executable. '
                        'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
                    )
                })
                continue
            final_response = '工具调用格式连续无法解析。请复制本轮“工具调用诊断”供排查。'
            result = {'content': final_response, 'error': True}
            result['thinking'] = '\n\n'.join(reasoning_parts)
            result['thinking_mode'] = local_thinking_mode
            result['diagnostics'] = _format_diagnostics(context)
            return result

        # Case 1: Agent finished (end_turn)
        if stop_reason == 'end_turn':
'''
agent = replace_once(agent, marker, retry_case, 'parse retry case')

# Strip reasoning from final answer and return thinking/diagnostics metadata.
old = r'''            final_response = _extract_text_content(content_blocks)
            bridge.log("Preparing response...", progress=0.95)
'''
new = r'''            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks
            final_response = _extract_text_content(visible_blocks)
            bridge.log("Preparing response...", progress=0.95)
'''
agent = replace_once(agent, old, new, 'final reasoning strip')
old = r'''            result = {"content": final_response}
            if created_files:
                result["created_files"] = created_files
            return result
'''
new = r'''            result = {"content": final_response}
            if created_files:
                result["created_files"] = created_files
            if is_offline:
                result["thinking"] = "\n\n".join(reasoning_parts)
                result["thinking_mode"] = local_thinking_mode
                result["diagnostics"] = _format_diagnostics(context)
            return result
'''
agent = replace_once(agent, old, new, 'final metadata')

# Record raw/canonical tool calls and make model-format errors explicitly
# recoverable. execute_tool adds its own detailed repair/path/schema events.
old = r'''                    tool_name = block.get('name')
                    tool_input = block.get('input', {})
                    tool_id = block.get('id')
                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input)
'''
new = r'''                    tool_name = block.get('name')
                    tool_input = block.get('input', {})
                    tool_id = block.get('id')
                    raw_tool_name = tool_name
                    raw_tool_input = tool_input
                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)
                    if is_offline:
                        context['_diagnostics'].append({
                            'stage': 'tool_call',
                            'raw_name': str(raw_tool_name),
                            'raw_args': _diag_safe(raw_tool_input),
                            'canonical_name': tool_name,
                            'canonical_args': _diag_safe(tool_input),
                            'repairs': list(compat_notes),
                        })
'''
agent = replace_once(agent, old, new, 'tool call diagnostics')

# Tool error diagnostic and retry instruction for model-caused formatting errors.
old = r'''                    except ToolError as e:
                        bridge.log(f"Tool error: {e}", level="warn")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "is_error": True,
                            "content": str(e)
                        })
'''
new = r'''                    except ToolError as e:
                        bridge.log(f"Tool error: {e}", level="warn")
                        if is_offline:
                            context['_diagnostics'].append({
                                'stage': 'tool_error', 'tool': tool_name, 'error': str(e)[:2000]
                            })
                        error_content = str(e)
                        if is_offline and ('[MODEL_TOOL_ARGUMENT_ERROR]' in error_content or '[MODEL_TOOL_NAME_ERROR]' in error_content):
                            error_content += (
                                '\n[RECOVERABLE] Retry the same task immediately with one enabled canonical tool and corrected exact arguments. '
                                'Choose a safe output filename yourself when possible; only ask the user if a required INPUT file or genuinely ambiguous destructive choice is missing.'
                            )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "is_error": True,
                            "content": error_content
                        })
'''
agent = replace_once(agent, old, new, 'tool error retry')

# Helpers for user-copyable diagnostics. Insert before process_query.
anchor = '\ndef process_query(\n'
diag = r'''

def _diag_safe(value: Any) -> Any:
    secret_words = {'api_key', 'access_token', 'google_access_token', 'authorization', 'token', 'password'}
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            key_s = str(key)
            result[key_s] = '[REDACTED]' if key_s.lower() in secret_words or key_s == '_context' else _diag_safe(item)
        return result
    if isinstance(value, list):
        return [_diag_safe(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + '...[truncated]'
    return value


def _format_diagnostics(context: Dict[str, Any]) -> str:
    events = context.get('_diagnostics', []) if isinstance(context, dict) else []
    safe = _diag_safe(events)
    try:
        return json.dumps(safe, ensure_ascii=False, indent=2)
    except Exception:
        return str(safe)
'''
if diag.strip() not in agent:
    agent = agent.replace(anchor, diag + anchor, 1)

agent_path.write_text(agent, encoding='utf-8')

print('Applied RastaCoder v6 tool reliability core patch')

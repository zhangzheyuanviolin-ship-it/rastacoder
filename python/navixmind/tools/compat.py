"""Tool-call compatibility helpers for local/small LLMs.

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
    for key in ("param", "request", "instruction", "command", "query"):
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
        modifying = keys & {"operations", "operation", "action"} or _contains_any(
            free, ("modify", "edit", "replace", "append", "update", "修改", "替换", "编辑", "追加", "更新")
        )
        creating = keys & {"content", "text", "body"} or _contains_any(
            free, ("create", "write", "make", "new document", "创建", "新建", "写入", "生成")
        )
        reading = keys & {"docx_path", "extract"} or _contains_any(
            free, ("read", "extract", "inspect", "open", "view", "summarize", "读取", "提取", "查看", "打开", "总结")
        ) or (".docx" in free and not creating)
        if modifying:
            routed = "modify_docx"
        elif reading:
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
    for m in re.finditer(r"""["']([^"']+\.[A-Za-z0-9]{1,6})["']""", text):
        results.append(m.group(1).strip())
    # Common unquoted Android/model basenames.
    for m in re.finditer(r"""(?<![\w])([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]{1,6})(?![\w])""", text):
        value = m.group(1).strip().rstrip(".,;:)")
        if value not in results:
            results.append(value)
    return results


def _extract_url(text: str) -> Optional[str]:
    m = re.search(r"""https?://[^\s<>"']+""", text)
    return m.group(0).rstrip(".,;)") if m else None


def _target_format(text: str) -> Optional[str]:
    patterns = (
        r"""\b(?:to|into|as)\s+\.?([A-Za-z0-9]{2,5})\b""",
        r"""(?:转成|转换成|转为|转换为)\s*\.?([A-Za-z0-9]{2,5})\b""",
    )
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).lower().lstrip(".")
    return None



def _explicit_destination(text: str, extensions: set[str]) -> Optional[str]:
    """Return an explicitly requested output filename/path from free-form text."""
    candidates = _extract_file_tokens(text)
    transitions = (
        "to", "into", "as", "save as", "saved as", "output to", "write to",
        "保存为", "输出为", "生成到", "生成为", "写入到",
    )
    for candidate in reversed(candidates):
        if _extension(candidate) not in extensions:
            continue
        escaped = re.escape(candidate)
        for transition in transitions:
            if re.search(re.escape(transition) + r"\s*[\"']?" + escaped, text, flags=re.IGNORECASE):
                return candidate
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



def _creation_content_from_freeform(text: str, files: List[str]) -> str:
    """Extract requested document text from common one-line small-model calls."""
    value = text.strip()
    if not value:
        return ""
    patterns = (
        r"""(?:content|text|body)\s*[:=]\s*[\"']?([\s\S]+?)[\"']?$""",
        r"""(?:saying|containing|with\s+content)\s+[\"']?([\s\S]+?)[\"']?$""",
        r"""\bwrite\s+[\"']?([\s\S]+?)[\"']?\s+(?:to|into)\s+[\"']?[^\"']+\.[A-Za-z0-9]{1,6}[\"']?\s*$""",
        r"""(?:内容为|内容是|写入内容|正文为|正文是)\s*[：:]?\s*[“”\"']?([\s\S]+?)[“”\"']?\s*$""",
    )
    for pattern in patterns:
        m = re.search(pattern, value, flags=re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip().strip("\"'“”")

    # Conservative fallback: remove an obvious leading creation verb and an
    # obvious trailing destination filename. This is used only for creation
    # tools, so it cannot overwrite/read an input file.
    cleaned = re.sub(
        r"""^(?:please\s+)?(?:write|create|save|make)\s+(?:a\s+)?(?:txt|text|word|docx|pdf)?\s*(?:file|document)?\s*[:：-]?\s*""",
        '', value, flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"""\s+(?:to|into|as)\s+[\"']?[^\"']+\.[A-Za-z0-9]{1,6}[\"']?\s*$""",
        '', cleaned, flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"""^(?:写入|创建|新建|保存)(?:一个|一份)?(?:TXT|txt|文本|Word|word|DOCX|docx|PDF|pdf)?(?:文件|文档)?\s*[：:]?\s*""",
        '', cleaned,
    ).strip()
    for file_name in files:
        if cleaned == file_name:
            return ""
    return cleaned.strip("\"'“”")

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

    if name == "create_zip" and files:
        destination = _explicit_destination(free, {"zip"})
        if destination is None:
            zip_candidates = [f for f in files if _extension(f) == "zip"]
            non_zip = [f for f in files if _extension(f) != "zip"]
            if len(zip_candidates) == 1 and non_zip and _contains_any(
                free, ("zip", "archive", "compress", "打包", "压缩", "创建")
            ):
                destination = zip_candidates[0]
        if destination and "output_path" not in args:
            args["output_path"] = destination
            notes.append("freeform->output_path")
        if "file_paths" not in args:
            sources = [f for f in files if f != destination]
            if sources:
                args["file_paths"] = sources
                notes.append("freeform->file_paths")

    if name in {"web_fetch", "headless_browser", "download_media"} and url and "url" not in args:
        args["url"] = url
        notes.append("freeform->url")

    if name == "python_execute" and "code" not in args:
        args["code"] = free
        notes.append("param->code")

    # Creation tools may receive the whole user intent inside one generic
    # `param`. Recover output filenames and requested body text deterministically.
    if name in {"write_file", "create_docx", "create_pdf"}:
        desired_ext = {"write_file": "txt", "create_docx": "docx", "create_pdf": "pdf"}[name]
        matching = [f for f in files if _extension(f) == desired_ext]
        if matching and "output_path" not in args:
            args["output_path"] = matching[-1]
            notes.append("freeform->output_path")
        if "content" not in args:
            recovered = _creation_content_from_freeform(free, files)
            if recovered:
                args["content"] = recovered
                notes.append("freeform->content")

    if name == "convert_document":
        destination = _explicit_destination(free, {"txt", "docx", "pdf", "html", "htm"})
        if destination:
            if "output_path" not in args:
                args["output_path"] = destination
                notes.append("freeform->output_path")
            destination_format = _extension(destination)
            if destination_format == "htm":
                destination_format = "html"
            if "output_format" not in args:
                args["output_format"] = destination_format
                notes.append("destination->output_format")
            if args.get("input_path") == destination:
                alternatives = [f for f in files if f != destination]
                if alternatives:
                    args["input_path"] = alternatives[0]
                    notes.append("destination_removed_from_input")
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
        args["output_path"] = args["input_path"]
        notes.append("default:output_path=in_place")

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


# RASTACODER_V11_ARGUMENT_KEY_SANITIZER
def _sanitize_argument_keys(args: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:
    """Repair punctuation copied from human-readable optional-argument hints.

    Small local models sometimes emit keys such as ``path?`` or ``recursive?``.
    Canonical keys always win if both spellings are present. Conflicting aliases
    are dropped instead of silently overwriting an explicit canonical value.
    """
    cleaned: Dict[str, Any] = {}
    origins: Dict[str, str] = {}
    for raw_key, value in args.items():
        original = str(raw_key)
        key = original.strip()
        key = re.sub(r'[\s?？:：]+$', '', key)
        if not key:
            notes.append(f'dropped_empty_key:{original!r}')
            continue
        if key != original:
            notes.append(f'arg_key:{original}->{key}')
        if key in cleaned:
            previous = origins.get(key, key)
            if original == key and previous != key:
                cleaned[key] = value
                origins[key] = original
                notes.append(f'arg_key_collision:canonical_wins:{key}')
            elif cleaned[key] != value:
                notes.append(f'arg_key_collision:dropped:{original}->{key}')
            continue
        cleaned[key] = value
        origins[key] = original
    return cleaned


# RASTACODER_V13_SCHEMA_AWARE_COERCION
_ENUM_CONTRACTS = {
    "read_docx": {"extract": ({"text", "tables", "all"}, "all")},
    "read_pptx": {"extract": ({"text", "slides", "notes", "all"}, "all")},
    "read_xlsx": {"extract": ({"values", "formulas", "all"}, "values")},
    "web_fetch": {"extract_mode": ({"text", "html", "links"}, "text")},
    "create_zip": {"compression": ({"deflated", "stored"}, "deflated")},
    "download_media": {"format": ({"video", "audio"}, "video")},
}

_STRING_SCALAR_ARGS = {
    "read_pdf": {"pages"},
    "read_xlsx": {"sheet", "range"},
}


def _coerce_contract_values(name: str, args: Dict[str, Any], notes: List[str]) -> None:
    # Repair only unambiguous primitive/schema mismatches.
    for key, contract in _ENUM_CONTRACTS.get(name, {}).items():
        allowed, default = contract
        if key not in args:
            continue
        value = args.get(key)
        if value is None or value == "":
            args.pop(key, None)
            notes.append(f"{key}:empty->default:{default}")
            continue
        if isinstance(value, bool):
            args[key] = default
            notes.append(f"{key}:bool->{default}")
            continue
        raw = str(value).strip()
        lowered = raw.lower().replace("-", "_").replace(" ", "_")
        if lowered in {"true", "false", "yes", "no", "on", "off", "1", "0"}:
            args[key] = default
            notes.append(f"{key}:bool_string->{default}")
            continue
        if lowered in allowed:
            if lowered != value:
                notes.append(f"{key}:{value}->{lowered}")
            args[key] = lowered

    for key in _STRING_SCALAR_ARGS.get(name, set()):
        if key not in args:
            continue
        value = args.get(key)
        if value is None or value == "":
            args.pop(key, None)
            notes.append(f"{key}:empty->executor_default")
        elif isinstance(value, bool):
            args.pop(key, None)
            notes.append(f"{key}:bool->executor_default")
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                value = int(value)
            args[key] = str(value)
            notes.append(f"{key}:scalar->string")


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

    args = _sanitize_argument_keys(args, notes)

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

    if name in {"web_fetch", "headless_browser", "download_media"}:
        _move_alias(args, "url", ["link", "uri", "website", "address"], notes)

    if name in {"ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file", "create_zip", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "output_path", ["output", "destination", "dest", "target", "target_path", "output_file", "filename_out"], notes)

    if name in {"write_file", "create_docx", "create_pdf"}:
        _move_alias(args, "output_path", ["filename", "file_name", "path", "file"], notes)
    if name == "create_zip":
        _move_alias(args, "output_path", ["filename", "file_name", "archive", "archive_path"], notes)

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
        _move_alias(args, "format", ["target_format", "output_format", "to_format"], notes)
        if "operation" in args:
            raw = str(args["operation"]).strip().lower().replace("-", "_").replace(" ", "_")
            aliases = {
                "cut": "trim", "clip": "trim", "crop_video": "crop",
                "scale": "resize", "rescale": "resize",
                "effects": "filter", "effect": "filter",
                "audio": "extract_audio", "extractaudio": "extract_audio", "extract_sound": "extract_audio",
                "frame": "extract_frame", "screenshot": "extract_frame",
                "transcode": "convert", "conversion": "convert",
                "convert_audio": "extract_audio", "audio_convert": "extract_audio", "audio_conversion": "extract_audio",
                "speed": "speed", "tempo": "speed", "playback_speed": "speed",
                "speed_up": "speed", "speedup": "speed", "accelerate": "speed",
                "slow_down": "speed", "slowdown": "speed",
            }
            normalized = aliases.get(raw, raw)
            if normalized != raw:
                notes.append(f"operation:{raw}->{normalized}")
            args["operation"] = normalized

        raw_params = args.get("params")
        params = dict(raw_params) if isinstance(raw_params, dict) else {}
        if args.get("operation") == "speed" and not isinstance(raw_params, dict) and raw_params not in (None, ""):
            try:
                params["factor"] = float(str(raw_params).strip())
                notes.append("params:scalar->params.factor")
            except (TypeError, ValueError):
                pass
        for key in ("start", "end", "duration", "width", "height", "x", "y", "vf", "af", "video_filter", "audio_filter", "format", "bitrate", "timestamp", "codec", "quality", "args", "factor", "speed", "rate"):
            if key in args and key not in params:
                params[key] = args.pop(key)
                notes.append(f"top-level:{key}->params.{key}")
        if args.get("operation") == "speed" and "factor" not in params:
            for alias in ("speed", "rate"):
                if alias in params:
                    params["factor"] = params.pop(alias)
                    notes.append(f"params.{alias}->params.factor")
                    break
        if args.get("operation") == "speed" and "factor" in params:
            try:
                params["factor"] = float(params["factor"])
            except (TypeError, ValueError):
                pass
        if "codec" in params:
            codec_raw = str(params["codec"]).lower().strip()
            codec = {"h264": "libx264", "avc": "libx264", "h265": "libx265", "hevc": "libx265"}.get(codec_raw, codec_raw)
            if codec != codec_raw:
                notes.append(f"codec:{codec_raw}->{codec}")
            params["codec"] = codec
        if params or "params" in args:
            args["params"] = params

    if name == "smart_crop":
        _move_alias(args, "aspect_ratio", ["ratio", "target_ratio", "aspect"], notes)

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
        if "operations" not in args and isinstance(args.get("action"), str):
            action = str(args.pop("action")).strip().lower().replace("-", "_").replace(" ", "_")
            aliases = {
                "modify_docx": {
                    "replace": "replace_text", "append": "add_paragraph", "append_paragraph": "add_paragraph",
                    "table_cell": "update_table_cell", "set_table_cell": "update_table_cell",
                },
                "modify_pptx": {
                    "new_slide": "add_slide", "append_slide": "add_slide", "notes": "set_notes",
                    "set_note": "set_notes", "set_text": "update_slide_text",
                },
                "modify_xlsx": {
                    "update_cell": "set_cell", "write_cell": "set_cell", "formula": "set_formula",
                    "append_row": "add_row", "new_sheet": "add_sheet", "remove_sheet": "delete_sheet",
                },
            }
            action = aliases[name].get(action, action)
            params = args.pop("params", {}) if isinstance(args.get("params"), dict) else {}
            protected = {"input_path", "output_path", "operations"}
            for key in list(args.keys()):
                if key not in protected:
                    params[key] = args.pop(key)
            args["operations"] = [{"action": action, "params": params}]
            notes.append("action->operations")
        if isinstance(args.get("operations"), list):
            action_aliases = {
                "modify_docx": {"replace": "replace_text", "append": "add_paragraph", "append_paragraph": "add_paragraph"},
                "modify_pptx": {"new_slide": "add_slide", "append_slide": "add_slide", "notes": "set_notes", "set_text": "update_slide_text"},
                "modify_xlsx": {"update_cell": "set_cell", "write_cell": "set_cell", "formula": "set_formula", "append_row": "add_row", "new_sheet": "add_sheet", "remove_sheet": "delete_sheet"},
            }[name]
            normalized_operations = []
            for item in args["operations"]:
                if isinstance(item, dict):
                    item = dict(item)
                    raw_action = str(item.get("action", "")).strip().lower().replace("-", "_").replace(" ", "_")
                    if raw_action:
                        mapped = action_aliases.get(raw_action, raw_action)
                        if mapped != raw_action:
                            notes.append(f"operation_action:{raw_action}->{mapped}")
                        item["action"] = mapped
                normalized_operations.append(item)
            args["operations"] = normalized_operations

    if name == "google_calendar":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "date_range", ["date", "range", "time_range"], notes)
        _move_alias(args, "event_id", ["id", "calendar_event_id"], notes)
        if str(args.get("action", "")).lower() in {"create", "add", "new", "create_event"} and not isinstance(args.get("event"), dict):
            event = {}
            for key in ("title", "start", "end", "description", "location"):
                if key in args:
                    event[key] = args.pop(key)
            if event:
                args["event"] = event
                notes.append("top-level-event->event")
        if "action" in args:
            action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {"get": "list", "show": "list", "list_events": "list", "add": "create", "new": "create", "create_event": "create", "remove": "delete", "delete_event": "delete"}.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    # RASTACODER_V11_WORKSPACE_LIST_COMPAT
    if name == "list_files":
        _move_alias(args, "path", ["folder", "folder_path", "dir", "directory_path"], notes)
        directory = args.get("directory")
        path_value = args.get("path")

        # A frequent Qwen small-model failure is interpreting optionality as a
        # boolean. Treat that as omitted/default rather than rejecting the call.
        if isinstance(directory, bool) or (isinstance(directory, str) and directory.strip().lower() in {"true", "false"}):
            args.pop("directory", None)
            directory = None
            notes.append("list_files:removed_boolean_directory")
        if isinstance(path_value, bool):
            args.pop("path", None)
            path_value = None
            notes.append("list_files:removed_boolean_path")

        roots = {"output", "downloads", "documents", "pictures", "screenshots", "camera"}
        directory_key = str(directory or "").strip().lower()
        path_text = str(args.get("path") or "").strip().replace("\\", "/")
        # RASTACODER_V12_VIRTUAL_WORKSPACE_ALIASES
        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}

        if directory_key in roots:
            if directory_key == "output":
                if path_text.lower() in workspace_aliases:
                    args["path"] = "."
                elif path_text.lower().startswith("output/"):
                    args["path"] = path_text[7:] or "."
            else:
                if path_text.lower() in workspace_aliases:
                    args["path"] = directory_key
                elif path_text and not os.path.isabs(path_text) and not any(
                    path_text.lower() == root or path_text.lower().startswith(root + "/") for root in roots
                ):
                    args["path"] = f"{directory_key}/{path_text.lstrip('./')}"
                elif not path_text:
                    args["path"] = directory_key
            args.pop("directory", None)
            notes.append(f"list_files:directory->{args.get('path', '.')}")
        elif "directory" in args:
            # Unknown legacy directory strings are treated as a path only when
            # no explicit path exists. This keeps the canonical model interface
            # to one path concept.
            if not path_text and isinstance(directory, str) and directory.strip():
                args["path"] = directory.strip()
                notes.append("list_files:legacy_directory->path")
            args.pop("directory", None)

        path_text = str(args.get("path") or ".").strip().replace("\\", "/")
        path_lower = path_text.lower()
        if path_lower in workspace_aliases:
            if path_text != ".":
                notes.append(f"list_files:virtual_workspace_alias:{path_text}->.")
            args["path"] = "."
        elif path_lower.startswith("/output/"):
            args["path"] = path_text[len("/output/"):] or "."
            notes.append(f"list_files:virtual_workspace_prefix:{path_text}->{args['path']}")
        elif path_lower.startswith("/workspace/"):
            args["path"] = path_text[len("/workspace/"):] or "."
            notes.append(f"list_files:virtual_workspace_prefix:{path_text}->{args['path']}")
        elif path_lower.startswith("output/"):
            args["path"] = path_text[7:] or "."
        elif path_lower.startswith("workspace/"):
            args["path"] = path_text[10:] or "."
        else:
            # Small models also invent leading slashes for documented logical
            # Android roots. Canonicalize those without accepting arbitrary OS roots.
            for _root in ("downloads", "documents", "pictures", "screenshots", "camera"):
                if path_lower == f"/{_root}":
                    args["path"] = _root
                    notes.append(f"list_files:logical_root:{path_text}->{_root}")
                    break
                if path_lower.startswith(f"/{_root}/"):
                    args["path"] = _root + "/" + path_text[len(_root) + 2:]
                    notes.append(f"list_files:logical_root:{path_text}->{args['path']}")
                    break

        for bool_key in ("recursive", "include_directories"):
            if isinstance(args.get(bool_key), str):
                lowered = args[bool_key].strip().lower()
                if lowered in {"true", "1", "yes", "on"}:
                    args[bool_key] = True
                    notes.append(f"{bool_key}:string->true")
                elif lowered in {"false", "0", "no", "off"}:
                    args[bool_key] = False
                    notes.append(f"{bool_key}:string->false")
        if args.get("pattern") in ("", None):
            args.pop("pattern", None)

    if name == "download_media" and "format" in args:
        raw_format = str(args["format"]).strip().lower().replace("-", "_").replace(" ", "_")
        mapped_format = {
            "mp3": "audio", "wav": "audio", "m4a": "audio", "aac": "audio", "flac": "audio",
            "audio_only": "audio", "music": "audio", "mp4": "video", "video_only": "video",
        }.get(raw_format, raw_format)
        if mapped_format != raw_format:
            notes.append(f"format:{raw_format}->{mapped_format}")
        args["format"] = mapped_format

    if name == "gmail":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "message_id", ["id", "email_id", "mail_id"], notes)
        if "action" in args:
            action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {"get": "read", "open": "read", "read_message": "read", "search": "list", "find": "list", "list_messages": "list"}.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    # Search functions expose only user intent to the model. Provider knobs are
    # merged later from user settings. Repair common 4B aliases before stripping noise.
    search_tools = {"anysearch_search", "exa_search", "langsearch_search", "tavily_search"}
    if name in search_tools:
        if not isinstance(args.get("query"), str) or not args.get("query", "").strip():
            for alias in ("q", "keyword", "keywords", "search_query", "text"):
                value = args.get(alias)
                if isinstance(value, str) and value.strip():
                    args["query"] = value.strip()
                    notes.append(f"{alias}->query")
                    break
        if not isinstance(args.get("query"), str) or not args.get("query", "").strip():
            topic_value = args.get("topic")
            if isinstance(topic_value, str) and topic_value.strip():
                args["query"] = topic_value.strip()
                notes.append("topic->query")
        if not isinstance(args.get("query"), str) or not args.get("query", "").strip():
            free_value = _freeform(args)
            if free_value:
                args["query"] = free_value
                notes.append("freeform->query")
        for key in list(args.keys()):
            if key != "query":
                args.pop(key, None)
                notes.append(f"search_setting_removed:{key}")

    # Apply schema-aware primitive/enum coercion after tool-specific alias
    # routing but before strict executor validation.
    _coerce_contract_values(name, args, notes)

    # Generic free-form keys are compatibility scaffolding, never canonical
    # tool arguments. Remove them after extracting deterministic information.
    for key in ("param", "request", "instruction", "command", "query"):
        if key == "query" and name in ({"gmail"} | search_tools):
            continue
        if key in args:
            args.pop(key, None)
            notes.append(f"removed:{key}")

    _repair_with_context(name, args, context, notes)
    return name, args, notes

"""Tool-call compatibility helpers for local/small LLMs.

Canonical tool schemas stay strict. This layer accepts common surface variants
from small models and normalizes them before dispatch. Corrections are returned
as notes so the UI can distinguish model-format recovery from runtime failures.
"""
from typing import Any, Dict, List, Tuple


TOOL_ALIASES = {
    "python": "python_execute",
    "run_python": "python_execute",
    "python_exec": "python_execute",
    "ffmpeg": "ffmpeg_process",
    "video_edit": "ffmpeg_process",
    "audio_edit": "ffmpeg_process",
    "ocr": "ocr_image",
    "image_ocr": "ocr_image",
    "browser": "headless_browser",
    "browse": "headless_browser",
    "convert_file": "convert_document",
    "document_convert": "convert_document",
    "doc_convert": "convert_document",
    "create_word": "create_docx",
    "create_word_document": "create_docx",
    "write_docx": "create_docx",
    "calendar": "google_calendar",
    "google_calendar_tool": "google_calendar",
    "email": "gmail",
    "google_mail": "gmail",
    "zip": "create_zip",
}


def normalize_tool_name(name: Any) -> str:
    value = str(name or "").strip().lower().replace("-", "_").replace(" ", "_")
    if value.endswith("()"):
        value = value[:-2]
    return TOOL_ALIASES.get(value, value)


def _move_alias(args: Dict[str, Any], target: str, aliases: List[str], notes: List[str]) -> None:
    if target in args and args[target] not in (None, ""):
        return
    for alias in aliases:
        if alias in args and args[alias] not in (None, ""):
            args[target] = args.pop(alias)
            notes.append(f"{alias}->{target}")
            return


def normalize_tool_call(tool_name: Any, raw_args: Any) -> Tuple[str, Dict[str, Any], List[str]]:
    notes: List[str] = []
    original_name = str(tool_name or "")
    name = normalize_tool_name(original_name)
    if name != original_name.strip():
        notes.append(f"tool:{original_name}->{name}")

    args = dict(raw_args) if isinstance(raw_args, dict) else {}

    # Some small models wrap arguments one level too deeply.
    for wrapper in ("arguments", "args", "parameters", "input"):
        nested = args.get(wrapper)
        if isinstance(nested, dict) and len(args) == 1:
            args = dict(nested)
            notes.append(f"unwrapped:{wrapper}")
            break

    read_path_key = {
        "read_pdf": "pdf_path",
        "read_docx": "docx_path",
        "read_pptx": "pptx_path",
        "read_xlsx": "xlsx_path",
        "ocr_image": "image_path",
        "read_file": "file_path",
        "file_info": "file_path",
    }.get(name)
    if read_path_key:
        _move_alias(
            args,
            read_path_key,
            ["file", "path", "source", "source_path", "input", "input_file", "filename"],
            notes,
        )

    if name in {
        "ffmpeg_process", "smart_crop", "convert_document",
        "modify_docx", "modify_pptx", "modify_xlsx",
    }:
        _move_alias(
            args,
            "input_path",
            ["file", "path", "source", "source_path", "input", "input_file"],
            notes,
        )

    if name in {
        "ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file",
        "create_zip", "modify_docx", "modify_pptx", "modify_xlsx",
    }:
        _move_alias(
            args,
            "output_path",
            ["output", "destination", "dest", "target", "target_path", "output_file"],
            notes,
        )

    if name == "convert_document":
        _move_alias(args, "output_format", ["format", "target_format", "to", "to_format"], notes)
        _move_alias(args, "output_path", ["output", "destination", "dest", "target_path"], notes)
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
        _move_alias(args, "content", ["text", "body", "document_text"], notes)

    if name == "create_pdf":
        _move_alias(args, "content", ["text", "body", "document_text"], notes)
        if "image_path" in args and "image_paths" not in args:
            args["image_paths"] = [args.pop("image_path")]
            notes.append("image_path->image_paths")
        if isinstance(args.get("image_paths"), str):
            args["image_paths"] = [args["image_paths"]]
            notes.append("image_paths:string->list")

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
                "audio": "extract_audio", "extractaudio": "extract_audio",
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
        for key in (
            "start", "end", "duration", "width", "height", "x", "y", "vf", "af",
            "video_filter", "audio_filter", "format", "bitrate", "timestamp",
            "codec", "quality", "args",
        ):
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
            mapped = {
                "get": "list", "show": "list", "list_events": "list",
                "add": "create", "new": "create", "create_event": "create",
                "remove": "delete", "delete_event": "delete",
            }.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    if name == "gmail":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "message_id", ["id", "email_id", "mail_id"], notes)
        if "action" in args:
            action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {
                "get": "read", "open": "read", "read_message": "read",
                "search": "list", "find": "list", "list_messages": "list",
            }.get(action, action)
            if mapped != action:
                notes.append(f"action:{action}->{mapped}")
            args["action"] = mapped

    return name, args, notes

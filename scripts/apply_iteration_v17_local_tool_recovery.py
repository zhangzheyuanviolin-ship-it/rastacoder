#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / 'python/navixmind/tools/compat.py'
TOOLS = ROOT / 'python/navixmind/tools/__init__.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one source block, found {count}')
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Small-model compatibility ABI: repair the exact phone failure and broaden
# deterministic aliases/defaults across the remaining local file tools.
# ---------------------------------------------------------------------------
text = COMPAT.read_text(encoding='utf-8')

old = '''        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}'''
new = '''        # RASTACODER_V17_LOCAL_ROOT_ALIAS_RECOVERY
        # Qwen3-4B may express the logical workspace root as '/'. Repair it at
        # the model ABI boundary so diagnostics and downstream tools see '.'.
        # The central path contract independently carries the same invariant.
        workspace_aliases = {"", ".", "./", "/", "output", "output/", "workspace", "workspace/", "/output", "/output/", "/workspace", "/workspace/"}'''
text = replace_once(text, old, new, 'workspace root alias')

old = '''    if name in {"web_fetch", "headless_browser", "download_media"}:
        _move_alias(args, "url", ["link", "uri", "website", "address"], notes)'''
new = '''    if name in {"web_fetch", "headless_browser", "download_media", "anysearch_extract"}:
        _move_alias(args, "url", ["link", "uri", "website", "address"], notes)'''
text = replace_once(text, old, new, 'URL alias coverage')

old = '''    if name in {"ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file", "create_zip", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "output_path", ["output", "destination", "dest", "target", "target_path", "output_file", "filename_out"], notes)'''
new = '''    # RASTACODER_V17_ALL_LOCAL_OUTPUT_ALIASES
    if name in {
        "ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file",
        "create_zip", "modify_docx", "modify_pptx", "modify_xlsx", "create_pptx",
        "create_xlsx", "image_compose", "pdf_manage", "convert_document", "download_media",
    }:
        _move_alias(args, "output_path", ["output", "destination", "dest", "target", "target_path", "output_file", "filename_out"], notes)'''
text = replace_once(text, old, new, 'output alias coverage')

anchor = '''    if name == "create_zip":
        _move_alias(args, "file_paths", ["files", "inputs", "paths"], notes)
        if isinstance(args.get("file_paths"), str):
            args["file_paths"] = [args["file_paths"]]
            notes.append("file_paths:string->list")
'''
addition = anchor + '''
    # RASTACODER_V17_STRUCTURED_TOOL_ABI_RECOVERY
    # These v7 tools previously had strict schemas but almost no 3B-4B surface
    # repair. Normalize only deterministic aliases/container shapes.
    if name == "file_manage":
        _move_alias(args, "action", ["operation", "op", "task"], notes)
        _move_alias(args, "source_path", ["source", "src", "from_path"], notes)
        _move_alias(args, "destination_path", ["destination", "dest", "dst", "to_path", "target_path"], notes)
        if "action" in args:
            raw_action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {
                "ls": "list", "list_files": "list", "make_dir": "mkdir", "create_dir": "mkdir",
                "create_directory": "mkdir", "cp": "copy", "mv": "move", "rm": "delete",
                "remove": "delete", "stat": "exists", "check": "exists",
            }.get(raw_action, raw_action)
            if mapped != raw_action:
                notes.append(f"action:{raw_action}->{mapped}")
            args["action"] = mapped
        if args.get("action") == "list" and not args.get("path"):
            args["path"] = "."
            notes.append("default:path=.")

    if name in {"list_zip", "extract_zip"}:
        _move_alias(args, "zip_path", ["file", "path", "archive", "archive_path", "input", "input_path"], notes)
    if name == "extract_zip":
        _move_alias(args, "output_dir", ["folder", "directory", "destination_dir", "extract_to"], notes)

    if name == "pdf_manage":
        _move_alias(args, "action", ["operation", "op", "task"], notes)
        _move_alias(args, "input_path", ["file", "path", "source", "source_path", "input"], notes)
        _move_alias(args, "input_paths", ["files", "paths", "sources"], notes)
        if isinstance(args.get("input_paths"), str):
            args["input_paths"] = [args["input_paths"]]
            notes.append("input_paths:string->list")
        if "action" in args:
            raw_action = str(args["action"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {
                "extract": "extract_pages", "extract_page": "extract_pages",
                "delete": "delete_pages", "remove_pages": "delete_pages",
                "rotate_pages": "rotate", "reorder_pages": "reorder",
                "combine": "merge", "merge_pdfs": "merge",
            }.get(raw_action, raw_action)
            if mapped != raw_action:
                notes.append(f"action:{raw_action}->{mapped}")
            args["action"] = mapped

    if name == "create_pptx":
        _move_alias(args, "slides", ["pages", "items"], notes)
        if isinstance(args.get("slides"), dict):
            args["slides"] = [args["slides"]]
            notes.append("slides:object->list")

    if name == "create_xlsx":
        _move_alias(args, "sheets", ["worksheets", "tabs"], notes)
        if isinstance(args.get("sheets"), dict):
            args["sheets"] = [args["sheets"]]
            notes.append("sheets:object->list")

    if name == "image_compose":
        _move_alias(args, "input_paths", ["images", "files", "paths"], notes)
        if "image_path" in args and "input_paths" not in args:
            args["input_paths"] = [args.pop("image_path")]
            notes.append("image_path->input_paths")
        if "input_path" in args and "input_paths" not in args:
            args["input_paths"] = [args.pop("input_path")]
            notes.append("input_path->input_paths")
        if isinstance(args.get("input_paths"), str):
            args["input_paths"] = [args["input_paths"]]
            notes.append("input_paths:string->list")
        _move_alias(args, "operation", ["action", "op", "task"], notes)
        if "operation" in args:
            raw_op = str(args["operation"]).strip().lower().replace("-", "_").replace(" ", "_")
            mapped = {
                "horizontal": "concat_horizontal", "concat_h": "concat_horizontal",
                "vertical": "concat_vertical", "concat_v": "concat_vertical",
                "greyscale": "grayscale", "gray": "grayscale", "rotate_image": "rotate",
                "convert_format": "convert", "format_convert": "convert",
            }.get(raw_op, raw_op)
            if mapped != raw_op:
                notes.append(f"operation:{raw_op}->{mapped}")
            args["operation"] = mapped

    if name == "anysearch_get_sub_domains":
        if isinstance(args.get("domains"), str) and not args.get("domain"):
            args["domain"] = args.pop("domains")
            notes.append("domains:string->domain")
        _move_alias(args, "domain", ["host", "hostname", "site"], notes)
'''
if 'RASTACODER_V17_STRUCTURED_TOOL_ABI_RECOVERY' not in text:
    if text.count(anchor) != 1:
        raise SystemExit(f'structured ABI anchor count={text.count(anchor)}')
    text = text.replace(anchor, addition, 1)

old = '''    if name == "create_docx" and not args.get("output_path") and args.get("content") is not None:
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
        notes.append("default:output_path=archive.zip")'''
new = '''    # RASTACODER_V17_DETERMINISTIC_OUTPUT_DEFAULTS
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
    elif name == "create_pptx" and not args.get("output_path"):
        args["output_path"] = "presentation.pptx"
        notes.append("default:output_path=presentation.pptx")
    elif name == "create_xlsx" and not args.get("output_path"):
        args["output_path"] = "spreadsheet.xlsx"
        notes.append("default:output_path=spreadsheet.xlsx")
    elif name == "convert_document" and not args.get("output_path") and isinstance(args.get("input_path"), str) and args.get("output_format"):
        stem = os.path.splitext(os.path.basename(args["input_path"]))[0] or "document"
        fmt = str(args["output_format"]).strip().lower().lstrip(".") or "txt"
        args["output_path"] = f"{stem}_converted.{fmt}"
        notes.append("derived:output_path=workspace_converted")
    elif name == "image_compose" and not args.get("output_path") and isinstance(args.get("input_paths"), list) and args.get("input_paths") and args.get("operation"):
        first = str(args["input_paths"][0])
        params = args.get("params") if isinstance(args.get("params"), dict) else {}
        requested = str(params.get("format") or "").strip().lower().lstrip(".")
        ext = requested or _extension(first) or "png"
        args["output_path"] = _derive_output(first, str(args["operation"]), ext)
        notes.append("derived:output_path")'''
text = replace_once(text, old, new, 'deterministic output defaults')

# If a small model supplies only '/' as an output destination, treat that as an
# omitted filename and let the deterministic defaults above select a file.
marker = '''    _repair_with_context(name, args, context, notes)
    return name, args, notes'''
replacement = '''    # RASTACODER_V17_OUTPUT_ROOT_IS_NOT_A_FILENAME
    if isinstance(args.get("output_path"), str) and args["output_path"].strip().replace("\\\\", "/") in {"/", ".", "./", "/workspace", "/output"}:
        args.pop("output_path", None)
        notes.append("output_path:workspace_root->default_filename")
    _repair_with_context(name, args, context, notes)
    # _repair_with_context may synthesize output names, so a root-only value is
    # removed before it runs; callers never attempt to open the workspace dir as a file.
    return name, args, notes'''
text = replace_once(text, marker, replacement, 'root-only output handling')

for required in [
    'RASTACODER_V17_LOCAL_ROOT_ALIAS_RECOVERY',
    'RASTACODER_V17_ALL_LOCAL_OUTPUT_ALIASES',
    'RASTACODER_V17_STRUCTURED_TOOL_ABI_RECOVERY',
    'RASTACODER_V17_DETERMINISTIC_OUTPUT_DEFAULTS',
    'RASTACODER_V17_OUTPUT_ROOT_IS_NOT_A_FILENAME',
    'workspace_aliases = {"", ".", "./", "/",',
]:
    if required not in text:
        raise SystemExit(f'Missing V17 compatibility invariant: {required}')
COMPAT.write_text(text, encoding='utf-8')


# ---------------------------------------------------------------------------
# 2) Shared executor path boundary. destination_path and extract_zip output_dir
# were previously outside the central resolver even though 4B models can emit
# the same leading-slash notation for them.
# ---------------------------------------------------------------------------
tools = TOOLS.read_text(encoding='utf-8')
old = '''    path_keys = [
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    ]'''
new = '''    # RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY
    path_keys = [
        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',
        'destination_path', 'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',
    ]'''
tools = replace_once(tools, old, new, 'shared scalar path keys')

old = '''def _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:
    """Resolve generated outputs through the same virtual-workspace contract."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    value = args.get('output_path')
    if isinstance(value, str):
        args['output_path'] = resolve_output_path(value, output_dir)'''
new = '''def _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:
    """Resolve generated files/directories through the virtual-workspace contract."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    # RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY
    # extract_zip uses output_dir while all other producers use output_path.
    for key in ('output_path', 'output_dir'):
        value = args.get(key)
        if isinstance(value, str):
            args[key] = resolve_output_path(value, output_dir)'''
tools = replace_once(tools, old, new, 'shared output path keys')

old = '''        "- WORKSPACE PATH RULE: use path='.' for the workspace root and relative paths like folder/file.txt below it. Do not invent Linux roots such as /workspace or /output.",
        "- Choose a sensible output filename yourself. Do not ask the user for an output path when a filename can be chosen safely.",'''
new = '''        "- WORKSPACE PATH RULE: use path='.' for the workspace root and relative paths like folder/file.txt below it. Never use bare '/' or Linux-style absolute roots; the app owns the real Android paths.",
        "- OUTPUT PATH RULE: choose a relative filename such as result.txt or folder/result.pdf; never prefix generated filenames with '/'.",
        "- Choose a sensible output filename yourself. Do not ask the user for an output path when a filename can be chosen safely.",'''
tools = replace_once(tools, old, new, 'local path prompt')

for required in [
    'RASTACODER_V17_ALL_LOCAL_PATH_BOUNDARY',
    'RASTACODER_V17_OUTPUT_DIRECTORY_BOUNDARY',
    'OUTPUT PATH RULE:',
]:
    if required not in tools:
        raise SystemExit(f'Missing V17 executor invariant: {required}')
TOOLS.write_text(tools, encoding='utf-8')

print('Applied V17 systemic local-tool ABI and shared path-boundary hardening')

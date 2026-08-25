#!/usr/bin/env python3
"""Third-pass systemic reliability hardening for RastaCoder v6.

Targets failure shapes which are common with 3B-4B models across the whole
21-Skill surface: raw-string arguments, filename/path aliases, ambiguous Word
routing, archive/document destinations, common URL/media aliases, simple Office
modify calls, Calendar event wrapping, and preservation of the model's original
tool call for user-copyable diagnostics.
"""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Compatibility layer.
# ---------------------------------------------------------------------------
compat_path = Path('python/navixmind/tools/compat.py')
text = compat_path.read_text(encoding='utf-8')

# Treat query as a generic free-form carrier for tools where it is not a
# canonical field (while preserving gmail.query later).
text = replace_once(
    text,
    '    for key in ("param", "request", "instruction", "command"):\n',
    '    for key in ("param", "request", "instruction", "command", "query"):\n',
    'freeform query carrier',
)

# Route Word skill calls which clearly reference an existing .docx to read,
# unless the language clearly requests creation or modification.
old = '''    elif name == "word":
        if keys & {"operations", "operation"} or _contains_any(free, ("modify", "edit", "replace", "修改", "替换", "编辑")):
            routed = "modify_docx"
        elif keys & {"docx_path", "extract"} or _contains_any(free, ("read", "extract", "inspect", "读取", "提取")):
            routed = "read_docx"
        else:
            routed = "create_docx"
'''
new = '''    elif name == "word":
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
'''
text = replace_once(text, old, new, 'word deterministic routing')

# Add a deterministic destination-file detector after target-format parsing.
anchor = '''def _extension(path: Any) -> str:
'''
helper = r'''
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
            if re.search(re.escape(transition) + r'''\s*["']?''' + escaped, text, flags=re.IGNORECASE):
                return candidate
    return None

'''
if helper.strip() not in text:
    text = text.replace(anchor, helper + anchor, 1)

# URL aliases are common in small-model JSON calls.
old = '''    if name in {"ffmpeg_process", "smart_crop", "convert_document", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "input_path", ["file", "path", "source", "source_path", "input", "input_file", "filename"], notes)

    if name in {"ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file", "create_zip", "modify_docx", "modify_pptx", "modify_xlsx"}:
'''
new = '''    if name in {"ffmpeg_process", "smart_crop", "convert_document", "modify_docx", "modify_pptx", "modify_xlsx"}:
        _move_alias(args, "input_path", ["file", "path", "source", "source_path", "input", "input_file", "filename"], notes)

    if name in {"web_fetch", "headless_browser", "download_media"}:
        _move_alias(args, "url", ["link", "uri", "website", "address"], notes)

    if name in {"ffmpeg_process", "smart_crop", "create_pdf", "create_docx", "write_file", "create_zip", "modify_docx", "modify_pptx", "modify_xlsx"}:
'''
text = replace_once(text, old, new, 'url aliases')

# Creation tools frequently use filename/path for their destination.
old = '''    free = _freeform(args)
    _apply_freeform(name, args, free, notes)
'''
new = '''    if name in {"write_file", "create_docx", "create_pdf"}:
        _move_alias(args, "output_path", ["filename", "file_name", "path", "file"], notes)
    if name == "create_zip":
        _move_alias(args, "output_path", ["filename", "file_name", "archive", "archive_path"], notes)

    free = _freeform(args)
    _apply_freeform(name, args, free, notes)
'''
text = replace_once(text, old, new, 'creation filename aliases')

# ZIP: distinguish source files from a requested output .zip.
old = '''    if name == "create_zip" and files and "file_paths" not in args:
        args["file_paths"] = files
        notes.append("freeform->file_paths")
'''
new = '''    if name == "create_zip" and files:
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
'''
text = replace_once(text, old, new, 'zip source destination split')

# Document conversion: explicit target filename determines both output path and
# target format, avoiding the common "to output.docx" ambiguity.
old = '''    if name == "convert_document":
        fmt = _target_format(free)
        if fmt and "output_format" not in args:
            args["output_format"] = fmt
            notes.append("freeform->output_format")
'''
new = '''    if name == "convert_document":
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
'''
text = replace_once(text, old, new, 'document destination inference')

# FFmpeg target-format aliases and extra operation aliases.
old = '''    if name == "ffmpeg_process":
        _move_alias(args, "operation", ["action", "op", "task"], notes)
        if "operation" in args:
'''
new = '''    if name == "ffmpeg_process":
        _move_alias(args, "operation", ["action", "op", "task"], notes)
        _move_alias(args, "format", ["target_format", "output_format", "to_format"], notes)
        if "operation" in args:
'''
text = replace_once(text, old, new, 'ffmpeg format aliases')
text = replace_once(
    text,
    '                "transcode": "convert", "conversion": "convert",\n',
    '                "transcode": "convert", "conversion": "convert",\n                "convert_audio": "extract_audio", "audio_convert": "extract_audio", "audio_conversion": "extract_audio",\n',
    'ffmpeg audio operation aliases',
)

# Smart crop common ratio aliases.
old = '''    if name == "smart_crop" and "aspect_ratio" in args:
'''
new = '''    if name == "smart_crop":
        _move_alias(args, "aspect_ratio", ["ratio", "target_ratio", "aspect"], notes)

    if name == "smart_crop" and "aspect_ratio" in args:
'''
text = replace_once(text, old, new, 'smart crop ratio aliases')

# Simple top-level Office actions are wrapped into the canonical operations[]
# form and their action names are normalized conservatively.
old = '''    if name in {"modify_docx", "modify_pptx", "modify_xlsx"}:
        if isinstance(args.get("operations"), dict):
            args["operations"] = [args["operations"]]
            notes.append("operations:object->list")
        if "operation" in args and "operations" not in args and isinstance(args["operation"], dict):
            args["operations"] = [args.pop("operation")]
            notes.append("operation->operations")
'''
new = '''    if name in {"modify_docx", "modify_pptx", "modify_xlsx"}:
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
'''
text = replace_once(text, old, new, 'office action wrapping')

# Calendar create calls often emit event fields at top level.
old = '''    if name == "google_calendar":
        _move_alias(args, "action", ["operation", "op"], notes)
        _move_alias(args, "date_range", ["date", "range", "time_range"], notes)
        _move_alias(args, "event_id", ["id", "calendar_event_id"], notes)
        if "action" in args:
'''
new = '''    if name == "google_calendar":
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
'''
text = replace_once(text, old, new, 'calendar event wrapper')

# Download-media format aliases.
old = '''    if name == "gmail":
        _move_alias(args, "action", ["operation", "op"], notes)
'''
new = '''    if name == "download_media" and "format" in args:
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
'''
text = replace_once(text, old, new, 'download format aliases')

# Keep gmail.query because it is canonical; remove generic query everywhere else.
old = '''    for key in ("param", "request", "instruction", "command"):
        if key in args:
            args.pop(key, None)
            notes.append(f"removed:{key}")
'''
new = '''    for key in ("param", "request", "instruction", "command", "query"):
        if key == "query" and name == "gmail":
            continue
        if key in args:
            args.pop(key, None)
            notes.append(f"removed:{key}")
'''
text = replace_once(text, old, new, 'generic query cleanup')

compat_path.write_text(text, encoding='utf-8')


# ---------------------------------------------------------------------------
# Agent parser / diagnostics.
# ---------------------------------------------------------------------------
agent_path = Path('python/navixmind/agent.py')
agent = agent_path.read_text(encoding='utf-8')

# Preserve a raw string argument as a free-form param instead of dropping it.
old = '''def _coerce_tool_args(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = _parse_mapping(value)
        return parsed if isinstance(parsed, dict) else {}
    return {}
'''
new = '''def _coerce_tool_args(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = _parse_mapping(value)
        if isinstance(parsed, dict):
            return parsed
        value = value.strip()
        return {"param": value} if value else {}
    return {}
'''
agent = replace_once(agent, old, new, 'raw string arguments')

# Preserve original tool name/arguments/source and parser repairs in tool blocks
# so the user can tell model output from compatibility repair.
old = '''def _build_tool_use(name: Any, arguments: Any, source: str, index: int) -> Optional[dict]:
    # Normalize with arguments BEFORE checking the canonical-name set. This is
    # required for v5 UI Skill IDs such as audio_processing and word.
    args = _coerce_tool_args(arguments)
    canonical, args, _ = normalize_tool_call(name, args)
    known = {t['name'] for t in TOOLS_SCHEMA}
    if canonical not in known:
        return None
    return {
        "type": "tool_use",
        "id": f"call_{abs(hash(source)) % 10**8:08d}_{index}",
        "name": canonical,
        "input": args,
    }
'''
new = '''def _build_tool_use(name: Any, arguments: Any, source: str, index: int) -> Optional[dict]:
    # Normalize with arguments BEFORE checking the canonical-name set. Preserve
    # both sides of that repair for the copyable diagnostic log.
    raw_args = _coerce_tool_args(arguments)
    canonical, args, parser_repairs = normalize_tool_call(name, raw_args)
    known = {t['name'] for t in TOOLS_SCHEMA}
    if canonical not in known:
        return None
    return {
        "type": "tool_use",
        "id": f"call_{abs(hash(source)) % 10**8:08d}_{index}",
        "name": canonical,
        "input": args,
        "_raw_name": str(name or ""),
        "_raw_input": raw_args,
        "_raw_source": str(source)[:1500],
        "_parser_repairs": list(parser_repairs),
    }
'''
agent = replace_once(agent, old, new, 'parser raw diagnostics metadata')

# Structured tool calls also retain pre-normalization values.
old = '''            if block.get('type') == 'tool_use':
                name, tool_input, _ = normalize_tool_call(
                    block.get('name'), _coerce_tool_args(block.get('input', {}))
                )
                block = dict(block)
                block['name'] = name
                block['input'] = tool_input
            sanitized_content.append(block)
'''
new = '''            if block.get('type') == 'tool_use':
                raw_name = block.get('name')
                raw_input = _coerce_tool_args(block.get('input', {}))
                name, tool_input, parser_repairs = normalize_tool_call(raw_name, raw_input)
                block = dict(block)
                block['_raw_name'] = str(raw_name or '')
                block['_raw_input'] = raw_input
                block['_raw_source'] = json.dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500]
                block['_parser_repairs'] = list(parser_repairs)
                block['name'] = name
                block['input'] = tool_input
            sanitized_content.append(block)
'''
agent = replace_once(agent, old, new, 'structured raw diagnostics')

old = '''                if block.get('type') == 'tool_use':
                    name, args, _ = normalize_tool_call(
                        block.get('name'), _coerce_tool_args(block.get('input', {}))
                    )
                    block = dict(block)
                    block['name'] = name
                    block['input'] = args
                normalized.append(block)
'''
new = '''                if block.get('type') == 'tool_use':
                    raw_name = block.get('_raw_name', block.get('name'))
                    raw_input = block.get('_raw_input', _coerce_tool_args(block.get('input', {})))
                    name, args, parser_repairs = normalize_tool_call(block.get('name'), block.get('input', {}))
                    block = dict(block)
                    block.setdefault('_raw_name', str(raw_name or ''))
                    block.setdefault('_raw_input', raw_input)
                    block.setdefault('_raw_source', json.dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500])
                    existing_repairs = block.get('_parser_repairs') if isinstance(block.get('_parser_repairs'), list) else []
                    block['_parser_repairs'] = list(existing_repairs) + [r for r in parser_repairs if r not in existing_repairs]
                    block['name'] = name
                    block['input'] = args
                normalized.append(block)
'''
agent = replace_once(agent, old, new, 'structured parser second pass diagnostics')

# Strip orphan tool XML when a JSON/function call was recovered, and classify
# even an unterminated tool wrapper as a parse error rather than final prose.
old = '''            if tool_blocks:
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
'''
new = '''            if tool_blocks:
                found = True
                remaining = re.sub(
                    r'</?(?:tool_call|function_call|function)\\b[^>]*>',
                    '', remaining, flags=re.IGNORECASE,
                ).strip()
                if remaining:
                    new_content.append({"type": "text", "text": remaining})
                new_content.extend(tool_blocks)
            elif tag_matches or re.search(r'<(?:tool_call|function_call|function)\\b', text, flags=re.IGNORECASE):
                # Recognizable tool-call wrapper, invalid payload/name. Never
                # leak it into final prose; let the ReAct loop request a retry.
                response['_tool_parse_error'] = tagged[:1500] if tag_matches else original[:1500]
                remaining = re.sub(
                    r'</?(?:tool_call|function_call|function)\\b[^>]*>',
                    '', remaining, flags=re.IGNORECASE,
                ).strip()
                new_content.append({"type": "text", "text": remaining}) if remaining else None
            else:
                new_content.append(block)
'''
agent = replace_once(agent, old, new, 'orphan tool wrapper hardening')

# Use preserved raw parser metadata in per-query diagnostics.
old = '''                    raw_tool_name = tool_name
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
new = '''                    raw_tool_name = block.get('_raw_name', tool_name)
                    raw_tool_input = block.get('_raw_input', tool_input)
                    parser_repairs = block.get('_parser_repairs') if isinstance(block.get('_parser_repairs'), list) else []
                    raw_source = block.get('_raw_source')
                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)
                    if is_offline:
                        repairs = list(parser_repairs) + [r for r in compat_notes if r not in parser_repairs]
                        context['_diagnostics'].append({
                            'stage': 'tool_call',
                            'raw_name': str(raw_tool_name),
                            'raw_args': _diag_safe(raw_tool_input),
                            'raw_source': _diag_safe(raw_source),
                            'canonical_name': tool_name,
                            'canonical_args': _diag_safe(tool_input),
                            'repairs': repairs,
                        })
'''
agent = replace_once(agent, old, new, 'true raw tool diagnostics')

# Ensure local early-error/max-step returns also contain Thinking/diagnostics.
old = '''        except APIError as e:
            bridge.log(f"API error: {e}", level="error")
            error_msg = _get_user_friendly_error(e)
            session.add_message("assistant", error_msg)
            return {"content": error_msg, "error": True}
'''
new = '''        except APIError as e:
            bridge.log(f"API error: {e}", level="error")
            error_msg = _get_user_friendly_error(e)
            session.add_message("assistant", error_msg)
            result = {"content": error_msg, "error": True}
            if is_offline:
                context['_diagnostics'].append({'stage': 'model_error', 'error': str(e)[:2000]})
                result['thinking'] = "\\n\\n".join(reasoning_parts)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result
'''
agent = replace_once(agent, old, new, 'local API error diagnostics')

old = '''        except Exception as e:
            CrashLogger.log_error("process_query", e)
            bridge.log(f"Exception: {str(e)}", level="error")
            error_msg = f"An unexpected error occurred: {e}"
            session.add_message("assistant", error_msg)
            return {
                "content": error_msg,
                "error": True
            }
'''
new = '''        except Exception as e:
            CrashLogger.log_error("process_query", e)
            bridge.log(f"Exception: {str(e)}", level="error")
            error_msg = f"An unexpected error occurred: {e}"
            session.add_message("assistant", error_msg)
            result = {"content": error_msg, "error": True}
            if is_offline:
                context['_diagnostics'].append({'stage': 'unexpected_error', 'error': str(e)[:2000]})
                result['thinking'] = "\\n\\n".join(reasoning_parts)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result
'''
agent = replace_once(agent, old, new, 'local unexpected error diagnostics')

old = '''        if partial:
            session.add_message("assistant", partial)
            return {"content": partial}
        break

    # Reached max iterations
    summary = _summarize_progress(messages, tool_call_count)
    max_iter_msg = f"I've reached my step limit after {iteration} iterations and {tool_call_count} tool calls. {summary}"
    session.add_message("assistant", max_iter_msg)
    return {"content": max_iter_msg}
'''
new = '''        if partial:
            session.add_message("assistant", partial)
            result = {"content": partial}
            if is_offline:
                result['thinking'] = "\\n\\n".join(reasoning_parts)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result
        break

    # Reached max iterations
    summary = _summarize_progress(messages, tool_call_count)
    max_iter_msg = f"I've reached my step limit after {iteration} iterations and {tool_call_count} tool calls. {summary}"
    session.add_message("assistant", max_iter_msg)
    result = {"content": max_iter_msg}
    if is_offline:
        context['_diagnostics'].append({'stage': 'max_iterations', 'iterations': iteration, 'tool_calls': tool_call_count})
        result['thinking'] = "\\n\\n".join(reasoning_parts)
        result['thinking_mode'] = local_thinking_mode
        result['diagnostics'] = _format_diagnostics(context)
    return result
'''
agent = replace_once(agent, old, new, 'terminal diagnostics')

agent_path.write_text(agent, encoding='utf-8')
print('Applied v6 deep systemic tool/parser/diagnostic reliability hardening')

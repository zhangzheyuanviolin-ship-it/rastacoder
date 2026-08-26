from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Anchor not found in {path}: {old[:120]!r}')
    if text.count(old) != 1:
        raise SystemExit(f'Anchor is not unique in {path}: count={text.count(old)}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# ---------------------------------------------------------------------------
# 1. Generic small-model argument-key sanitation + list_files compatibility.
# ---------------------------------------------------------------------------
compat_path = 'python/navixmind/tools/compat.py'
compat = Path(compat_path).read_text(encoding='utf-8')
if '# RASTACODER_V11_ARGUMENT_KEY_SANITIZER' not in compat:
    replace_once(
        compat_path,
        '\ndef normalize_tool_call(\n',
        '''\n# RASTACODER_V11_ARGUMENT_KEY_SANITIZER\ndef _sanitize_argument_keys(args: Dict[str, Any], notes: List[str]) -> Dict[str, Any]:\n    \"\"\"Repair punctuation copied from human-readable optional-argument hints.\n\n    Small local models sometimes emit keys such as ``path?`` or ``recursive?``.\n    Canonical keys always win if both spellings are present. Conflicting aliases\n    are dropped instead of silently overwriting an explicit canonical value.\n    \"\"\"\n    cleaned: Dict[str, Any] = {}\n    origins: Dict[str, str] = {}\n    for raw_key, value in args.items():\n        original = str(raw_key)\n        key = original.strip()\n        key = re.sub(r'[\\s?？:：]+$', '', key)\n        if not key:\n            notes.append(f'dropped_empty_key:{original!r}')\n            continue\n        if key != original:\n            notes.append(f'arg_key:{original}->{key}')\n        if key in cleaned:\n            previous = origins.get(key, key)\n            if original == key and previous != key:\n                cleaned[key] = value\n                origins[key] = original\n                notes.append(f'arg_key_collision:canonical_wins:{key}')\n            elif cleaned[key] != value:\n                notes.append(f'arg_key_collision:dropped:{original}->{key}')\n            continue\n        cleaned[key] = value\n        origins[key] = original\n    return cleaned\n\n\ndef normalize_tool_call(\n'''
    )

    replace_once(
        compat_path,
        '''    name = TOOL_ALIASES.get(raw_token, raw_token)\n''',
        '''    args = _sanitize_argument_keys(args, notes)\n\n    name = TOOL_ALIASES.get(raw_token, raw_token)\n'''
    )

    replace_once(
        compat_path,
        '''    if name == "download_media" and "format" in args:\n''',
        '''    # RASTACODER_V11_WORKSPACE_LIST_COMPAT\n    if name == "list_files":\n        _move_alias(args, "path", ["folder", "folder_path", "dir", "directory_path"], notes)\n        directory = args.get("directory")\n        path_value = args.get("path")\n\n        # A frequent Qwen small-model failure is interpreting optionality as a\n        # boolean. Treat that as omitted/default rather than rejecting the call.\n        if isinstance(directory, bool) or (isinstance(directory, str) and directory.strip().lower() in {"true", "false"}):\n            args.pop("directory", None)\n            directory = None\n            notes.append("list_files:removed_boolean_directory")\n        if isinstance(path_value, bool):\n            args.pop("path", None)\n            path_value = None\n            notes.append("list_files:removed_boolean_path")\n\n        roots = {"output", "downloads", "documents", "pictures", "screenshots", "camera"}\n        directory_key = str(directory or "").strip().lower()\n        path_text = str(args.get("path") or "").strip().replace("\\\\", "/")\n        workspace_aliases = {"", ".", "./", "output", "output/", "workspace", "workspace/"}\n\n        if directory_key in roots:\n            if directory_key == "output":\n                if path_text.lower() in workspace_aliases:\n                    args["path"] = "."\n                elif path_text.lower().startswith("output/"):\n                    args["path"] = path_text[7:] or "."\n            else:\n                if path_text.lower() in workspace_aliases:\n                    args["path"] = directory_key\n                elif path_text and not os.path.isabs(path_text) and not any(\n                    path_text.lower() == root or path_text.lower().startswith(root + "/") for root in roots\n                ):\n                    args["path"] = f"{directory_key}/{path_text.lstrip('./')}"\n                elif not path_text:\n                    args["path"] = directory_key\n            args.pop("directory", None)\n            notes.append(f"list_files:directory->{args.get('path', '.')}")\n        elif "directory" in args:\n            # Unknown legacy directory strings are treated as a path only when\n            # no explicit path exists. This keeps the canonical model interface\n            # to one path concept.\n            if not path_text and isinstance(directory, str) and directory.strip():\n                args["path"] = directory.strip()\n                notes.append("list_files:legacy_directory->path")\n            args.pop("directory", None)\n\n        path_text = str(args.get("path") or ".").strip().replace("\\\\", "/")\n        if path_text.lower() in workspace_aliases:\n            args["path"] = "."\n        elif path_text.lower().startswith("output/"):\n            args["path"] = path_text[7:] or "."\n        elif path_text.lower().startswith("workspace/"):\n            args["path"] = path_text[10:] or "."\n\n        for bool_key in ("recursive", "include_directories"):\n            if isinstance(args.get(bool_key), str):\n                lowered = args[bool_key].strip().lower()\n                if lowered in {"true", "1", "yes", "on"}:\n                    args[bool_key] = True\n                    notes.append(f"{bool_key}:string->true")\n                elif lowered in {"false", "0", "no", "off"}:\n                    args[bool_key] = False\n                    notes.append(f"{bool_key}:string->false")\n        if args.get("pattern") in ("", None):\n            args.pop("pattern", None)\n\n    if name == "download_media" and "format" in args:\n'''
    )


# ---------------------------------------------------------------------------
# 2. Make list_files and file_manage share one real workspace root.
# ---------------------------------------------------------------------------
ext_path = 'python/navixmind/tools/extended_tools.py'
ext = Path(ext_path).read_text(encoding='utf-8')
if '# RASTACODER_V11_WORKSPACE_ROOT' not in ext:
    replace_once(
        ext_path,
        '''def _resolve_workspace_path(value: str, _output_dir: Optional[str]) -> str:\n    \"\"\"Resolve model-facing relative paths against the real app output root.\"\"\"\n    raw = os.path.expanduser(str(value or '').strip())\n    if not raw:\n        return raw\n    if os.path.isabs(raw):\n        return os.path.normpath(raw)\n    normalized = raw.replace('\\\\', '/').lstrip('./')\n    root = _default_output_dir(_output_dir)\n    if normalized == 'output':\n        return os.path.normpath(root)\n    if normalized.startswith('output/'):\n        normalized = normalized[len('output/'): ]\n    return os.path.normpath(os.path.join(root, normalized))\n''',
        '''# RASTACODER_V11_WORKSPACE_ROOT\ndef _resolve_workspace_path(value: str, _output_dir: Optional[str]) -> str:\n    \"\"\"Resolve a model-facing path against the real writable workspace.\"\"\"\n    raw = os.path.expanduser(str(value or '').strip())\n    root = os.path.normpath(_default_output_dir(_output_dir))\n    if not raw:\n        return root\n    if os.path.isabs(raw):\n        return os.path.normpath(raw)\n    normalized = raw.replace('\\\\', '/').strip()\n    while normalized.startswith('./'):\n        normalized = normalized[2:]\n    if normalized in {'', '.', 'output', 'output/', 'workspace', 'workspace/'}:\n        return root\n    if normalized.startswith('output/'):\n        normalized = normalized[len('output/'):]\n    elif normalized.startswith('workspace/'):\n        normalized = normalized[len('workspace/'):]\n    if normalized == '..' or normalized.startswith('../'):\n        raise ToolError(f'Workspace path escapes output root: {value}')\n    candidate = os.path.normpath(os.path.join(root, normalized))\n    try:\n        if os.path.commonpath([root, candidate]) != root:\n            raise ToolError(f'Workspace path escapes output root: {value}')\n    except ValueError:\n        raise ToolError(f'Workspace path is invalid: {value}')\n    return candidate\n'''
    )

    replace_once(
        ext_path,
        '''def list_files(\n''',
        '''def _resolve_list_target(directory: str, path: Optional[str], _output_dir: Optional[str]) -> str:\n    \"\"\"Resolve one canonical list target. Relative paths are workspace-relative.\"\"\"\n    named = {\n        "output": _default_output_dir(_output_dir),\n        "downloads": "/storage/emulated/0/Download",\n        "documents": "/storage/emulated/0/Documents",\n        "pictures": "/storage/emulated/0/Pictures",\n        "screenshots": "/storage/emulated/0/Pictures/Screenshots",\n        "camera": "/storage/emulated/0/DCIM/Camera",\n    }\n    raw = str(path or '').strip().replace('\\\\', '/')\n    directory_key = str(directory or 'output').strip().lower()\n    if not raw:\n        return os.path.normpath(named.get(directory_key, _resolve_named_directory(directory_key, _output_dir)))\n    if os.path.isabs(raw):\n        return os.path.normpath(raw)\n    while raw.startswith('./'):\n        raw = raw[2:]\n    if raw in {'', '.', 'output', 'output/', 'workspace', 'workspace/'}:\n        return os.path.normpath(named['output'])\n    first, _, remainder = raw.partition('/')\n    first_key = first.lower()\n    if first_key in named:\n        base = os.path.normpath(named[first_key])\n        if not remainder:\n            return base\n        if remainder == '..' or remainder.startswith('../'):\n            raise ToolError(f'Directory path escapes selected root: {path}')\n        target = os.path.normpath(os.path.join(base, remainder))\n        if os.path.commonpath([base, target]) != base:\n            raise ToolError(f'Directory path escapes selected root: {path}')\n        return target\n    if directory_key in named and directory_key != 'output':\n        base = os.path.normpath(named[directory_key])\n        if raw == '..' or raw.startswith('../'):\n            raise ToolError(f'Directory path escapes selected root: {path}')\n        target = os.path.normpath(os.path.join(base, raw))\n        if os.path.commonpath([base, target]) != base:\n            raise ToolError(f'Directory path escapes selected root: {path}')\n        return target\n    return _resolve_workspace_path(raw, _output_dir)\n\n\ndef list_files(\n'''
    )

    replace_once(
        ext_path,
        '''    target = path or _resolve_named_directory(directory, _output_dir)\n    if not os.path.isdir(target):\n''',
        '''    target = _resolve_list_target(directory, path, _output_dir)\n    if not os.path.isdir(target):\n'''
    )

    replace_once(
        ext_path,
        '''            "directory": target,\n            "count": len(entries),\n''',
        '''            "directory": target,\n            "requested_path": path if path not in (None, "") else ".",\n            "workspace_root": os.path.normpath(_default_output_dir(_output_dir)),\n            "count": len(entries),\n'''
    )


# ---------------------------------------------------------------------------
# 3. Canonical one-path list_files schema and global workspace path resolution.
# ---------------------------------------------------------------------------
tools_path = 'python/navixmind/tools/__init__.py'
tools = Path(tools_path).read_text(encoding='utf-8')
if '# RASTACODER_V11_CANONICAL_LIST_FILES' not in tools:
    replace_once(
        tools_path,
        '''# RASTACODER_V7_COMPLETE_SKILLS\n# Every structured v7 utility is available to the local model when its Skill is\n''',
        '''# RASTACODER_V11_CANONICAL_LIST_FILES\n# One model-facing path concept prevents directory/path ambiguity. Common Android\n# roots are addressed as path prefixes (downloads/, documents/, pictures/, etc.).\nfor _schema_list in (TOOLS_SCHEMA, OFFLINE_TOOLS_SCHEMA):\n    for _tool in _schema_list:\n        if _tool.get("name") == "list_files":\n            _tool["description"] = (\n                "List files/directories. path is relative to the app workspace by default; "\n                "use downloads/, documents/, pictures/, screenshots/, or camera/ for common Android folders."\n            )\n            _tool["input_schema"] = {\n                "type": "object",\n                "properties": {\n                    "path": {"type": "string", "default": ".", "description": "Workspace-relative folder path; '.' means workspace root"},\n                    "recursive": {"type": "boolean", "default": False},\n                    "pattern": {"type": "string", "description": "Optional glob such as *.pptx"},\n                    "include_directories": {"type": "boolean", "default": True},\n                },\n                "required": [],\n            }\n\n# RASTACODER_V7_COMPLETE_SKILLS\n# Every structured v7 utility is available to the local model when its Skill is\n'''
    )

    # Remove '?' suffix notation from every compact prompt hint. Qwen3 4B had\n    # copied these literal characters into JSON argument keys on real devices.
    p = Path(tools_path)
    text = p.read_text(encoding='utf-8')
    start = text.index('LOCAL_TOOL_PROMPT_HINTS = {')
    end = text.index('\n}\n\n\ndef _offline_tool_names', start) + 2
    block = text[start:end].replace('?', '')
    block = block.replace(
        '"list_files": "list_files(directory, path, recursive, pattern, include_directories)",',
        '"list_files": "list_files(path=\'.\', recursive=false, pattern=null, include_directories=true) ; path is workspace-relative",'
    )
    text = text[:start] + block + text[end:]
    p.write_text(text, encoding='utf-8')

    replace_once(
        tools_path,
        '''def _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:\n    \"\"\"Resolve relative output paths to a writable directory.\"\"\"\n    import os\n    os.makedirs(output_dir, exist_ok=True)\n    output_keys = ['output_path']\n    for key in output_keys:\n        if key in args:\n            value = args[key]\n            if isinstance(value, str) and not os.path.isabs(value):\n                args[key] = os.path.join(output_dir, value)\n''',
        '''# RASTACODER_V11_GLOBAL_WORKSPACE_PATHS\ndef _workspace_relative_path(value: str, output_dir: str) -> str:\n    import os\n    raw = str(value or '').strip().replace('\\\\', '/')\n    if not raw or raw in {'.', './', 'output', 'output/', 'workspace', 'workspace/'}:\n        return os.path.normpath(output_dir)\n    if os.path.isabs(raw):\n        return os.path.normpath(raw)\n    while raw.startswith('./'):\n        raw = raw[2:]\n    android_roots = {\n        'downloads': '/storage/emulated/0/Download',\n        'documents': '/storage/emulated/0/Documents',\n        'pictures': '/storage/emulated/0/Pictures',\n        'screenshots': '/storage/emulated/0/Pictures/Screenshots',\n        'camera': '/storage/emulated/0/DCIM/Camera',\n    }\n    first, _, remainder = raw.partition('/')\n    if first.lower() in android_roots:\n        base = os.path.normpath(android_roots[first.lower()])\n        if not remainder:\n            return base\n        if remainder == '..' or remainder.startswith('../'):\n            raise ToolError(f'Path escapes Android root: {value}')\n        target = os.path.normpath(os.path.join(base, remainder))\n        if os.path.commonpath([base, target]) != base:\n            raise ToolError(f'Path escapes Android root: {value}')\n        return target\n    if raw.startswith('output/'):\n        raw = raw[len('output/'):]\n    elif raw.startswith('workspace/'):\n        raw = raw[len('workspace/'):]\n    if raw == '..' or raw.startswith('../'):\n        raise ToolError(f'Path escapes workspace root: {value}')\n    root = os.path.normpath(output_dir)\n    target = os.path.normpath(os.path.join(root, raw))\n    if os.path.commonpath([root, target]) != root:\n        raise ToolError(f'Path escapes workspace root: {value}')\n    return target\n\n\ndef _resolve_workspace_input_paths(args: Dict[str, Any], output_dir: str) -> None:\n    path_keys = [\n        'image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'source_path',\n        'zip_path', 'docx_path', 'pptx_path', 'xlsx_path',\n    ]\n    for key in path_keys:\n        value = args.get(key)\n        if isinstance(value, str):\n            args[key] = _workspace_relative_path(value, output_dir)\n    for key in ('image_paths', 'file_paths', 'input_paths'):\n        values = args.get(key)\n        if isinstance(values, list):\n            args[key] = [\n                _workspace_relative_path(v, output_dir) if isinstance(v, str) else v\n                for v in values\n            ]\n    operations = args.get('operations')\n    if isinstance(operations, list):\n        for op in operations:\n            if not isinstance(op, dict) or not isinstance(op.get('params'), dict):\n                continue\n            params = op['params']\n            for key in ('image_path', 'file_path', 'source_path', 'input_path'):\n                if isinstance(params.get(key), str):\n                    params[key] = _workspace_relative_path(params[key], output_dir)\n\n\ndef _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:\n    \"\"\"Resolve relative outputs inside the writable workspace without output/output duplication.\"\"\"\n    import os\n    os.makedirs(output_dir, exist_ok=True)\n    value = args.get('output_path')\n    if isinstance(value, str) and not os.path.isabs(value):\n        raw = value.strip().replace('\\\\', '/')\n        while raw.startswith('./'):\n            raw = raw[2:]\n        if raw.startswith('output/'):\n            raw = raw[len('output/'):]\n        elif raw.startswith('workspace/'):\n            raw = raw[len('workspace/'):]\n        if raw == '..' or raw.startswith('../'):\n            raise ToolError(f'Output path escapes workspace root: {value}')\n        root = os.path.normpath(output_dir)\n        target = os.path.normpath(os.path.join(root, raw))\n        if os.path.commonpath([root, target]) != root:\n            raise ToolError(f'Output path escapes workspace root: {value}')\n        args['output_path'] = target\n'''
    )

    replace_once(
        tools_path,
        '''    # Resolve relative output paths to writable directory\n    output_dir = context.get('output_dir')\n    if output_dir:\n        _resolve_output_paths(args, output_dir)\n''',
        '''    # Resolve every model-facing relative file path against the same workspace root.\n    output_dir = context.get('output_dir')\n    if output_dir:\n        _resolve_workspace_input_paths(args, output_dir)\n        _resolve_output_paths(args, output_dir)\n'''
    )


# ---------------------------------------------------------------------------
# 4. Generic OpenAI-compatible cloud client using the same ReAct/tool layer.
# ---------------------------------------------------------------------------
agent_path = 'python/navixmind/agent.py'
agent = Path(agent_path).read_text(encoding='utf-8')
if '# RASTACODER_V11_OPENAI_COMPATIBLE_CLIENT' not in agent:
    replace_once(
        agent_path,
        '''\nclass APIError(Exception):\n''',
        '''\n# RASTACODER_V11_OPENAI_COMPATIBLE_CLIENT\nclass OpenAICompatibleClient:\n    \"\"\"Adapter for /v1/chat/completions providers with native tool_calls.\"\"\"\n\n    def __init__(self, base_url: str, api_key: str, model: str):\n        self.base_url = str(base_url or '').strip().rstrip('/')\n        self.api_key = str(api_key or '').strip()\n        self.model = str(model or '').strip()\n        if not self.base_url or not self.model:\n            raise APIError('OpenAI-compatible Base URL and Model ID are required', 400)\n\n    def _endpoint(self) -> str:\n        lower = self.base_url.lower()\n        if lower.endswith('/chat/completions'):\n            return self.base_url\n        if lower.endswith('/v1'):\n            return self.base_url + '/chat/completions'\n        return self.base_url + '/v1/chat/completions'\n\n    @staticmethod\n    def _convert_messages(messages: List[Dict[str, Any]], system: str) -> List[Dict[str, Any]]:\n        converted: List[Dict[str, Any]] = [{"role": "system", "content": system}]\n        for msg in messages:\n            role = str(msg.get('role', 'user'))\n            content = msg.get('content', '')\n            if isinstance(content, str):\n                converted.append({"role": role, "content": content})\n                continue\n            if not isinstance(content, list):\n                converted.append({"role": role, "content": str(content)})\n                continue\n            if role == 'assistant':\n                text_parts = []\n                calls = []\n                for block in content:\n                    if not isinstance(block, dict):\n                        continue\n                    if block.get('type') == 'text' and block.get('text'):\n                        text_parts.append(str(block.get('text')))\n                    elif block.get('type') == 'tool_use':\n                        calls.append({\n                            'id': str(block.get('id') or f"call_{len(calls)}"),\n                            'type': 'function',\n                            'function': {\n                                'name': str(block.get('name') or ''),\n                                'arguments': json.dumps(block.get('input') or {}, ensure_ascii=False),\n                            },\n                        })\n                item: Dict[str, Any] = {'role': 'assistant', 'content': '\\n'.join(text_parts) or None}\n                if calls:\n                    item['tool_calls'] = calls\n                converted.append(item)\n            elif role == 'user':\n                ordinary = []\n                for block in content:\n                    if isinstance(block, dict) and block.get('type') == 'tool_result':\n                        converted.append({\n                            'role': 'tool',\n                            'tool_call_id': str(block.get('tool_use_id') or ''),\n                            'content': str(block.get('content') or ''),\n                        })\n                    elif isinstance(block, dict) and block.get('type') == 'text':\n                        ordinary.append(str(block.get('text') or ''))\n                    elif isinstance(block, str):\n                        ordinary.append(block)\n                if any(x for x in ordinary):\n                    converted.append({'role': 'user', 'content': '\\n'.join(x for x in ordinary if x)})\n            else:\n                converted.append({'role': role, 'content': str(content)})\n        return converted\n\n    def create_message(\n        self, messages: List[Dict[str, Any]], system: str = SYSTEM_PROMPT,\n        tools: Optional[List[dict]] = None, max_tokens: int = 4096, retry_count: int = 2\n    ) -> dict:\n        headers = {'content-type': 'application/json'}\n        if self.api_key:\n            headers['authorization'] = f'Bearer {self.api_key}'\n        body: Dict[str, Any] = {\n            'model': self.model,\n            'messages': self._convert_messages(messages, system),\n            'max_tokens': int(max_tokens),\n        }\n        if tools:\n            body['tools'] = LocalLLMClient._convert_tools_to_openai(tools)\n            body['tool_choice'] = 'auto'\n\n        last_error: Optional[APIError] = None\n        for attempt in range(max(1, retry_count)):\n            try:\n                response = requests.post(self._endpoint(), headers=headers, json=body, timeout=120)\n                if response.status_code == 200:\n                    data = response.json()\n                    choices = data.get('choices') if isinstance(data, dict) else None\n                    if not isinstance(choices, list) or not choices:\n                        raise APIError('OpenAI-compatible response has no choices', 502)\n                    choice = choices[0] if isinstance(choices[0], dict) else {}\n                    message = choice.get('message') if isinstance(choice.get('message'), dict) else {}\n                    blocks: List[Dict[str, Any]] = []\n                    text = message.get('content')\n                    if isinstance(text, str) and text.strip():\n                        blocks.append({'type': 'text', 'text': text})\n                    raw_calls = message.get('tool_calls')\n                    if not isinstance(raw_calls, list):\n                        raw_calls = []\n                    legacy = message.get('function_call')\n                    if isinstance(legacy, dict):\n                        raw_calls = list(raw_calls) + [{'id': 'legacy_function_call', 'function': legacy}]\n                    for index, call in enumerate(raw_calls):\n                        if not isinstance(call, dict):\n                            continue\n                        fn = call.get('function') if isinstance(call.get('function'), dict) else call\n                        raw_name = fn.get('name')\n                        raw_args = _coerce_tool_args(fn.get('arguments', fn.get('args', {})))\n                        canonical, canonical_args, repairs = normalize_tool_call(raw_name, raw_args)\n                        blocks.append({\n                            'type': 'tool_use',\n                            'id': str(call.get('id') or f'call_{index}'),\n                            'name': canonical,\n                            'input': canonical_args,\n                            '_raw_name': str(raw_name or ''),\n                            '_raw_input': raw_args,\n                            '_raw_source': json.dumps(call, ensure_ascii=False)[:1500],\n                            '_parser_repairs': repairs,\n                        })\n                    finish = str(choice.get('finish_reason') or '').lower()\n                    if any(b.get('type') == 'tool_use' for b in blocks) or finish in {'tool_calls', 'function_call'}:\n                        stop_reason = 'tool_use'\n                    elif finish in {'length', 'max_tokens'}:\n                        stop_reason = 'max_tokens'\n                    else:\n                        stop_reason = 'end_turn'\n                    usage_raw = data.get('usage') if isinstance(data.get('usage'), dict) else {}\n                    return {\n                        'stop_reason': stop_reason,\n                        'content': blocks,\n                        'usage': {\n                            'input_tokens': int(usage_raw.get('prompt_tokens') or usage_raw.get('input_tokens') or 0),\n                            'output_tokens': int(usage_raw.get('completion_tokens') or usage_raw.get('output_tokens') or 0),\n                        },\n                    }\n\n                try:\n                    error_data = response.json()\n                except Exception:\n                    error_data = {}\n                error_obj = error_data.get('error') if isinstance(error_data, dict) else None\n                if isinstance(error_obj, dict):\n                    message = str(error_obj.get('message') or error_obj)\n                else:\n                    message = str(error_data or getattr(response, 'text', '') or 'Unknown API error')\n                last_error = APIError(message[:2000], int(response.status_code))\n                if response.status_code in {408, 429, 500, 502, 503, 504} and attempt < retry_count - 1:\n                    import time\n                    time.sleep(1 if response.status_code == 429 else 2 ** attempt)\n                    continue\n                raise last_error\n            except requests.Timeout:\n                last_error = APIError('OpenAI-compatible request timed out', 408)\n                if attempt < retry_count - 1:\n                    continue\n                raise last_error\n            except requests.RequestException as exc:\n                last_error = APIError(f'OpenAI-compatible network error: {exc}', 0)\n                if attempt < retry_count - 1:\n                    continue\n                raise last_error\n        raise last_error or APIError('Unknown OpenAI-compatible API error', 0)\n\n\nclass APIError(Exception):\n'''
    )

    replace_once(
        agent_path,
        '''    preferred = context.get('preferred_model', '')\n    is_offline_model = 'offline_model_info' in context if context else False\n\n    if not api_key and not is_offline_model:\n        return {\n            "content": "API key not configured. Please enter your Claude API key to get started, or select an offline model.",\n            "error": True\n        }\n''',
        '''    preferred = context.get('preferred_model', '')\n    is_offline_model = 'offline_model_info' in context if context else False\n    is_openai_compatible = preferred == 'openai-compatible'\n    openai_config = context.get('openai_compatible') if isinstance(context.get('openai_compatible'), dict) else {}\n\n    if is_openai_compatible:\n        if not str(openai_config.get('base_url') or '').strip() or not str(openai_config.get('model') or '').strip():\n            return {\n                "content": "OpenAI 兼容接口尚未配置完整。请在设置中填写 Base URL 和 Model ID。",\n                "error": True\n            }\n    elif not api_key and not is_offline_model:\n        return {\n            "content": "API key not configured. Please enter your Claude API key to get started, or select an offline model.",\n            "error": True\n        }\n'''
    )

    replace_once(
        agent_path,
        '''    else:\n        if system_prompt != SYSTEM_PROMPT:\n            bridge.log("Using custom system prompt", level="info")\n        # Create Claude client with selected model\n        client = ClaudeClient(api_key, model=selected_model)\n''',
        '''    else:\n        if system_prompt != SYSTEM_PROMPT:\n            bridge.log("Using custom system prompt", level="info")\n        if is_openai_compatible:\n            client = OpenAICompatibleClient(\n                base_url=str(openai_config.get('base_url') or ''),\n                api_key=str(openai_config.get('api_key') or ''),\n                model=str(openai_config.get('model') or selected_model),\n            )\n            bridge.log(f"Using OpenAI-compatible cloud model: {client.model}", level="info")\n        else:\n            client = ClaudeClient(api_key, model=selected_model)\n'''
    )

    replace_once(
        agent_path,
        '''                        model_result = (\n                            _prepare_tool_result_for_model(tool_name, result, context, max_tokens)\n                            if is_offline else result_str\n                        )\n''',
        '''                        model_result = (\n                            _prepare_tool_result_for_model(tool_name, result, context, max_tokens)\n                            if (is_offline or is_openai_compatible) else result_str\n                        )\n'''
    )

    replace_once(
        agent_path,
        '''                        error_content = _tool_error_for_model(tool_name, e) if is_offline else str(e)\n''',
        '''                        error_content = _tool_error_for_model(tool_name, e) if (is_offline or is_openai_compatible) else str(e)\n'''
    )

    replace_once(
        agent_path,
        '''    # Check 1: Cost budget threshold\n''',
        '''    # V11 custom OpenAI-compatible provider keeps the exact user-entered model ID.\n    if requested_model == 'openai-compatible':\n        cfg = context.get('openai_compatible') if isinstance(context.get('openai_compatible'), dict) else {}\n        model = str(cfg.get('model') or 'openai-compatible').strip()\n        return model, f"Using OpenAI-compatible model: {model}"\n\n    # Check 1: Cost budget threshold\n'''
    )


# ---------------------------------------------------------------------------
# 5. Flutter secure settings, model registry, bridge context and accessible UI.
# ---------------------------------------------------------------------------
storage_path = 'lib/core/services/storage_service.dart'
storage = Path(storage_path).read_text(encoding='utf-8')
if 'RASTACODER_V11_OPENAI_COMPAT_STORAGE' not in storage:
    replace_once(
        storage_path,
        '''  static const _keyApiKey = 'claude_api_key';\n''',
        '''  static const _keyApiKey = 'claude_api_key';\n  // RASTACODER_V11_OPENAI_COMPAT_STORAGE\n  static const _keyOpenAICompatibleBaseUrl = 'openai_compatible_base_url';\n  static const _keyOpenAICompatibleApiKey = 'openai_compatible_api_key';\n  static const _keyOpenAICompatibleModel = 'openai_compatible_model';\n'''
    )
    replace_once(
        storage_path,
        '''  // RASTACODER_V8_SEARCH_KEYS\n  String _searchApiStorageKey(String provider) {\n''',
        '''  Future<void> setOpenAICompatibleBaseUrl(String value) async {\n    final normalized = value.trim().replaceAll(RegExp(r'/+$'), '');\n    if (normalized.isEmpty) {\n      await _storage.delete(key: _keyOpenAICompatibleBaseUrl);\n    } else {\n      await _storage.write(key: _keyOpenAICompatibleBaseUrl, value: normalized);\n    }\n  }\n\n  Future<String?> getOpenAICompatibleBaseUrl() async =>\n      _storage.read(key: _keyOpenAICompatibleBaseUrl);\n\n  Future<void> setOpenAICompatibleApiKey(String value) async {\n    if (value.trim().isEmpty) {\n      await _storage.delete(key: _keyOpenAICompatibleApiKey);\n    } else {\n      await _storage.write(key: _keyOpenAICompatibleApiKey, value: value.trim());\n    }\n  }\n\n  Future<String?> getOpenAICompatibleApiKey() async =>\n      _storage.read(key: _keyOpenAICompatibleApiKey);\n\n  Future<void> setOpenAICompatibleModel(String value) async {\n    if (value.trim().isEmpty) {\n      await _storage.delete(key: _keyOpenAICompatibleModel);\n    } else {\n      await _storage.write(key: _keyOpenAICompatibleModel, value: value.trim());\n    }\n  }\n\n  Future<String?> getOpenAICompatibleModel() async =>\n      _storage.read(key: _keyOpenAICompatibleModel);\n\n  Future<Map<String, String>> getOpenAICompatibleConfig() async {\n    final baseUrl = (await getOpenAICompatibleBaseUrl())?.trim() ?? '';\n    final apiKey = (await getOpenAICompatibleApiKey())?.trim() ?? '';\n    final model = (await getOpenAICompatibleModel())?.trim() ?? '';\n    return {'base_url': baseUrl, 'api_key': apiKey, 'model': model};\n  }\n\n  // RASTACODER_V8_SEARCH_KEYS\n  String _searchApiStorageKey(String provider) {\n'''
    )

model_path = 'lib/core/models/model_registry.dart'
model = Path(model_path).read_text(encoding='utf-8')
if 'RASTACODER_V11_OPENAI_COMPAT_MODEL' not in model:
    replace_once(
        model_path,
        '''  static const cloudModels = [auto, opus, sonnet, haiku];\n''',
        '''  // RASTACODER_V11_OPENAI_COMPAT_MODEL\n  static const openAICompatible = ModelInfo(\n    id: 'openai-compatible',\n    displayName: 'OpenAI Compatible',\n    description: 'Custom Base URL, API Key and Model ID; uses the same tool layer',\n    provider: ModelProvider.cloud,\n    apiModelId: 'openai-compatible',\n  );\n\n  static const cloudModels = [auto, opus, sonnet, haiku, openAICompatible];\n'''
    )

bridge_path = 'lib/core/bridge/bridge.dart'
bridge = Path(bridge_path).read_text(encoding='utf-8')
if 'RASTACODER_V11_OPENAI_COMPAT_CONTEXT' not in bridge:
    replace_once(
        bridge_path,
        '''    final searchProviderSettings =\n        await StorageService.instance.getAllSearchProviderSettings();\n''',
        '''    final searchProviderSettings =\n        await StorageService.instance.getAllSearchProviderSettings();\n    // RASTACODER_V11_OPENAI_COMPAT_CONTEXT\n    final openAICompatibleConfig =\n        await StorageService.instance.getOpenAICompatibleConfig();\n'''
    )
    replace_once(
        bridge_path,
        '''      'search_provider_settings': searchProviderSettings,\n''',
        '''      'search_provider_settings': searchProviderSettings,\n      if (preferredModel == 'openai-compatible')\n        'openai_compatible': openAICompatibleConfig,\n'''
    )

settings_path = 'lib/features/settings/settings_screen.dart'
settings = Path(settings_path).read_text(encoding='utf-8')
if 'RASTACODER_V11_OPENAI_COMPAT_SETTINGS' not in settings:
    replace_once(
        settings_path,
        '''import 'local_model_benchmark_screen.dart';\n''',
        '''import 'local_model_benchmark_screen.dart';\nimport 'openai_compatible_settings_screen.dart';\n'''
    )
    replace_once(
        settings_path,
        '''          // Model Selection\n          _ModelSelector(\n''',
        '''          // RASTACODER_V11_OPENAI_COMPAT_SETTINGS\n          _SettingsTile(\n            title: 'OpenAI 兼容接口',\n            subtitle: '配置自定义 Base URL、API Key 与 Model ID；可用于云端工具调用对照测试',\n            trailing: const Icon(Icons.cloud_outlined, size: 20),\n            onTap: () => Navigator.push(\n              context,\n              MaterialPageRoute(builder: (_) => const OpenAICompatibleSettingsScreen()),\n            ),\n          ),\n\n          // Model Selection\n          _ModelSelector(\n'''
    )

openai_screen = Path('lib/features/settings/openai_compatible_settings_screen.dart')
if not openai_screen.exists():
    openai_screen.write_text(r'''import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../core/services/storage_service.dart';

// RASTACODER_V11_OPENAI_COMPAT_SETTINGS_SCREEN
class OpenAICompatibleSettingsScreen extends StatefulWidget {
  const OpenAICompatibleSettingsScreen({super.key});

  @override
  State<OpenAICompatibleSettingsScreen> createState() =>
      _OpenAICompatibleSettingsScreenState();
}

class _OpenAICompatibleSettingsScreenState
    extends State<OpenAICompatibleSettingsScreen> {
  final _baseUrlController = TextEditingController();
  final _apiKeyController = TextEditingController();
  final _modelController = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final config = await StorageService.instance.getOpenAICompatibleConfig();
    _baseUrlController.text = config['base_url'] ?? '';
    _apiKeyController.text = config['api_key'] ?? '';
    _modelController.text = config['model'] ?? '';
    if (mounted) setState(() => _loading = false);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    _apiKeyController.dispose();
    _modelController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final baseUrl = _baseUrlController.text.trim();
    final model = _modelController.text.trim();
    if (baseUrl.isEmpty || model.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Base URL 和 Model ID 不能为空')),
      );
      return;
    }
    final uri = Uri.tryParse(baseUrl);
    if (uri == null || !uri.hasScheme ||
        (uri.scheme != 'http' && uri.scheme != 'https')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Base URL 必须是 http 或 https 地址')),
      );
      return;
    }
    setState(() => _saving = true);
    await StorageService.instance.setOpenAICompatibleBaseUrl(baseUrl);
    await StorageService.instance.setOpenAICompatibleApiKey(_apiKeyController.text);
    await StorageService.instance.setOpenAICompatibleModel(model);
    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('OpenAI 兼容接口配置已保存')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: NavixTheme.background,
      appBar: AppBar(
        backgroundColor: NavixTheme.background,
        title: const Text('OpenAI 兼容接口'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  '兼容 OpenAI Chat Completions 工具调用协议。Base URL 可以填写服务根地址、以 /v1 结尾的地址，或完整 /chat/completions 地址。模型和本地 Qwen 共用同一套工具、兼容层与执行后验证。',
                ),
                const SizedBox(height: 16),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 Base URL',
                  child: TextField(
                    controller: _baseUrlController,
                    keyboardType: TextInputType.url,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Base URL',
                      hintText: 'https://api.example.com/v1',
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 API Key',
                  child: TextField(
                    controller: _apiKeyController,
                    obscureText: true,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'API Key',
                      hintText: '可留空：部分兼容服务不要求密钥',
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Semantics(
                  textField: true,
                  label: 'OpenAI 兼容接口 Model ID',
                  child: TextField(
                    controller: _modelController,
                    autocorrect: false,
                    decoration: const InputDecoration(
                      labelText: 'Model ID',
                      hintText: '例如 provider-model-name',
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Semantics(
                  button: true,
                  label: _saving ? '正在保存 OpenAI 兼容接口配置' : '保存 OpenAI 兼容接口配置',
                  child: ElevatedButton(
                    onPressed: _saving ? null : _save,
                    child: Text(_saving ? '正在保存…' : '保存'),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  '保存后回到“API 与模型”，在模型列表中选择 OpenAI Compatible。API Key 使用系统安全存储，并且不会写入模型提示词或工具参数。',
                ),
              ],
            ),
    );
  }
}
''', encoding='utf-8')

print('RastaCoder v11 workspace/OpenAI-compatible patch applied.')

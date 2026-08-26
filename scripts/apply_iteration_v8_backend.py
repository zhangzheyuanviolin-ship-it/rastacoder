from pathlib import Path


def patch(path: str, old: str, new: str, count: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'{path}: expected {count} occurrence(s), found {actual}: {old[:100]!r}')
    p.write_text(text.replace(old, new, count), encoding='utf-8')


# ---------------------------------------------------------------------------
# Secure search-provider API keys.
# ---------------------------------------------------------------------------
patch(
    'lib/core/services/storage_service.dart',
    "  static const _keyLocalBenchmarkHistory = 'local_benchmark_history';\n",
    "  static const _keyLocalBenchmarkHistory = 'local_benchmark_history';\n"
    "  // RASTACODER_V8_SEARCH_KEYS\n"
    "  static const _searchApiProviders = <String>{'anysearch', 'exa', 'langsearch', 'tavily'};\n",
)
patch(
    'lib/core/services/storage_service.dart',
    "  /// Delete API key\n  Future<void> deleteApiKey() async {\n    await _storage.delete(key: _keyApiKey);\n  }\n",
    "  /// Delete API key\n  Future<void> deleteApiKey() async {\n    await _storage.delete(key: _keyApiKey);\n  }\n\n"
    "  // RASTACODER_V8_SEARCH_KEYS\n"
    "  String _searchApiStorageKey(String provider) {\n"
    "    final normalized = provider.trim().toLowerCase();\n"
    "    if (!_searchApiProviders.contains(normalized)) {\n"
    "      throw ArgumentError('Unsupported search provider: $provider');\n"
    "    }\n"
    "    return 'search_api_key_$normalized';\n"
    "  }\n\n"
    "  Future<void> setSearchApiKey(String provider, String key) async {\n"
    "    final value = key.trim();\n"
    "    if (value.isEmpty) {\n"
    "      await deleteSearchApiKey(provider);\n"
    "      return;\n"
    "    }\n"
    "    await _storage.write(key: _searchApiStorageKey(provider), value: value);\n"
    "  }\n\n"
    "  Future<String?> getSearchApiKey(String provider) async {\n"
    "    final value = await _storage.read(key: _searchApiStorageKey(provider));\n"
    "    return value == null || value.trim().isEmpty ? null : value.trim();\n"
    "  }\n\n"
    "  Future<bool> hasSearchApiKey(String provider) async =>\n"
    "      (await getSearchApiKey(provider)) != null;\n\n"
    "  Future<void> deleteSearchApiKey(String provider) async {\n"
    "    await _storage.delete(key: _searchApiStorageKey(provider));\n"
    "  }\n\n"
    "  Future<Map<String, String>> getConfiguredSearchApiKeys() async {\n"
    "    final result = <String, String>{};\n"
    "    for (final provider in _searchApiProviders) {\n"
    "      final value = await getSearchApiKey(provider);\n"
    "      if (value != null) result[provider] = value;\n"
    "    }\n"
    "    return result;\n"
    "  }\n",
)

# ---------------------------------------------------------------------------
# Bridge: inject keys only into private execution context.
# ---------------------------------------------------------------------------
patch(
    'lib/core/bridge/bridge.dart',
    "    final localThinkingMode = await StorageService.instance.getLocalThinkingMode();\n",
    "    final localThinkingMode = await StorageService.instance.getLocalThinkingMode();\n"
    "    // Search credentials stay in secure storage and are injected only into\n"
    "    // execution context; they are never model-visible tool arguments.\n"
    "    final searchApiKeys = await StorageService.instance.getConfiguredSearchApiKeys();\n",
)
patch(
    'lib/core/bridge/bridge.dart',
    "      if (googleToken != null) 'google_access_token': googleToken,\n",
    "      if (googleToken != null) 'google_access_token': googleToken,\n"
    "      if (searchApiKeys.isNotEmpty) 'search_api_keys': searchApiKeys,\n",
)

# ---------------------------------------------------------------------------
# File workspace resolution + verified deletion.
# ---------------------------------------------------------------------------
patch(
    'python/navixmind/tools/extended_tools.py',
    "def _resolve_named_directory(directory: str, _output_dir: Optional[str]) -> str:\n",
    "def _resolve_workspace_path(value: str, _output_dir: Optional[str]) -> str:\n"
    "    \"\"\"Resolve model-facing relative paths against the real app output root.\"\"\"\n"
    "    raw = os.path.expanduser(str(value or '').strip())\n"
    "    if not raw:\n"
    "        return raw\n"
    "    if os.path.isabs(raw):\n"
    "        return os.path.normpath(raw)\n"
    "    normalized = raw.replace('\\\\', '/').lstrip('./')\n"
    "    root = _default_output_dir(_output_dir)\n"
    "    if normalized == 'output':\n"
    "        return os.path.normpath(root)\n"
    "    if normalized.startswith('output/'):\n"
    "        normalized = normalized[len('output/'): ]\n"
    "    return os.path.normpath(os.path.join(root, normalized))\n\n\n"
    "def _resolve_named_directory(directory: str, _output_dir: Optional[str]) -> str:\n",
)
start = "def file_manage(\n"
end = "\n\ndef list_zip(zip_path: str) -> dict:\n"
p = Path('python/navixmind/tools/extended_tools.py')
text = p.read_text(encoding='utf-8')
si = text.find(start)
ei = text.find(end, si)
if si < 0 or ei < 0:
    raise SystemExit('extended_tools.py: file_manage block not found')
new_file_manage = '''def file_manage(
    action: str,
    path: Optional[str] = None,
    source_path: Optional[str] = None,
    destination_path: Optional[str] = None,
    recursive: bool = False,
    overwrite: bool = False,
    _output_dir: Optional[str] = None,
) -> dict:
    """Manage files relative to the real app output root and verify mutations."""
    action = (action or "").strip().lower()
    source_raw = source_path or path

    try:
        if action == "list":
            resolved = _resolve_workspace_path(path, _output_dir) if path else _default_output_dir(_output_dir)
            return list_files(path=resolved, directory="output", recursive=recursive, _output_dir=_output_dir)

        if action == "mkdir":
            target_raw = path or destination_path
            if not target_raw:
                raise ToolError("mkdir requires path")
            target = _resolve_workspace_path(target_raw, _output_dir)
            os.makedirs(target, exist_ok=True)
            if not os.path.isdir(target):
                raise ToolError(f"mkdir verification failed: {target}")
            return {"success": True, "action": action, "path": target, "exists_after": True}

        if action == "exists":
            if not source_raw:
                raise ToolError("exists requires path")
            source = _resolve_workspace_path(source_raw, _output_dir)
            exists = os.path.lexists(source)
            return {
                "success": True,
                "action": action,
                "path": source,
                "exists": exists,
                "is_file": os.path.isfile(source),
                "is_directory": os.path.isdir(source),
            }

        if action == "touch":
            target_raw = source_raw or destination_path
            if not target_raw:
                raise ToolError("touch requires path")
            target = _resolve_workspace_path(target_raw, _output_dir)
            _ensure_parent(target)
            with open(target, "a", encoding="utf-8"):
                os.utime(target, None)
            if not os.path.isfile(target):
                raise ToolError(f"touch verification failed: {target}")
            return {"success": True, "action": action, "path": target, "exists_after": True}

        if action in {"copy", "move", "rename"}:
            if not source_raw or not destination_path:
                raise ToolError(f"{action} requires source_path and destination_path")
            source = _resolve_workspace_path(source_raw, _output_dir)
            destination = _resolve_workspace_path(destination_path, _output_dir)
            if not os.path.lexists(source):
                raise ToolError(f"Source not found: {source}")
            if os.path.lexists(destination):
                if not overwrite:
                    raise ToolError(f"Destination already exists: {destination}")
                if os.path.isdir(destination) and not os.path.islink(destination):
                    shutil.rmtree(destination)
                else:
                    os.remove(destination)
            _ensure_parent(destination)
            if action == "copy":
                if os.path.isdir(source) and not os.path.islink(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
                if not os.path.lexists(source) or not os.path.lexists(destination):
                    raise ToolError(f"Copy verification failed: {source} -> {destination}")
            else:
                shutil.move(source, destination)
                if os.path.lexists(source) or not os.path.lexists(destination):
                    raise ToolError(f"{action} verification failed: {source} -> {destination}")
            return {
                "success": True,
                "action": action,
                "source_path": source,
                "destination_path": destination,
                "destination_exists_after": True,
            }

        if action == "delete":
            if not source_raw:
                raise ToolError("delete requires path")
            source = _resolve_workspace_path(source_raw, _output_dir)
            if not os.path.lexists(source):
                raise ToolError(f"Delete target not found: {source}")
            if os.path.isdir(source) and not os.path.islink(source):
                if recursive:
                    shutil.rmtree(source)
                else:
                    os.rmdir(source)
            else:
                os.remove(source)
            if os.path.lexists(source):
                raise ToolError(f"Delete verification failed; target still exists: {source}")
            return {
                "success": True,
                "action": action,
                "path": source,
                "deleted": True,
                "exists_after": False,
            }

        raise ToolError(
            "Unknown file_manage action. Use list, mkdir, copy, move, rename, delete, touch, or exists."
        )
    except ToolError:
        raise
    except Exception as exc:
        raise ToolError(f"File operation failed ({action}): {exc}")
'''
p.write_text(text[:si] + new_file_manage + text[ei:], encoding='utf-8')

# ---------------------------------------------------------------------------
# Tool catalog + six search functions grouped as four independent Skills.
# ---------------------------------------------------------------------------
patch(
    'lib/core/models/tool_skill.dart',
    "  static const v7AddedToolNames = <String>{\n    'file_manage', 'list_zip', 'extract_zip', 'pdf_manage',\n    'create_pptx', 'create_xlsx',\n  };\n",
    "  static const v7AddedToolNames = <String>{\n    'file_manage', 'list_zip', 'extract_zip', 'pdf_manage',\n    'create_pptx', 'create_xlsx',\n  };\n\n"
    "  // RASTACODER_V8_SEARCH_SKILLS\n"
    "  static const v8SearchToolNames = <String>{\n"
    "    'anysearch_search', 'anysearch_extract', 'anysearch_get_sub_domains',\n"
    "    'exa_search', 'langsearch_search', 'tavily_search',\n"
    "  };\n",
)
patch(
    'lib/core/models/tool_skill.dart',
    "    ...v7AddedToolNames,\n  };\n",
    "    ...v7AddedToolNames,\n    ...v8SearchToolNames,\n  };\n",
)
anchor = "    LocalToolSkill(\n      id: 'basic_calculation', category: '计算与数据', title: '基础计算与 Python',\n"
insert = '''    LocalToolSkill(
      id: 'anysearch_search', category: '网络搜索', title: 'AnySearch 搜索',
      description: '独立使用 AnySearch 搜索、网页抽取和子域能力；API Key 由用户手动配置。',
      toolNames: ['anysearch_search', 'anysearch_extract', 'anysearch_get_sub_domains'],
      capabilities: ['通用网络搜索', '指定域/子域搜索', '网页正文抽取', '查询站点支持的子域', '手动配置 AnySearch API Key'],
    ),
    LocalToolSkill(
      id: 'exa_search', category: '网络搜索', title: 'Exa 搜索',
      description: '独立使用 Exa 神经/自动搜索；API Key 由用户手动配置。',
      toolNames: ['exa_search'],
      capabilities: ['网页搜索', '日期过滤', '域名包含/排除', '正文/摘要/高亮', '手动配置 Exa API Key'],
    ),
    LocalToolSkill(
      id: 'langsearch_search', category: '网络搜索', title: 'LangSearch 搜索',
      description: '独立使用 LangSearch 网络搜索；API Key 由用户手动配置。',
      toolNames: ['langsearch_search'],
      capabilities: ['网页搜索', '时间新鲜度过滤', '结果摘要', '手动配置 LangSearch API Key'],
    ),
    LocalToolSkill(
      id: 'tavily_search', category: '网络搜索', title: 'Tavily 搜索',
      description: '独立使用 Tavily 搜索；API Key 由用户手动配置。',
      toolNames: ['tavily_search'],
      capabilities: ['网页搜索', 'basic/advanced 深度', 'general/news 主题', '时间过滤', '域名过滤', '答案摘要', '手动配置 Tavily API Key'],
    ),
'''
patch('lib/core/models/tool_skill.dart', anchor, insert + anchor)

# ---------------------------------------------------------------------------
# Python tool registry/search schemas.
# ---------------------------------------------------------------------------
patch(
    'python/navixmind/tools/__init__.py',
    "from .media import download_media\n",
    "from .media import download_media\n"
    "from .search_tools import (\n"
    "    anysearch_search, anysearch_extract, anysearch_get_sub_domains,\n"
    "    exa_search, langsearch_search, tavily_search,\n"
    ")\n",
)
search_schema_block = r'''

# RASTACODER_V8_SEARCH_SKILLS
_V8_SEARCH_TOOL_SCHEMAS = [
    {
        "name": "anysearch_search",
        "description": "Search the web with AnySearch. API credential is configured by the user in Tool Management.",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "max_results": {"type": "integer"},
            "domain": {"type": "string"}, "sub_domain": {"type": "string"},
            "sub_domain_params": {"type": "object"}}, "required": ["query"]},
    },
    {
        "name": "anysearch_extract",
        "description": "Extract readable content from one web URL with AnySearch.",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "anysearch_get_sub_domains",
        "description": "List supported AnySearch sub-domains for one or more domains.",
        "input_schema": {"type": "object", "properties": {
            "domain": {"type": "string"}, "domains": {"type": "array", "items": {"type": "string"}}}},
    },
    {
        "name": "exa_search",
        "description": "Search the web with Exa and optionally return text, summaries, or highlights.",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "num_results": {"type": "integer"},
            "topic": {"type": "string", "enum": ["general", "news"]},
            "search_type": {"type": "string", "enum": ["auto", "neural", "fast", "deep"]},
            "start_published_date": {"type": "string"},
            "include_domains": {"type": "array", "items": {"type": "string"}},
            "exclude_domains": {"type": "array", "items": {"type": "string"}},
            "include_text": {"type": "boolean"}, "include_summary": {"type": "boolean"},
            "include_highlights": {"type": "boolean"}}, "required": ["query"]},
    },
    {
        "name": "langsearch_search",
        "description": "Search the web with LangSearch.",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "count": {"type": "integer"},
            "freshness": {"type": "string", "enum": ["oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"]},
            "summary": {"type": "boolean"}}, "required": ["query"]},
    },
    {
        "name": "tavily_search",
        "description": "Search the web with Tavily.",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "max_results": {"type": "integer"},
            "topic": {"type": "string", "enum": ["general", "news"]},
            "search_depth": {"type": "string", "enum": ["basic", "advanced"]},
            "include_answer": {"type": "boolean"}, "time_range": {"type": "string", "enum": ["", "day", "week", "month", "year"]},
            "include_domains": {"type": "array", "items": {"type": "string"}},
            "exclude_domains": {"type": "array", "items": {"type": "string"}},
            "include_raw_content": {"type": "boolean"}}, "required": ["query"]},
    },
]
_existing_tool_names = {t["name"] for t in TOOLS_SCHEMA}
TOOLS_SCHEMA.extend(t for t in _V8_SEARCH_TOOL_SCHEMAS if t["name"] not in _existing_tool_names)
_existing_offline_names = {t["name"] for t in OFFLINE_TOOLS_SCHEMA}
OFFLINE_TOOLS_SCHEMA.extend(t for t in _V8_SEARCH_TOOL_SCHEMAS if t["name"] not in _existing_offline_names)
'''
patch(
    'python/navixmind/tools/__init__.py',
    "\n\n# RASTACODER_V7_COMPLETE_SKILLS\n",
    search_schema_block + "\n\n# RASTACODER_V7_COMPLETE_SKILLS\n",
)
patch(
    'python/navixmind/tools/__init__.py',
    "    \"google_calendar\": {\"tools\": (\"google_calendar\",)},\n}\n",
    "    \"google_calendar\": {\"tools\": (\"google_calendar\",)},\n"
    "    \"anysearch_search\": {\"tools\": (\"anysearch_search\", \"anysearch_extract\", \"anysearch_get_sub_domains\")},\n"
    "    \"exa_search\": {\"tools\": (\"exa_search\",)},\n"
    "    \"langsearch_search\": {\"tools\": (\"langsearch_search\",)},\n"
    "    \"tavily_search\": {\"tools\": (\"tavily_search\",)},\n}\n",
)
patch(
    'python/navixmind/tools/__init__.py',
    "    \"google_calendar\": \"google_calendar(action, date_range?, event?, event_id?) ; action=list|create|delete|update\",\n}\n",
    "    \"google_calendar\": \"google_calendar(action, date_range?, event?, event_id?) ; action=list|create|delete|update\",\n"
    "    \"anysearch_search\": \"anysearch_search(query, max_results?, domain?, sub_domain?, sub_domain_params?)\",\n"
    "    \"anysearch_extract\": \"anysearch_extract(url)\",\n"
    "    \"anysearch_get_sub_domains\": \"anysearch_get_sub_domains(domain? or domains?)\",\n"
    "    \"exa_search\": \"exa_search(query, num_results?, topic?, search_type?, start_published_date?, include_domains?, exclude_domains?, include_text?, include_summary?, include_highlights?)\",\n"
    "    \"langsearch_search\": \"langsearch_search(query, count?, freshness?, summary?)\",\n"
    "    \"tavily_search\": \"tavily_search(query, max_results?, topic?, search_depth?, include_answer?, time_range?, include_domains?, exclude_domains?, include_raw_content?)\",\n"
    "}\n",
)
patch(
    'python/navixmind/tools/__init__.py',
    "        \"image_compose\": image_compose,\n    }\n",
    "        \"image_compose\": image_compose,\n"
    "        \"anysearch_search\": anysearch_search,\n"
    "        \"anysearch_extract\": anysearch_extract,\n"
    "        \"anysearch_get_sub_domains\": anysearch_get_sub_domains,\n"
    "        \"exa_search\": exa_search,\n"
    "        \"langsearch_search\": langsearch_search,\n"
    "        \"tavily_search\": tavily_search,\n"
    "    }\n",
)
patch(
    'python/navixmind/tools/__init__.py',
    "    if tool_name in [\"google_calendar\", \"gmail\"]:\n        args[\"_context\"] = context\n",
    "    if tool_name in [\n"
    "        \"google_calendar\", \"gmail\", \"anysearch_search\", \"anysearch_extract\",\n"
    "        \"anysearch_get_sub_domains\", \"exa_search\", \"langsearch_search\", \"tavily_search\",\n"
    "    ]:\n"
    "        args[\"_context\"] = context\n",
)

# ---------------------------------------------------------------------------
# Thinking data: remove tool-call payloads and suppress reasoning completely
# when the user selected /no_think.
# ---------------------------------------------------------------------------
agent = Path('python/navixmind/agent.py')
text = agent.read_text(encoding='utf-8')
marker = "def _extract_reasoning_blocks(content_blocks: List[Dict[str, Any]]) -> str:\n"
if text.count(marker) != 1:
    raise SystemExit('agent.py: reasoning marker missing')
sanitizer = r'''def _sanitize_reasoning(text: str) -> str:
    """Keep human-readable reasoning while excluding tool-call payloads."""
    import re
    value = str(text or '').strip()
    if not value:
        return ''
    value = re.sub(
        r'<(?:tool_call|function_call|tool_result|tool_use)>[\s\S]*?</(?:tool_call|function_call|tool_result|tool_use)>',
        '', value, flags=re.IGNORECASE,
    )
    value = re.sub(r'</?(?:tool_call|function_call|tool_result|tool_use)[^>]*>', '', value, flags=re.IGNORECASE)
    for obj in list(_extract_json_objects(value)):
        try:
            if _try_parse_tool_json(obj, 0) is not None:
                value = value.replace(obj, '')
        except Exception:
            pass
    known = {str(t.get('name', '')) for t in TOOLS_SCHEMA}
    kept = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if not line:
            if kept and kept[-1] != '':
                kept.append('')
            continue
        if lower.startswith(('tool:', 'result:', 'executing ', 'code:', 'file:', '[tool result]', '[tool error]')):
            continue
        if any(lower.startswith(name.lower() + '(') for name in known if name):
            continue
        kept.append(raw_line.rstrip())
    while kept and not kept[-1].strip():
        kept.pop()
    return '\n'.join(kept).strip()


def _thinking_for_ui(parts: List[str], mode: str) -> str:
    if str(mode) == 'disabled':
        return ''
    return _sanitize_reasoning('\n\n'.join(str(x) for x in parts if str(x).strip()))


'''
text = text.replace(marker, sanitizer + marker, 1)
text = text.replace("    return '\\n\\n'.join(parts)\n\n\ndef _strip_reasoning_from_blocks", "    return _sanitize_reasoning('\\n\\n'.join(parts))\n\n\ndef _strip_reasoning_from_blocks", 1)
old_reason = "            reasoning = str(response.get('_reasoning') or '').strip()\n            if reasoning:\n                reasoning_parts.append(reasoning)\n"
new_reason = "            reasoning = _sanitize_reasoning(str(response.get('_reasoning') or ''))\n            if reasoning and local_thinking_mode != 'disabled':\n                reasoning_parts.append(reasoning)\n"
if text.count(old_reason) != 1:
    raise SystemExit('agent.py: response reasoning block missing')
text = text.replace(old_reason, new_reason, 1)
text = text.replace('"\\n\\n".join(reasoning_parts)', '_thinking_for_ui(reasoning_parts, local_thinking_mode)')
text = text.replace("f\"Using on-device inference; skills={len(enabled_skills)}/21, tools={len(enabled_tools)}/23\"", "f\"Using on-device inference; skills={len(enabled_skills)}/{len(ALL_LOCAL_SKILL_IDS)}, tools={len(enabled_tools)}/{len(get_enabled_tool_names(ALL_LOCAL_SKILL_IDS))}\"")
agent.write_text(text, encoding='utf-8')

print('V8 backend patch applied successfully')

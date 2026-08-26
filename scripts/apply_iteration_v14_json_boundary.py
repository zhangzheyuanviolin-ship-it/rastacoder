#!/usr/bin/env python3
"""Apply V14 systemic JSON-safety and raw-argument preservation patches."""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


agent_path = Path("python/navixmind/agent.py")
agent = agent_path.read_text()
if "RASTACODER_V14_JSON_BOUNDARY" not in agent:
    agent = replace_once(
        agent,
        "from .crash_logger import CrashLogger\n",
        "from .crash_logger import CrashLogger\nfrom .json_contract import to_json_safe, json_dumps_safe\n# RASTACODER_V14_JSON_BOUNDARY\n",
        "agent import",
    )

    agent = agent.replace("'messages_json': json.dumps(openai_messages),", "'messages_json': json_dumps_safe(openai_messages),")
    agent = agent.replace("args['tools_json'] = json.dumps(openai_tools)", "args['tools_json'] = json_dumps_safe(openai_tools)")
    agent = agent.replace(
        "json.dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)",
        "json_dumps_safe({'name': raw_name, 'arguments': raw_input})",
    )
    agent = agent.replace(
        "call_json = json.dumps({\n                                \"name\": block.get('name', ''),\n                                \"arguments\": block.get('input', {})\n                            })",
        "call_json = json_dumps_safe({\n                                \"name\": block.get('name', ''),\n                                \"arguments\": block.get('input', {})\n                            })",
    )
    agent = agent.replace(
        "'arguments': json.dumps(block.get('input') or {}, ensure_ascii=False),",
        "'arguments': json_dumps_safe(block.get('input') or {}),",
    )
    agent = agent.replace(
        "'_raw_source': json.dumps(call, ensure_ascii=False)[:1500],",
        "'_raw_source': json_dumps_safe(call)[:1500],",
    )

    # Keep the raw pre-normalization tree immutable. Several compatibility
    # transforms are intentionally nested; a shallow copy can corrupt the
    # diagnostic/source representation for later retries.
    agent = replace_once(
        agent,
        "raw_input = _coerce_tool_args(block.get('input', {}))\n                name, tool_input, parser_repairs = normalize_tool_call(raw_name, raw_input)",
        "raw_input = to_json_safe(_coerce_tool_args(block.get('input', {})))\n                raw_input_for_diag = to_json_safe(raw_input)\n                name, tool_input, parser_repairs = normalize_tool_call(raw_name, raw_input)\n                tool_input = to_json_safe(tool_input)",
        "structured raw input",
    )
    agent = agent.replace("block['_raw_input'] = raw_input\n", "block['_raw_input'] = raw_input_for_diag\n", 1)

    # JSON-RPC process_query may contain arbitrary nested tool outputs or
    # diagnostics. The outermost bridge boundary must also be strict-safe.
    agent = replace_once(
        agent,
        "            return json.dumps({\n                \"jsonrpc\": \"2.0\",\n                \"id\": request_id,\n                \"result\": result\n            })",
        "            return json_dumps_safe({\n                \"jsonrpc\": \"2.0\",\n                \"id\": request_id,\n                \"result\": result\n            })",
        "process_query jsonrpc boundary",
    )

    agent = replace_once(
        agent,
        "    if isinstance(value, list):\n        return [_diag_safe(v) for v in value[:50]]\n",
        "    if isinstance(value, (list, tuple)):\n        return [_diag_safe(v) for v in list(value)[:50]]\n    if isinstance(value, (set, frozenset)):\n        return [_diag_safe(v) for v in to_json_safe(value)[:50]]\n",
        "agent diagnostics collections",
    )
    agent = agent.replace("return json.dumps(safe, ensure_ascii=False, indent=2)", "return json_dumps_safe(safe, indent=2)")

    # Tool execution boundary: every one of the 37 functions receives a
    # JSON-safe argument tree and returns a JSON-safe result tree before any
    # logging, diagnostics, model-prefill or bridge serialization occurs.
    agent = replace_once(
        agent,
        "                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)\n                    if is_offline:",
        "                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)\n                    tool_input = to_json_safe(tool_input)\n                    if is_offline:",
        "process tool input boundary",
    )
    agent = replace_once(
        agent,
        "                        result = execute_tool(tool_name, tool_input, context)\n                        # Truncate large results\n                        result_str = json.dumps(result) if isinstance(result, dict) else str(result)",
        "                        result = to_json_safe(execute_tool(tool_name, tool_input, context))\n                        # Serialize only through the canonical strict JSON boundary.\n                        result_str = json_dumps_safe(result) if isinstance(result, (dict, list)) else str(result)",
        "tool result serialization",
    )
    agent = agent.replace("params_str = json.dumps(params) if params else ''", "params_str = json_dumps_safe(params) if params else ''")

    # Feeders that previously relied on default=str now preserve collection
    # shape instead of turning a set into an opaque string representation.
    agent = agent.replace("json.dumps(result, ensure_ascii=False, default=str)", "json_dumps_safe(result)")
    agent = agent.replace("json.dumps(value, ensure_ascii=False, default=str)", "json_dumps_safe(value)")
    agent = agent.replace("json.dumps(metadata, ensure_ascii=False, default=str)", "json_dumps_safe(metadata)")

    agent_path.write_text(agent)


tools_path = Path("python/navixmind/tools/__init__.py")
tools = tools_path.read_text()
if "RASTACODER_V14_JSON_BOUNDARY" not in tools:
    tools = replace_once(
        tools,
        "from ..bridge import ToolError, get_bridge\n",
        "from ..bridge import ToolError, get_bridge\nfrom ..json_contract import to_json_safe\n# RASTACODER_V14_JSON_BOUNDARY\n",
        "tools import",
    )
    tools = replace_once(
        tools,
        "    tool_name, args, compatibility_notes = normalize_tool_call(tool_name, args, context=context)\n    bridge = get_bridge()",
        "    tool_name, args, compatibility_notes = normalize_tool_call(tool_name, args, context=context)\n    args = to_json_safe(args)\n    bridge = get_bridge()",
        "executor input boundary",
    )
    tools = replace_once(
        tools,
        "    if isinstance(value, list):\n        return [_safe_diag_value(v) for v in value[:50]]\n",
        "    if isinstance(value, (list, tuple)):\n        return [_safe_diag_value(v) for v in list(value)[:50]]\n    if isinstance(value, (set, frozenset)):\n        return [_safe_diag_value(v) for v in to_json_safe(value)[:50]]\n",
        "tool diagnostic collections",
    )
    tools = replace_once(
        tools,
        "    result = tool_func(**args)\n    return _verify_tool_result(tool_name, args, result)",
        "    result = to_json_safe(tool_func(**args))\n    return to_json_safe(_verify_tool_result(tool_name, args, result))",
        "executor output boundary",
    )
    tools_path.write_text(tools)


compat_path = Path("python/navixmind/tools/compat.py")
compat = compat_path.read_text()
if "RASTACODER_V14_DEEP_ARGUMENT_COPY" not in compat:
    compat = replace_once(
        compat,
        "import os\nimport re\n",
        "import copy\nimport os\nimport re\n# RASTACODER_V14_DEEP_ARGUMENT_COPY\n",
        "compat copy import",
    )
    compat = replace_once(
        compat,
        "    if isinstance(raw_args, dict):\n        args = dict(raw_args)",
        "    if isinstance(raw_args, dict):\n        args = copy.deepcopy(raw_args)",
        "compat deep copy",
    )
    compat_path.write_text(compat)

print("Applied V14 systemic JSON boundary patches")

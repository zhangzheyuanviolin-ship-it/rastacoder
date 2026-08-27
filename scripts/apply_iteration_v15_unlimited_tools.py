from pathlib import Path

ROOT = Path('.')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_once(path, old, new):
    text = read(path)
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'V15 anchor not found in {path}: {old[:140]!r}')
    write(path, text.replace(old, new, 1))


# Zero is the explicit sentinel for unlimited tool calls. In this mode the
# tool-driven ReAct loop also bypasses max_iterations, otherwise a hidden step
# ceiling would still terminate long cloud-agent tasks.
replace_once(
    'python/navixmind/agent.py',
    '''    max_iterations = context.get('max_iterations', DEFAULT_MAX_ITERATIONS)\n    max_tool_calls = context.get('max_tool_calls', DEFAULT_MAX_TOOL_CALLS)\n    max_tokens = context.get('max_tokens', DEFAULT_MAX_TOKENS)''',
    '''    max_iterations = max(1, int(context.get('max_iterations', DEFAULT_MAX_ITERATIONS)))\n    max_tool_calls = int(context.get('max_tool_calls', DEFAULT_MAX_TOOL_CALLS))\n    unlimited_tool_calls = max_tool_calls <= 0\n    max_tokens = context.get('max_tokens', DEFAULT_MAX_TOKENS)''',
)
replace_once(
    'python/navixmind/agent.py',
    '''    while iteration < max_iterations:\n        iteration += 1\n        bridge.log(f"Thinking... (step {iteration}/{max_iterations})", progress=iteration / max_iterations * 0.5)''',
    '''    while unlimited_tool_calls or iteration < max_iterations:\n        iteration += 1\n        if unlimited_tool_calls:\n            bridge.log(f"Thinking... (step {iteration}, unlimited tool mode)")\n        else:\n            bridge.log(f"Thinking... (step {iteration}/{max_iterations})", progress=iteration / max_iterations * 0.5)''',
)
replace_once(
    'python/navixmind/agent.py',
    '                    if tool_call_count > max_tool_calls:',
    '                    if not unlimited_tool_calls and tool_call_count > max_tool_calls:',
)
replace_once(
    'python/navixmind/agent.py',
    '''                    bridge.log(f"Tool: {tool_name} - {input_summary}", progress=0.5 + (iteration / max_iterations * 0.3))''',
    '''                    bridge.log(\n                        f"Tool: {tool_name} - {input_summary}",\n                        progress=None if unlimited_tool_calls else 0.5 + (iteration / max_iterations * 0.3),\n                    )''',
)

replace_once(
    'lib/core/services/storage_service.dart',
    '''  /// Set max tool calls per query\n  Future<void> setMaxToolCalls(int calls) async {''',
    '''  /// Set max tool calls per query. Zero means unlimited.\n  Future<void> setMaxToolCalls(int calls) async {''',
)
replace_once(
    'lib/core/services/storage_service.dart',
    '  /// Get max tool calls per query (default: 50)',
    '  /// Get max tool calls per query (default: 50; zero means unlimited)',
)
replace_once(
    'lib/features/settings/settings_screen.dart',
    '''            subtitle: '$_maxToolCalls — 达到该工具执行次数后停止',''',
    '''            subtitle: _maxToolCalls == 0\n                ? '不限次数 — 不限制本轮工具调用与工具驱动步骤'\n                : '$_maxToolCalls — 达到该工具执行次数后停止',''',
)
replace_once(
    'lib/features/settings/settings_screen.dart',
    '''              items: const [\n                DropdownMenuItem(value: 15, child: Text('15')),\n                DropdownMenuItem(value: 25, child: Text('25')),\n                DropdownMenuItem(value: 50, child: Text('50')),\n                DropdownMenuItem(value: 100, child: Text('100')),\n              ],\n              onChanged: (value) async {\n                if (value != null) {\n                  await StorageService.instance.setMaxToolCalls(value);''',
    '''              items: const [\n                DropdownMenuItem(value: 0, child: Text('不限次数')),\n                DropdownMenuItem(value: 15, child: Text('15')),\n                DropdownMenuItem(value: 25, child: Text('25')),\n                DropdownMenuItem(value: 50, child: Text('50')),\n                DropdownMenuItem(value: 100, child: Text('100')),\n              ],\n              onChanged: (value) async {\n                if (value != null) {\n                  await StorageService.instance.setMaxToolCalls(value);''',
)

print('V15 unlimited-tools patch applied.')

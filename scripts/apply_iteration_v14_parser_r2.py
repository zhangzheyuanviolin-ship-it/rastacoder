from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
agent_path = ROOT / 'python/navixmind/agent.py'
agent = agent_path.read_text(encoding='utf-8')


def once(text, old, new, label):
    if new in text:
        print(label + ': already applied')
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, found {count}')
    print(label + ': applied')
    return text.replace(old, new, 1)

if 'RASTACODER_V14_ORDERED_JSONISH_PARSER' not in agent:
    pattern = re.compile(
        r'def _parse_mapping\(text: str\) -> Optional\[dict\]:[\s\S]*?\n\ndef _coerce_tool_args\(value: Any\) -> dict:'
    )
    match = pattern.search(agent)
    if not match:
        raise SystemExit('ordered parser: function range not found')
    replacement = r'''# RASTACODER_V14_ORDERED_JSONISH_PARSER
def _ordered_literal_eval(text: str) -> Any:
    """Literal-eval JSON-ish model output while preserving brace-item source order."""
    import ast

    def walk(node):
        if isinstance(node, ast.Dict):
            return {walk(k): walk(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.List):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Tuple):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Set):
            # Qwen-class small models sometimes use {a,b,c} where the schema
            # requires [a,b,c]. Preserve lexical order instead of creating a
            # Python set whose iteration order would scramble spreadsheet rows.
            return [walk(v) for v in node.elts]
        return ast.literal_eval(node)

    return walk(ast.parse(text, mode='eval').body)


def _parse_mapping(text: str) -> Optional[dict]:
    """Parse JSON-like tool call objects without executing model text."""
    import re

    value = text.strip()
    candidates = [value, re.sub(r',\s*([}\]])', r'\1', value)]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    try:
        parsed = _ordered_literal_eval(value)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError, TypeError):
        pass
    return None


def _missing_json_value_keys(text: str) -> List[str]:
    """Return quoted object keys emitted without a ': value' payload."""
    keys: List[str] = []
    pattern = re.compile(r'(?P<prefix>[,{]\s*)"(?P<key>(?:\\.|[^"\\])*)"\s*(?=,|})')
    for match in pattern.finditer(str(text or '')):
        key = match.group('key').strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _coerce_tool_args(value: Any) -> dict:'''
    agent = agent[:match.start()] + replacement + agent[match.end():]

old_try = '''def _try_parse_tool_json(json_str: str, index: int) -> Optional[dict]:
    """Parse common JSON/dict function-call variants into a tool_use block."""
    call_data = _parse_mapping(json_str)
    if not call_data:
        return None
'''
new_try = '''def _try_parse_tool_json(json_str: str, index: int) -> Optional[dict]:
    """Parse common JSON/dict function-call variants into a tool_use block."""
    # A quoted key with no colon/value means the model omitted semantic content.
    # Reject it into the bounded format-repair path; never silently execute null.
    if _missing_json_value_keys(json_str):
        return None
    call_data = _parse_mapping(json_str)
    if not call_data:
        return None
'''
agent = once(agent, old_try, new_try, 'reject missing-value tool JSON')

old_retry = '''                        '[Tool call format error] The previous tool call was not executable. '
                        'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
'''
new_retry = '''                        '[Tool call format error] The previous tool call was not executable. '
                        + (
                            'The previous JSON contained argument key(s) with no value: '
                            + ', '.join(_missing_json_value_keys(raw_bad))
                            + '. Every included key must have a colon and a real JSON value. '
                            'Omit optional keys you do not need. For content/text/body, provide the complete requested text. '
                            if _missing_json_value_keys(raw_bad) else ''
                        )
                        + 'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
'''
agent = once(agent, old_retry, new_retry, 'precise parser retry guidance')

# Use the V14 JSON-safe boundary consistently in tool-result prefills as well.
for old, new in (
    ('json.dumps(result, ensure_ascii=False, default=str)', '_json_boundary_dumps(result, ensure_ascii=False)'),
    ('json.dumps(meta, ensure_ascii=False, default=str)', '_json_boundary_dumps(meta, ensure_ascii=False)'),
    ('json.dumps(value, ensure_ascii=False, default=str)', '_json_boundary_dumps(value, ensure_ascii=False)'),
    ('json.dumps(metadata, ensure_ascii=False, default=str)', '_json_boundary_dumps(metadata, ensure_ascii=False)'),
):
    agent = agent.replace(old, new)

agent_path.write_text(agent, encoding='utf-8')
print('V14 parser R2 applied: ordered brace-arrays, missing-value rejection, precise bounded repair.')

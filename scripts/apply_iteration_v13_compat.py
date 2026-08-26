from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "python/navixmind/tools/compat.py"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if new in text:
        print(f"{label}: already applied")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    text = text.replace(old, new, 1)
    print(f"{label}: applied")


anchor = '''def normalize_tool_call(
    tool_name: Any,
    raw_args: Any,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], List[str]]:
'''
block = '''# RASTACODER_V13_SCHEMA_AWARE_COERCION
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


''' + anchor
replace_once(anchor, block, "schema-aware coercion helpers")

replace_once(
    '''    # Generic free-form keys are compatibility scaffolding, never canonical
    # tool arguments. Remove them after extracting deterministic information.
''',
    '''    # Apply schema-aware primitive/enum coercion after tool-specific alias
    # routing but before strict executor validation.
    _coerce_contract_values(name, args, notes)

    # Generic free-form keys are compatibility scaffolding, never canonical
    # tool arguments. Remove them after extracting deterministic information.
''',
    "invoke schema-aware coercion",
)

path.write_text(text, encoding="utf-8")
print("V13 compatibility coercion patch applied.")

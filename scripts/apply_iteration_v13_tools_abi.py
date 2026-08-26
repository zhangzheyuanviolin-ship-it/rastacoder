from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "python/navixmind/tools/__init__.py"
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


replace_once(
    "from typing import Any, Dict\nfrom pathlib import Path\n",
    "from typing import Any, Dict\nfrom pathlib import Path\nimport copy\n",
    "import copy",
)

replace_once(
    '    "read_docx": "read_docx(docx_path, extract)",\n'
    '    "modify_docx": "modify_docx(input_path, output_path, operations)",\n'
    '    "create_pptx": "create_pptx(output_path, title, slides)",\n'
    '    "read_pptx": "read_pptx(pptx_path, extract)",\n'
    '    "modify_pptx": "modify_pptx(input_path, output_path, operations)",\n'
    '    "create_xlsx": "create_xlsx(output_path, sheets)",\n'
    '    "read_xlsx": "read_xlsx(xlsx_path, sheet, range, extract)",\n',
    '    "read_docx": "read_docx(docx_path) ; ordinary reads need only the file path",\n'
    '    "modify_docx": "modify_docx(input_path, output_path, operations)",\n'
    '    "create_pptx": "create_pptx(output_path, title, slides)",\n'
    '    "read_pptx": "read_pptx(pptx_path) ; ordinary reads need only the file path",\n'
    '    "modify_pptx": "modify_pptx(input_path, output_path, operations)",\n'
    '    "create_xlsx": "create_xlsx(output_path, sheets)",\n'
    '    "read_xlsx": "read_xlsx(xlsx_path, sheet, range) ; omit sheet/range for the whole workbook",\n',
    "document hints",
)

anchor = '''def _offline_tool_names():
    return {tool["name"] for tool in OFFLINE_TOOLS_SCHEMA}


def get_enabled_tool_names(skill_ids=None):
'''
block = '''# RASTACODER_V13_SMALL_MODEL_TOOL_ABI
# Strict executor/cloud schemas remain unchanged. Local 3B-4B models receive a
# deep-copied projection which hides deterministic app-defaultable selectors.
_LOCAL_MODEL_HIDDEN_ARGS = {
    "read_docx": {"extract"},
    "read_pptx": {"extract"},
    "read_xlsx": {"extract"},
    "web_fetch": {"extract_mode"},
}


def get_local_tool_argument_classes():
    # Classify every local schema property for audit/fuzz coverage.
    result = {}
    for tool in OFFLINE_TOOLS_SCHEMA:
        schema = tool.get("input_schema") or {}
        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        hidden = set(_LOCAL_MODEL_HIDDEN_ARGS.get(tool.get("name"), set()))
        classes = {}
        for key, spec in props.items():
            if key in required:
                classes[key] = "model_essential"
            elif key in hidden or (isinstance(spec, dict) and "default" in spec):
                classes[key] = "app_defaultable"
            else:
                classes[key] = "advanced_optional"
        result[str(tool.get("name"))] = classes
    return result


def _project_tool_for_local_model(tool):
    projected = copy.deepcopy(tool)
    name = str(projected.get("name") or "")
    schema = projected.get("input_schema") or {}
    props = schema.get("properties") or {}
    for key in _LOCAL_MODEL_HIDDEN_ARGS.get(name, set()):
        props.pop(key, None)
        required = schema.get("required")
        if isinstance(required, list) and key in required:
            required.remove(key)
    if name == "read_docx":
        projected["description"] = (
            "Read a DOCX file. Give only docx_path for an ordinary full read; "
            "the app chooses safe extraction defaults."
        )
    elif name == "read_pptx":
        projected["description"] = (
            "Read a PPTX file. Give only pptx_path for an ordinary full read; "
            "the app chooses safe extraction defaults."
        )
    elif name == "read_xlsx":
        projected["description"] = (
            "Read an XLSX workbook. Give xlsx_path; sheet/range are optional targeting controls."
        )
    elif name == "web_fetch":
        projected["description"] = "Fetch the readable text of a webpage. Give the URL."
    return projected


def _offline_tool_names():
    return {tool["name"] for tool in OFFLINE_TOOLS_SCHEMA}


def get_enabled_tool_names(skill_ids=None):
'''
replace_once(anchor, block, "ABI projection helpers")

replace_once(
    '''def get_offline_tools_for_skills(skill_ids=None):
    enabled = get_enabled_tool_names(skill_ids)
    return [tool for tool in OFFLINE_TOOLS_SCHEMA if tool["name"] in enabled]
''',
    '''def get_offline_tools_for_skills(skill_ids=None):
    enabled = get_enabled_tool_names(skill_ids)
    return [
        _project_tool_for_local_model(tool)
        for tool in OFFLINE_TOOLS_SCHEMA
        if tool["name"] in enabled
    ]
''',
    "project local tool schemas",
)

path.write_text(text, encoding="utf-8")
print("V13 tools ABI patch applied.")

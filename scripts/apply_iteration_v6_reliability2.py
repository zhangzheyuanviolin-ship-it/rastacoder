#!/usr/bin/env python3
"""Second-pass reliability hardening after the core v6 patch.

Generalizes the user's TXT/Word failure class: a small model may emit a Skill
name plus one generic natural-language `param` instead of exact function args.
This patch safely recovers creation content/output names for text/DOCX/PDF.
"""
from pathlib import Path

p = Path('python/navixmind/tools/compat.py')
text = p.read_text(encoding='utf-8')

anchor = '''def _apply_freeform(name: str, args: Dict[str, Any], free: str, notes: List[str]) -> None:
'''
helper = r'''
def _creation_content_from_freeform(text: str, files: List[str]) -> str:
    """Extract requested document text from common one-line small-model calls."""
    value = text.strip()
    if not value:
        return ""
    patterns = (
        r"""(?:content|text|body)\s*[:=]\s*[\"']?([\s\S]+?)[\"']?$""",
        r"""(?:saying|containing|with\s+content)\s+[\"']?([\s\S]+?)[\"']?$""",
        r"""\bwrite\s+[\"']?([\s\S]+?)[\"']?\s+(?:to|into)\s+[\"']?[^\"']+\.[A-Za-z0-9]{1,6}[\"']?\s*$""",
        r"""(?:内容为|内容是|写入内容|正文为|正文是)\s*[：:]?\s*[“”\"']?([\s\S]+?)[“”\"']?\s*$""",
    )
    for pattern in patterns:
        m = re.search(pattern, value, flags=re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip().strip("\"'“”")

    # Conservative fallback: remove an obvious leading creation verb and an
    # obvious trailing destination filename. This is used only for creation
    # tools, so it cannot overwrite/read an input file.
    cleaned = re.sub(
        r"""^(?:please\s+)?(?:write|create|save|make)\s+(?:a\s+)?(?:txt|text|word|docx|pdf)?\s*(?:file|document)?\s*[:：-]?\s*""",
        '', value, flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"""\s+(?:to|into|as)\s+[\"']?[^\"']+\.[A-Za-z0-9]{1,6}[\"']?\s*$""",
        '', cleaned, flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"""^(?:写入|创建|新建|保存)(?:一个|一份)?(?:TXT|txt|文本|Word|word|DOCX|docx|PDF|pdf)?(?:文件|文档)?\s*[：:]?\s*""",
        '', cleaned,
    ).strip()
    for file_name in files:
        if cleaned == file_name:
            return ""
    return cleaned.strip("\"'“”")

'''
if helper.strip() not in text:
    text = text.replace(anchor, helper + anchor, 1)

old = '''    if name == "python_execute" and "code" not in args:
        args["code"] = free
        notes.append("param->code")

    if name == "convert_document":
'''
new = '''    if name == "python_execute" and "code" not in args:
        args["code"] = free
        notes.append("param->code")

    # Creation tools may receive the whole user intent inside one generic
    # `param`. Recover output filenames and requested body text deterministically.
    if name in {"write_file", "create_docx", "create_pdf"}:
        desired_ext = {"write_file": "txt", "create_docx": "docx", "create_pdf": "pdf"}[name]
        matching = [f for f in files if _extension(f) == desired_ext]
        if matching and "output_path" not in args:
            args["output_path"] = matching[-1]
            notes.append("freeform->output_path")
        if "content" not in args:
            recovered = _creation_content_from_freeform(free, files)
            if recovered:
                args["content"] = recovered
                notes.append("freeform->content")

    if name == "convert_document":
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f'Expected one creation freeform insertion anchor, found {count}')
text = text.replace(old, new, 1)

p.write_text(text, encoding='utf-8')
print('Applied generalized v6 free-form creation recovery')

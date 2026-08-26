from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "python/navixmind/agent.py"
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


anchor = '''def _tool_error_for_model(tool_name: str, error: Any) -> str:
'''
block = r'''# RASTACODER_V13_DOCUMENT_INGESTION
_DOCUMENT_READ_TOOLS = {"read_file", "read_pdf", "read_docx", "read_pptx", "read_xlsx"}


def _document_primary_text(result: Any) -> str:
    if not isinstance(result, dict):
        return str(result or "")
    for key in ("content", "text"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value
    for key in ("sheets", "data", "slides", "tables", "notes"):
        value = result.get(key)
        if value not in (None, "", [], {}):
            try:
                return json.dumps(value, ensure_ascii=False, default=str)
            except Exception:
                return str(value)
    return ""


def _split_complete_document_text(text: str, chunk_chars: int = 7000) -> List[str]:
    value = str(text or "")
    size = max(1200, int(chunk_chars))
    return [value[i:i + size] for i in range(0, len(value), size)] or [""]


def _document_result_for_local_model(
    client: Any,
    user_query: str,
    tool_name: str,
    result: Any,
    context: Dict[str, Any],
    max_output_tokens: int,
) -> str:
    # Map-reduce large document text with the same downloaded local model.
    source_text = _document_primary_text(result)
    budget = _tool_result_char_budget(context, max_output_tokens)
    if not source_text or len(source_text) <= budget:
        return _prepare_tool_result_for_model(
            tool_name, result, context, max_output_tokens
        )

    chunks = _split_complete_document_text(source_text)
    helper = LocalLLMClient(
        model_id=str(getattr(client, "model_id", getattr(client, "model", ""))),
        temperature=0.2,
        top_p=0.9,
        thinking_mode="disabled",
    )
    note_cap = max(420, min(1200, (budget - 900) // max(1, len(chunks))))
    notes: List[str] = []
    failures = 0
    source_query = str(user_query or "").strip()[:2400]
    helper_system = (
        "You are an internal document-ingestion helper. Read the supplied chunk "
        "and return compact evidence notes for the original user request. Preserve "
        "relevant names, numbers, dates, claims, qualifications, structure and uncertainty. "
        "Do not call tools. Do not output JSON or XML. Do not answer the user directly."
    )

    for index, chunk in enumerate(chunks, 1):
        prompt = (
            f"ORIGINAL USER REQUEST:\n{source_query}\n\n"
            f"DOCUMENT CHUNK {index}/{len(chunks)}:\n{chunk}\n\n"
            f"Return evidence notes for this chunk only, at most {note_cap} characters."
        )
        note = ""
        try:
            response = helper.create_message(
                messages=[{"role": "user", "content": prompt}],
                system=helper_system,
                tools=None,
                max_tokens=max(256, min(640, int(max_output_tokens))),
                retry_count=1,
            )
            blocks = _strip_reasoning_from_blocks(response.get("content", []))
            note = _extract_text_content(blocks).strip()
        except Exception as exc:
            failures += 1
            context.setdefault("_diagnostics", []).append({
                "stage": "document_ingestion_chunk_error",
                "tool": tool_name,
                "chunk": index,
                "chunks": len(chunks),
                "error": str(exc)[:1200],
            })

        if not note:
            head = max(180, note_cap // 2)
            tail = max(120, note_cap - head - 40)
            note = chunk[:head]
            if len(chunk) > head:
                note += "\n...[chunk fallback]...\n" + chunk[-tail:]
        note, _ = _trim_model_text(note, note_cap)
        notes.append(f"[chunk {index}/{len(chunks)}]\n{note}")

    metadata = {}
    if isinstance(result, dict):
        for key, value in result.items():
            if (
                key not in {"content", "text", "slides", "tables", "notes", "sheets", "data"}
                and isinstance(value, (str, int, float, bool, type(None)))
            ):
                metadata[key] = value

    digest = "\n\n".join(notes)
    payload = (
        "DOCUMENT_INGESTION\n"
        f"tool: {tool_name}\n"
        f"source_chars: {len(source_text)}\n"
        f"chunks_processed: {len(chunks)}\n"
        f"chunk_failures: {failures}\n"
        "coverage: complete executor-returned text was partitioned across all chunks\n"
        f"metadata: {json.dumps(metadata, ensure_ascii=False, default=str)}\n"
        "evidence_digest:\n"
        f"{digest}"
    )
    payload, _ = _trim_model_text(payload, budget)
    context.setdefault("_diagnostics", []).append({
        "stage": "document_ingestion_complete",
        "tool": tool_name,
        "source_chars": len(source_text),
        "chunks": len(chunks),
        "chunk_failures": failures,
        "digest_chars": len(payload),
    })
    return (
        f"TOOL_RESULT\ntool: {tool_name}\nstatus: succeeded\npayload:\n{payload}\n\n"
        "NEXT_ACTION: Answer the original user request from the evidence digest. "
        "The digest covers every source chunk. Do not request the same document again "
        "unless the user explicitly asks for a different extraction."
    )


''' + anchor
replace_once(anchor, block, "document ingestion helpers")

replace_once(
    '''                        model_result = (
                            _prepare_tool_result_for_model(tool_name, result, context, max_tokens)
                            if (is_offline or is_openai_compatible) else result_str
                        )
''',
    '''                        if is_offline and tool_name in _DOCUMENT_READ_TOOLS:
                            model_result = _document_result_for_local_model(
                                client, user_query, tool_name, result, context, max_tokens
                            )
                        else:
                            model_result = (
                                _prepare_tool_result_for_model(tool_name, result, context, max_tokens)
                                if (is_offline or is_openai_compatible) else result_str
                            )
''',
    "route document reads through ingestion",
)

path.write_text(text, encoding="utf-8")
print("V13 document ingestion patch applied.")

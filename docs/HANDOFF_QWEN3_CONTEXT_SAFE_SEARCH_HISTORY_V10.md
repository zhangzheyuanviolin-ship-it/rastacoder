# RastaCoder Qwen3 Context-Safe Search + History v10 — verified release handoff

Current branch: `iteration/qwen3-context-safe-search-history-v10`
Release tag: `qwen3-context-safe-search-history-v10`
Version: `0.0.9` / code `23`

## V10 fixes
- Local tool results now pass through a context-aware model payload budget before MLC prefill. At 8192 context with 2048 output reservation, the tool payload is kept to a compact safe range instead of injecting raw multi-kilobyte JSON.
- AnySearch, Exa, LangSearch and Tavily results use one normalized model-facing search format that prioritizes title, URL, publication date, provider answer and summary. Full page text is only used as a fallback excerpt when summary/snippet data is absent.
- The exact reported Exa pattern (five results, raw payload above 7900 chars, 8192 context) is a release gate.
- Generic long-result tools such as read_file/read_docx/read_pdf/web_fetch share the same context-safety layer and explicit truncation note.
- Local max_tokens recovery is bounded to one tool-free final-answer continuation. A second max_tokens returns the accumulated answer instead of consuming the 50-step loop.
- Tool failures now carry explicit model recovery policy for missing credentials, 401/403, 429, argument errors, timeout/network failures and unknown failures, preventing blind identical retries.
- Conversation history rows expose a dedicated accessible open-conversation action; the rename/delete menu is a separate sibling control so screen-reader activation does not land on the management menu.
- The optional OpenAI-compatible cloud-provider endpoint was deliberately deferred to keep this release focused on local tool reliability.

## Inherited capability invariant
- 25 manually controlled Skills / exactly 37 canonical local functions.
- All V9 systemic postcondition, search-parameter isolation, Office mutation and media gates remain green.

## Final verification
- Package: `ai.navixmind`
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `b98a071c579e8ad637f0b6241e211a3a9811d7a36a8fa0261eca5e887e29a144`
- APK size: `517014408` bytes

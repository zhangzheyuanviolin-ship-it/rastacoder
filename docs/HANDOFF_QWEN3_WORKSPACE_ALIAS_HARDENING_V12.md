# RastaCoder Qwen3 Workspace Alias Hardening v12 — verified release handoff

Branch: `iteration/qwen3-workspace-alias-hardening-v12`
Release tag: `qwen3-workspace-alias-hardening-v12`
Version: `0.0.11` / code `25`
Package: `ai.navixmind`

## Triggering real-device failure
Local Qwen3-4B called `list_files(path="/workspace")`; V11 left the path unchanged, attempted literal Android/Linux `/workspace`, failed with `Directory not found or inaccessible: /workspace`, and the model ended the turn.

## Confirmed V11 causes
1. Compatibility aliases omitted `/workspace` and `/output`.
2. Global workspace resolver returned all absolute paths unchanged before virtual-workspace interpretation.
3. Lower extended file-tool resolver repeated that absolute-path bypass.
4. Directory-not-found recovery guidance did not tell the local model to retry workspace root with `path='.'`.
5. Successful list results exposed physical workspace paths back to the model, risking multi-step path drift.

## V12 architecture
- New `python/navixmind/tools/path_contract.py` centralizes the logical model namespace.
- Canonical workspace root is `.`.
- Defensive aliases include `workspace`, `output`, `/workspace`, `/output` and nested forms.
- Logical Android roots remain `downloads`, `documents`, `pictures`, `screenshots`, `camera`.
- Trusted uploaded-file absolute paths remain usable; traversal outside selected logical roots is rejected.
- `list_files` keeps its logical input through the executor boundary and performs physical resolution internally with the configured workspace root.
- Model-facing list payloads expose logical paths only and never the private physical workspace root.
- The local prompt/schema explicitly tells Qwen3-4B to use `path='.'` for workspace root.
- Workspace/list errors explicitly instruct one corrected `list_files(path='.')` retry instead of asking the user to reattach a workspace directory.
- V11 OpenAI-compatible Chat Completions provider is preserved unchanged for cloud-vs-local A/B testing.

## Validation history
- First V12 no-APK preflight: run `32966081018`. It correctly failed only the new V12 gate after V9/V10/V11 were green, catching one residual physical `requested_path` leak before any APK build.
- Precise boundary fix marker: `RASTACODER_V12_PRESERVE_LIST_LOGICAL_PATH`.
- Second V12 no-APK preflight: run `32966400251`, fully green including V9/V10/V11/V12 gates and Flutter static analysis.
- Formal release repeats V9/V10/V11/V12 gates before and after APK build.

## Inherited invariants
- 25 manually controlled Skills / exactly 37 canonical local functions.
- V9 Office/media/search/postcondition hardening remains green.
- V10 context-safe tool-result and bounded local continuation behavior remains green.
- V11 accessible history fixes and OpenAI-compatible provider remain green.

## Final verified artifact
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `6e62ec683e575ddb5cb78b4ee6883e600cf9d2a38616f26c6c277e483ddd0626`
- APK size: `517027536` bytes

## Post-release real-device findings — 2026-08-26

V12 fixed the workspace-listing failure on the user's real device. Subsequent basic document/cloud tests exposed a broader architectural problem that supersedes patch-by-patch tool fixes.

### DOCX

Qwen3-4B first emitted `read_docx(..., extract=true)` and hit the enum contract (`text|tables|all`). It then self-corrected to `extract=text`; the tool successfully extracted 45,015 characters. The Agent subsequently hit consecutive local max-output limits and produced no usable final answer.

### PPTX

Qwen3-4B first emitted `read_pptx(..., extract=True)` and hit the enum contract (`text|slides|notes|all`). It then self-corrected to `extract=text`; the tool successfully extracted 6,979 characters. The supplied log ends at the following `llm_generate`; the user reports the basic task did not complete normally.

### PDF

No exact PDF device failure has been supplied yet. It must be tested as part of the same document-ingestion family in the next architecture pass.

### OpenAI Compatible

After configuring and selecting `OpenAI Compatible`, sending is blocked by the Flutter chat screen's generic cloud readiness gate, which still requires a Claude API key. The bridge/Python OpenAI-compatible configuration exists, but the UI prevents the request from reaching it. This is a confirmed deterministic routing bug and exposes a missing end-to-end provider test.

### Strategic conclusion

The parsers demonstrably work on the supplied DOCX/PPTX files, and Qwen3-4B can select and retry canonical tools. Current failures point to the model-facing Tool ABI, long-result ingestion/orchestration, provider routing, and insufficient end-to-end validation. The next iteration must audit all 37 canonical functions systematically instead of adding one-off repairs per tool.

**Mandatory next-context document:**

`docs/NEXT_CONTEXT_V13_SYSTEMIC_TOOL_ABI_AUDIT_HANDOFF.md`

It contains the exact device logs, upstream-first findings, systemic diagnosis, required V13 architecture, 37-function contract-fuzz direction, document-ingestion redesign, explicit provider-routing plan, golden-path acceptance suite, and release discipline. Read it before any V13 code change or build.

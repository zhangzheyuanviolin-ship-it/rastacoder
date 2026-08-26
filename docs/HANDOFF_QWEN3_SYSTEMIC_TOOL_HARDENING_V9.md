# RastaCoder Qwen3 Systemic Tool Hardening v9 — verified release handoff

Current branch: `iteration/qwen3-systemic-tool-hardening-v9`
Release tag: `qwen3-systemic-tool-hardening-v9`
Version: `0.0.8` / code `22`

## V9 real-device feedback generalized into systemic fixes
- FFmpeg now has a canonical structured `speed` operation. Common aliases such as tempo/playback_speed/speed_up normalize to speed, and scalar params such as `"1.5"` normalize to `params.factor=1.5`.
- Native audio/video speed processing verifies a real non-empty output and compares output duration against the requested speed factor when probe metadata is available.
- AnySearch, Exa, LangSearch and Tavily search functions expose only `query` to the local model. Result count, provider search type/topic, freshness/depth, date/domain filters and content options are user-configured per Skill and privately merged at execution.
- Compatibility recovery preserves correct `query` and repairs common Qwen3-4B variants such as q/keyword/search_query and the observed Exa `topic=<actual keywords>` failure.
- DOCX/PPTX/XLSX edits default to the existing file when no explicit destination is requested. They save transactionally through a temp sibling, reopen the saved artifact, and reject zero-effect/invalid operations instead of reporting success.
- A central postcondition layer verifies every file-producing tool result: output must physically exist, be non-empty, and structured files (ZIP/PDF/DOCX/PPTX/XLSX/images) must reopen successfully. Text writes are read back byte-for-text equivalence at UTF-8 string level.
- Media download no longer references an undefined fallback headers variable and rejects empty downloads.

## Capability invariant
- 25 manually controlled Skills.
- 37 canonical local functions with exact schema/Skill coverage equality.
- Search credentials and provider tuning remain execution-context data and are absent from model-visible arguments.

## Verification
- Exact user cases are automated: MP3 1.5x speed call normalization; Exa topic-as-query recovery; DOCX physical end-paragraph append.
- Generalized gates cover PPTX missing-shape no-op rejection, XLSX missing-sheet no-op rejection, in-place Office persistence, search-parameter isolation, empty/mismatched output rejection, media header fallback, and Flutter Analyze.
- Final package: `ai.navixmind`
- Final ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `96edf62465b3c958a78319f3913f97acd7de7667108ae003211e30d912caaf14`
- APK size: `517004168` bytes

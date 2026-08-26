# RastaCoder Qwen3 Systemic Tool ABI v13 — verified release handoff

Branch: `iteration/qwen3-systemic-tool-abi-v13`
Release tag: `qwen3-systemic-tool-abi-v13`
Version: `0.0.12` / code `26`
Package: `ai.navixmind`
Preflight run: `32977996370`

## V13 verified architecture
- Preserves exactly 25 manually controlled Skills / 37 canonical local functions.
- Separates strict executor schemas from a smaller model-facing Tool ABI projection for Qwen3-class local models.
- Hides deterministic DOCX/PPTX/XLSX/web extraction selectors from the local model while retaining strict executor/cloud compatibility.
- Adds schema-aware argument coercion for common small-model enum, boolean, scalar, wrapper, alias and punctuation mistakes before strict validation.
- Adds complete-partition long-document ingestion: oversized document text is split across bounded chunks, processed tool-free with the same local model, and reduced to a bounded query-relevant evidence digest.
- Separates local, Anthropic and OpenAI-compatible provider readiness. OpenAI-compatible routing requires Base URL + Model ID and allows provider API Key to remain optional.
- Preserves V9 transactional Office/media/search postconditions, V10 context-safe continuation, V11 history/provider work and V12 logical workspace path hardening.

## Validation
- No-APK V13 preflight run `32977996370`: SUCCESS, including V9/V10/V11/V12/V13 gates and Flutter static analysis.
- Formal release repeated V9/V10/V11/V12/V13 gates before and after APK build.
- Package/version, stable signing certificate, ARM64-only ABI and exact known-good MLC runtime were verified after build.

## Final verified artifact
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `45df4ec4bc66622929d05e66675ff3a49933dbca93b7a1f6b14daf91d4827b83`
- APK size: `517035724` bytes

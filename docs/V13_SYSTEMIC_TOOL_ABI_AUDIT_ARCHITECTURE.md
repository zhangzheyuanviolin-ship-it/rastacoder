# RastaCoder V13 systemic Tool ABI audit and architecture

Branch: `iteration/qwen3-systemic-tool-abi-v13`
Baseline branch: `iteration/qwen3-workspace-alias-hardening-v12`
Frozen verified source: `a42715cc33668b43e01d1fed35bf59b20f80a451`
V12 post-release field-feedback head: `0360d3b788b3096f1e0a0fda705fd07c93aeab4d`

## Scope freeze

V13 adds no new Skill and no new canonical executor function. The local catalogue remains 25 user-controlled Skills / 37 canonical functions. This iteration is a systemic boundary hardening pass across model-facing Tool ABI, document ingestion, argument normalization, and cloud-provider routing.

## Archaeology findings

The upstream `BoozeLee/rastacoder` code already exposed executor-oriented Office schemas directly to the model: `read_docx.extract` is `text|tables|all`, `read_pptx.extract` is `text|slides|notes|all`, and `read_xlsx.extract` is `values|formulas|all`. Upstream also fed large tool payloads back to the model with a simple character truncation strategy. The fork did not invent those enums; the fork's later Skill work made small-model execution substantially broader and added compatibility repair, but the on-device 3B–4B route still inherited too much executor ABI complexity at the model boundary.

The evolution through V6–V12 fixed independent reliability layers: canonical function naming and generic argument repair, complete Skill coverage, route/history/accessibility behavior, transactional Office/media/search postconditions, bounded search/context results, OpenAI-compatible plumbing, and virtual workspace path normalization. The V12 real-device DOCX/PPTX failures show that these layers are individually useful but do not yet form a complete small-model ABI: the model still has to choose executor enums it should not need to know, and long document text is still treated as one generic oversized tool result.

The OpenAI-compatible Python bridge and request client are already capable of operating with Base URL + Model ID and an optional API key. The blocking defect is in Flutter chat readiness: both route synchronization and the send gate currently classify every non-offline model as Claude and require a Claude key before Python can run.

## V13 architecture

### 1. Explicit provider capability identity

Keep the existing broad `ModelProvider.cloud/offline` classification for compatibility, and add an explicit route capability identity:

- `local`: requires downloaded + loaded local model.
- `anthropic`: requires Claude API key.
- `openaiCompatible`: requires Base URL + Model ID; API key is optional.

Both `_syncModelRouteState()` and `_ensureSelectedRouteReadyForSend()` must switch on this identity. The OpenAI-compatible route must never call the Claude-key gate or send a Claude key merely to become ready.

### 2. Model-facing Tool ABI is a projection, not the executor schema

`TOOLS_SCHEMA` remains the strict executor/cloud contract. Local Qwen receives a deep-copied model-facing projection.

Every canonical function has an argument classification derived from the strict schema:

- model-essential: required by the executor schema or explicitly promoted for ordinary task intent;
- app-defaultable: executor option has a deterministic safe default and is hidden from the small-model schema when exposing it harms reliability;
- advanced-only: optional executor controls retained only when necessary for a real user intent.

V13 first applies this separation to the document/read family that produced field failures:

- `read_docx(docx_path)`; app defaults `extract=all`.
- `read_pptx(pptx_path)`; app defaults `extract=all`.
- `read_xlsx(xlsx_path, sheet?, range?)`; app defaults `extract=values`.
- `read_pdf(pdf_path, pages?)`; app defaults `pages=all`.
- `web_fetch(url)` ordinary model-facing path; app defaults extraction to text while legacy/advanced executor calls remain compatible.

The strict executor schemas are unchanged so cloud models, old sessions, and direct compatibility calls remain valid.

### 3. Schema-aware compatibility coercion before validation

The compatibility layer must deterministically normalize common small-model surface mistakes before the strict schema gate:

- trailing punctuation on keys;
- nested `arguments/args/parameters/input` wrappers;
- canonical aliases and path aliases;
- enum case/spacing/hyphen variants;
- boolean and string-boolean values accidentally emitted for enum selectors -> the tool's safe default;
- scalar page/sheet/range values -> strings where unambiguous;
- null/empty optional selectors -> omit and let executor defaults apply;
- existing string/list/object repairs for file arrays, operations, media params, search intent, and workspace aliases.

Ambiguous transformations remain rejected. Every repair remains observable in diagnostics.

### 4. Document-family ingestion is separate from generic tool-result trimming

Search/list payload compaction remains generic. Document reads require a complete-coverage ingestion path.

For local models, when a read result exceeds the ordinary model-result budget:

1. extract the primary textual payload;
2. split it into bounded, non-overlapping chunks covering the complete executor-returned text;
3. run a tool-free, `/no_think` internal ingestion pass over every chunk using the same downloaded local model;
4. ask each pass for compact query-relevant evidence notes preserving names, numbers, claims, structure, and uncertainties;
5. aggregate those notes into one bounded `DOCUMENT_INGESTION` payload with source character count and chunk-coverage metadata;
6. return that digest to the normal ReAct turn for the user-facing final answer.

This prevents a 45k-character DOCX/PPTX/PDF from forcing one giant prefill or from yielding only a head/tail truncation. Ordinary short reads keep the direct path. Internal ingestion never exposes tools and never creates a second agent loop.

### 5. Max-token behavior

The existing one-shot local final-answer continuation remains as a last-resort guard. V13's document ingestion is designed to prevent read/summarize tasks from entering that path solely because a large source document was inserted wholesale into the active conversation.

## Acceptance matrix

V13 is eligible for an APK only after all inherited V9/V10/V11/V12 gates remain green and V13 adds these checks:

1. all 37 canonical local functions are still covered by the Skill catalogue;
2. every function receives a generated argument classification with no unclassified schema property;
3. local `read_docx` schema exposes `docx_path` and hides `extract`;
4. local `read_pptx` schema exposes `pptx_path` and hides `extract`;
5. local `read_xlsx` hides `extract` while preserving optional sheet/range targeting;
6. bool/string-bool enum mistakes for DOCX/PPTX/XLSX normalize to safe defaults;
7. mixed-case valid enum values normalize deterministically;
8. PDF page numeric values normalize to strings and null pages fall back to executor default;
9. short document tool results remain direct and bounded;
10. synthetic ~45k document text is split with complete character coverage and produces a bounded ingestion digest contract without generic head/tail truncation;
11. OpenAI-compatible route identity does not depend on Claude API key;
12. OpenAI-compatible readiness requires Base URL + Model ID and treats provider API key as optional;
13. Anthropic readiness still requires Claude key;
14. local readiness still requires downloaded/loaded state;
15. Flutter static analysis passes;
16. formal APK verification repeats package/version/signature/ARM64/runtime hashes and all inherited regression gates.

## Formal release target

Version: `0.0.12` / code `26`
Tag: `qwen3-systemic-tool-abi-v13`
APK: `RastaCoder-Qwen3-4B-systemic-tool-abi-v13-update.apk`

The stable package id, signing identity, known-good MLC runtime, local Qwen3-4B model registration, 25-Skill/37-function catalogue, history behavior, workspace path contract, and V9–V12 postcondition safeguards are frozen invariants.
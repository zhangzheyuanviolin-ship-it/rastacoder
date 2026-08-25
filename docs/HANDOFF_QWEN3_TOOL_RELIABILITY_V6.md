# RastaCoder Qwen3 Tool Reliability v6 — Live Handoff

Last updated: 2026-08-25
Branch: `iteration/qwen3-tool-reliability-v6`
Base v5 commit: `6c50af4917f7908da0cce9b0ec15646f35bd3f30`
Parent development branch: `iteration/qwen3-cn-ui-live-tools-google`

## User-reported v5 regressions

The v5 UI features are present, but local Qwen3-4B tool-call reliability regressed even with only one Skill enabled.

Observed failures supplied by the user:

1. Word creation:
   - Model invoked `create_docx` with only `content`.
   - Runtime error: `[MODEL_TOOL_ARGUMENT_ERROR] create_docx missing required parameter(s): output_path. Received: ['content']`.
   - Model then asked the user for a path instead of recovering automatically.

2. Audio conversion:
   - Model emitted literal final text:
     `<tool_call>{"name":"audio_processing","arguments":{"param":"convert analysis_article.mp3 to wav"}}</tool_call>`
   - `audio_processing` is a Skill id, while the executable tool is `ffmpeg_process`.
   - The parser/executor compatibility layer did not recover this Skill-name call and the call leaked to final response.

3. Thinking mode is not practically verifiable:
   - v5 has model-default / force-thinking / force-no-thinking settings.
   - Raw/model reasoning remains hidden from the chat UI in all modes.
   - The chat bubble already contains a legacy `<think>` ExpansionTile, but the local tool-call parser discards `<think>` text on tool-use turns, so the user cannot reliably inspect it.

4. Tool-call failures are difficult to diagnose:
   - The chat surface shows a user-facing error, but there is no complete copy/export flow for model tool-call diagnostics.
   - Need enough information to distinguish model-format error, parser normalization, argument repair, file/path resolution, executor error, and native tool error.

## v6 objective

This is a full reliability audit, not a two-bug patch.

Audit every one of the 21 Skills and all 23 canonical underlying local tools for the same failure classes:

- Skill id emitted as if it were a tool name.
- Human-friendly alias emitted as tool name.
- Canonical tool name emitted with wrong argument names.
- Generic `param`, `query`, `request`, `instruction`, or free-form string arguments.
- Missing output filename/path for creation/conversion/modification tools.
- Missing operation/action values.
- Missing input path when there is exactly one attached/known compatible file.
- Basename vs full path mismatch.
- Output extension/format mismatch.
- Enum aliases and common natural-language variants.
- XML/Hermes/raw-JSON/single-quote/trailing-comma/function-syntax tool call variants.
- Tool-call tags leaking into final assistant text.
- Error recovery after a first malformed tool call.
- Multiple enabled Skills without accidental alias collisions.

The v6 release must maximize single-Skill reliability for every Skill before considering speed.

## Required architectural constraints

- Keep all 21 user-managed Skills and all 23 canonical tools. No capability may be removed.
- Skill selection remains entirely manual. No automatic Skill selection/router.
- Thinking mode remains entirely manual. Skill state must never change Thinking mode.
- Keep package id `ai.navixmind`.
- Preserve stable signing identity and in-place upgrade compatibility.
- Preserve the known-good ARM64 MLC runtime.
- Do not modify `local-agent-plaza`; it is read-only reference material only.

## Planned reliability changes

### A. Skill-to-tool compatibility layer

Add explicit Skill-id aliases only when routing is unambiguous:
- `audio_processing` -> `ffmpeg_process`
- `video_processing` -> `ffmpeg_process`
- `word` -> context-sensitive Word canonical tool; creation intent defaults to `create_docx`
- and equivalent safe mappings for the other Skills.

Where one Skill contains multiple canonical tools, route using arguments/intent/file extension. If ambiguity remains, do not silently execute a destructive operation.

### B. Argument repair and default synthesis

For safe deterministic cases, synthesize missing values before strict schema validation:
- `create_docx(content)` -> default output filename `document.docx`.
- `create_pdf(content)` -> default `document.pdf`.
- `write_file(content)` -> default `output.txt`.
- `ffmpeg_process` can infer a unique current attachment and safe output filename.
- Audio-output conversion is normalized to the native `extract_audio` branch with `params.format`, because the native `convert` branch is video-oriented.
- Similar safe defaults are added for ZIP, smart crop and Office modification outputs.

All repairs must be logged as compatibility repairs.

### C. Parser hardening

The parser must recognize Skill ids and common aliases inside tool-call tags and raw JSON. A recognizable tool call must never be returned as normal assistant prose merely because its name is non-canonical. An unparseable `<tool_call>` wrapper should trigger a bounded model retry rather than leak into the final reply.

### D. Thinking visibility

Implement an expandable/collapsible Thinking area in chat for local Qwen3 responses:
- collapsed by default;
- accessible label for screen readers;
- preserve reasoning separately from final answer and keep it out of subsequent model history;
- when force-no-thinking is selected and no reasoning is produced, explicitly show that state;
- when thinking/model-default produces no visible reasoning, explicitly say the model returned no displayable reasoning text.

This makes the manual Thinking setting inspectable from the UI.

### E. Tool diagnostics

Add per-query diagnostic capture with copy/export support. It should include:
- enabled Skills and canonical allowed tools;
- selected Thinking mode and local model parameters;
- raw model tool call name/arguments in a bounded representation;
- canonicalized tool name and argument repairs;
- resolved file/input/output paths;
- schema/enum/disabled-tool errors;
- executor/native error summaries;
- parser retry state.

Secrets such as API keys, OAuth tokens and authorization values must be redacted.

### F. Full 21-Skill / 23-tool test matrix

Before release, build a machine-checkable regression suite covering every canonical tool and every Skill. At minimum test:
- canonical call;
- Skill-id/alias call where applicable;
- common malformed argument names;
- missing safe-default output path;
- file basename/unique-attachment inference;
- parser extraction from `<tool_call>` text;
- disabled-tool enforcement;
- no tool-call leakage into final text.

## Current findings from v5 source audit

- v5 `build_offline_skill_prompt()` prints Skill ids such as `audio_processing` in the prompt while describing canonical `ffmpeg_process`. This increases the chance that a 4B model emits the Skill id as the function name.
- v5 also gives the model a generic example argument key `{"param":"value"}`. The user's failing audio call copied this exact unsafe pattern as `{"param":"convert analysis_article.mp3 to wav"}`.
- v5 `TOOL_ALIASES` includes `audio_edit` and `video_edit`, but does not include `audio_processing` or `video_processing`.
- v5 strict schema validation requires `create_docx.output_path` and happens before any default output filename synthesis.
- v5 parser checks whether a name is canonical before argument-aware normalization, preventing ambiguous Skill aliases from being repaired.
- v5 native FFmpeg `convert` path is video-oriented; audio target formats are more reliable through `extract_audio` with an explicit `params.format`.
- v5 local parser removes `<think>...</think>` while extracting text-based tool calls, which destroys reasoning from tool-use turns before the UI can display it.
- v5 has no full copy/share diagnostic surface attached to each local response.

## Progress log

### 2026-08-25 — Milestone 0

- Created dedicated reliability branch from v5 source.
- Created this handoff document before code changes.
- Confirmed work scope is full 21-Skill reliability audit + Thinking visibility + diagnostics, not isolated fixes.

### 2026-08-25 — Milestone 1: core design/patchers written

New files on the v6 branch:
- `scripts/apply_iteration_v6.py`
- `scripts/apply_iteration_v6_ui.py`

Core patcher currently implements:
- removes Skill IDs from the model-facing prompt; only canonical callable function names/signatures are injected;
- removes the unsafe generic `param` example and explicitly forbids generic argument keys;
- adds single-tool Skill aliases and deterministic routing for multi-tool Skills (`word`, `powerpoint`, `excel`, `text_files`);
- recognizes the user's exact failing `audio_processing + param="convert analysis_article.mp3 to wav"` shape;
- infers safe output names and unique current attachments where deterministic;
- normalizes audio target conversion to native `extract_audio` + `params.format`;
- performs alias/repair before strict schema validation and before canonical-name rejection in the text parser;
- adds bounded parser retry for malformed `<tool_call>` wrappers so raw XML does not become the final assistant answer;
- initializes per-query redacted diagnostics and records query config, model response shape, raw/canonical tool calls, repairs, resolved paths and tool errors;
- preserves `<think>` reasoning separately before tool-call parsing removes it, keeps reasoning out of model history, and returns it to Flutter as dedicated metadata.

UI patcher currently implements:
- `ChatMessage.thinking`, `thinkingMode`, and `diagnostics` fields;
- uses explicit local reasoning in the existing collapsed Thinking ExpansionTile;
- shows the manual Thinking mode even when the model returns no displayable reasoning text;
- adds a collapsed `工具调用诊断` panel to assistant/error messages;
- diagnostic panel has explicit `复制诊断日志` and `分享诊断日志` buttons;
- long-press menu also exposes copy/share diagnostics;
- VoiceOver semantics announce when a response contains expandable Thinking or diagnostics.

Important: these patchers are written but have not yet passed CI. Do not treat Milestone 1 as a release-ready state.

## Release gate

Do not publish v6 until all of the following pass:

1. 21 Skills still cover exactly all 23 canonical local tools.
2. Full compatibility/test matrix passes.
3. Python compilation passes.
4. Flutter analyze passes without new blocking errors.
5. Full Android/Flutter debug build compiles Kotlin/native integration.
6. APK package/version/signature/ABI/runtime verification passes.
7. Thinking area is accessible and manually expandable/collapsible.
8. Tool diagnostic log can be copied/exported and contains enough information to classify failures.
9. v4/v5 previously working examples such as TXT->DOCX and audio format conversion are regression-tested.
10. Handoff document is updated with final commit, workflow run, release tag, APK SHA-256, and known residual risks.

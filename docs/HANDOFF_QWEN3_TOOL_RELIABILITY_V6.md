# RastaCoder Qwen3 Tool Reliability v6 — Live Handoff

Last updated: 2026-08-25
Branch: `iteration/qwen3-tool-reliability-v6`
Base v5 commit: `6c50af4917f7908da0cce9b0ec15646f35bd3f30`
Parent development branch: `iteration/qwen3-cn-ui-live-tools-google`
Target v6 version: `0.0.5`, versionCode `19`

## Non-negotiable constraints

- Work only in `rastacoder`. `local-agent-plaza` is read-only reference material.
- Preserve package/applicationId `ai.navixmind`.
- Preserve the stable RastaCoder signing identity for in-place upgrades.
- Preserve the byte-verified ARM64 MLC runtime SHA-256 `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`.
- Keep all 21 user-managed Skills and all 23 canonical underlying tools.
- Skill selection stays manual. No automatic Skill router.
- Thinking mode stays manual and independent from Skills.
- Do not release v6 until all validation/native/APK gates pass.

## User-reported v5 regressions

The v5 UI features are present, but Qwen3-4B tool reliability regressed systemically even with one Skill enabled.

Confirmed user samples:

1. Word creation failure
   - Model called `create_docx` with only `content`.
   - Runtime error: `[MODEL_TOOL_ARGUMENT_ERROR] create_docx missing required parameter(s): output_path. Received: ['content']`.
   - Model then asked the user to provide a path instead of recovering with a safe output filename.

2. Audio conversion failure
   - Literal final text leaked to chat:
     `<tool_call>{"name":"audio_processing","arguments":{"param":"convert analysis_article.mp3 to wav"}}</tool_call>`
   - `audio_processing` is a UI Skill ID; executable canonical function is `ffmpeg_process`.
   - Parser did not recover the alias and therefore did not execute the tool.

3. TXT write failure
   - User tested the text-file Skill and observed the same systemic behavior: tool-call text / imagined success appeared as final prose instead of an executed TXT write.
   - This expands the regression family beyond media/Word and confirms a general model-output → parser → argument-repair problem.

4. Thinking mode cannot be empirically verified
   - v5 has model-default / forced thinking / forced no-thinking.
   - User sees final answer only in normal use.
   - Existing `MessageBubble` contains a legacy `<think>` ExpansionTile, but local parser removes `<think>` on tool-use turns and does not return reasoning separately.

5. Tool errors are not diagnosable from the UI
   - No complete per-query copy/export log exists.
   - Need to distinguish model formatting, parser normalization, alias repair, path resolution, schema failure, executor/native failure.

6. Chat lifecycle is incomplete
   - ChatScreen stores visible messages only in an in-memory `_messages` list.
   - User cannot create a fresh conversation or browse/switch history.
   - Restarting the app clears the visible chat, so user has been forced to restart just to get a new thread.

## Root-cause findings

### Tool calling

- v5 exposes UI Skill IDs such as `audio_processing`, `word`, `text_files` in the model-facing system prompt while execution accepts canonical functions such as `ffmpeg_process`, `create_docx`, `write_file`.
- v5 substantially compresses the exact canonical function-signature guidance that existed in v4. This is a likely direct reliability regression for a 4B model.
- The generic `{ "param": "value" }` example also exists in v4, so it is not by itself the v5 regression. In v5 it became more dangerous because Skill IDs were newly exposed while exact signatures were weakened. The user’s audio output copied both failure cues at once.
- v5 compatibility aliases do not include `audio_processing` / `video_processing` or deterministic routing for multi-tool Skill IDs.
- v5 `_build_tool_use` rejects unknown/noncanonical names before argument-aware normalization.
- v5 validates required schema parameters before any safe default synthesis.
- `create_docx`, `write_file` and other creation tools therefore fail on missing `output_path` even when a safe filename can be selected automatically.
- Native Android FFmpeg `convert` is video-oriented. Audio targets MP3/WAV/M4A/AAC/FLAC/OGG are more reliable through `extract_audio` + `params.format`.
- MLC streamed structured tool calls were accumulated with `getOrPut(toolCallAccumulators.size)`, which can create a separate accumulator for successive fragments of one call. v6 must key by streamed tool-call index and merge arguments.

### Thinking / diagnostics

- `MessageBubble` already has a collapsed Thinking UI for literal `<think>` blocks.
- The local parser removes reasoning during tool-call normalization, so tool-use-turn reasoning is lost before Flutter receives it.
- MLC v5 event telemetry reports phases but does not provide reasoning content.
- v6 must preserve local model reasoning separately from final answer and expose it through the existing accessible collapsed panel.

### Conversation history

The repository already contains most of the data layer:

- `lib/core/database/collections/conversation.dart`
- `lib/core/database/collections/message.dart`
- `lib/core/services/conversation_manager.dart`
- Isar already opens Conversation and Message schemas.

`ConversationManager` already has `createConversation`, `loadConversation`, `addMessage`, summarization logic and Python `sync_full` / `new_conversation` deltas.

The integration gap is the problem:

- `main.dart` never initializes `ConversationManager`.
- `ChatScreen` does not use it and keeps messages only in `_messages` memory.
- Therefore restart clears the visible thread and the UI has no history/new-conversation surface.

v6 will wire this existing layer rather than invent a parallel database.

## v6 implementation files currently staged

Core reliability:
- `scripts/apply_iteration_v6.py`
- `scripts/run_iteration_v6.py`
- `scripts/apply_iteration_v6_reliability2.py`

Observability:
- `scripts/apply_iteration_v6_ui.py`

Conversation lifecycle:
- `scripts/apply_iteration_v6_history.py`

Native MLC:
- `scripts/apply_iteration_v6_native.py`

Validation:
- `scripts/validate_iteration_v6.py`
- `scripts/validate_iteration_v6_extended.py`
- `.github/workflows/v6-validation.yml`

## Implemented design in the patch chain

### A. Model-facing tool contract

- Skill IDs remain UI-only and are omitted from the local system prompt.
- Model sees only enabled canonical executable function names.
- Model sees exact canonical signatures such as `write_file(output_path, content)`, `create_docx(output_path, content, title?)`, `ffmpeg_process(input_path, output_path, operation, params?)`.
- Prompt explicitly requires exact argument names and forbids generic `param/request/instruction/command` keys.
- Enabled schema still contains only functions belonging to manually enabled Skills.

### B. Compatibility / argument repair

- Accepts legacy aliases and v5 Skill-name hallucinations.
- Deterministically routes multi-tool Skill names `text_files`, `word`, `powerpoint`, `excel` based on intent/arguments.
- Infers a unique compatible current attachment where safe.
- Synthesizes safe output filenames for DOCX/PDF/TXT/ZIP/Office modifications/smart crop/media output.
- User audio regression shape is normalized to canonical `ffmpeg_process`, input file, `operation=extract_audio`, `params.format=wav`, derived WAV output.
- Generic free-form creation recovery is generalized across `write_file`, `create_docx`, `create_pdf`, including extraction of body text and an explicit output filename when present.
- Generic compatibility keys are removed before strict schema validation.

### C. Parser hardening

- Alias/argument-aware normalization happens before canonical-name rejection.
- Hermes/XML/raw JSON variants remain accepted.
- Recognizable but invalid `<tool_call>` output produces bounded repair retries and cannot silently leak as final prose.
- Model-caused name/argument errors are returned as recoverable tool results so the ReAct loop can retry immediately.

### D. Thinking / diagnostics

- Reasoning is captured before parser cleanup, kept separate from final answer and kept out of subsequent model history.
- Flutter receives `thinking`, `thinking_mode`, and redacted `diagnostics` metadata.
- Existing collapsed Thinking panel uses explicit reasoning metadata first.
- If no displayable reasoning is returned, UI shows the selected manual Thinking mode so enabled/disabled/default can be tested.
- Per-response `工具调用诊断` panel supports copy/share and is exposed on error messages too.
- Diagnostics include enabled Skills/canonical tools, model parameters, raw/canonical tool call, repairs, resolved paths, schema/native errors and parser retry state; secrets are redacted.

### E. Persistent multi-conversation lifecycle

`apply_iteration_v6_history.py` stages:

- initialize `ConversationManager` from the existing Isar instance in `main.dart`;
- add list/read/store/rename/delete history APIs;
- keep DB persistence separate from Python insertion for messages already processed by `process_query`, preventing duplicate context;
- guard `sync_full` / `new_conversation` while Python is still booting;
- re-sync selected conversation on Python ready/restart;
- add accessible `聊天记录` and `新建对话` app-bar controls;
- add accessible history screen with switch, rename and delete;
- persist user and final assistant/error messages;
- auto-title a new conversation from its first user request;
- when history switches, reload persisted UI messages and sync the same conversation ID into Python SessionState.

### F. Native structured-tool stream hardening

- Accumulate `choice.delta.tool_calls` by `forEachIndexed { index, tc -> ... }`.
- Reuse `toolCallAccumulators[index]` across chunks.
- Merge streamed argument maps instead of replacing/fragmenting them.

## Validation coverage

The two v6 validators jointly require:

- exact 21 Skill set and exact 23 canonical tool coverage;
- no model-facing Skill-ID list;
- canonical callable signature prompt;
- every Skill exercised in the routing matrix;
- exact user audio regression sample;
- exact content-only DOCX regression sample;
- generic TXT Skill + `param` write sample;
- generalized DOCX/PDF free-form creation samples;
- one representative normalized call for every canonical tool, checked against that tool’s real top-level `required` schema keys;
- unique-attachment/path/output-default repair families;
- parser alias extraction and tool-call leak prevention markers;
- manual Thinking and diagnostics UI markers;
- MLC call-index accumulation and argument merge;
- Isar ConversationManager initialization, new/load/rename/delete/history UI and Python resync markers.

## CI history

### Validation run #1 — failed before behavioral tests

Run:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32861631517`

Result:
- known-good baseline restore passed;
- deterministic v2→v5 replay passed;
- v5 validator passed;
- failed while executing the first v6 core patcher because embedded generated `compat.py` regex literals reused the outer triple-single-quote delimiter, causing a Python `SyntaxError` at the patch-script layer;
- no v6 behavior test, Flutter compile or Android build ran in this failed attempt.

`run_iteration_v6.py` was added to repair only those bounded embedded regex delimiters in memory, compile the repaired patcher and execute it reproducibly. Current workflow uses this runner.

## Current checkpoint

Latest workflow definition has been expanded to apply, in order:

1. exact v5 reconstruction;
2. v6 core reliability runner;
3. generalized free-form creation recovery;
4. Thinking/diagnostics UI;
5. persistent history/new-conversation integration;
6. MLC structured-call accumulation hardening;
7. base + extended systemic validators;
8. Python compile;
9. Flutter analyze;
10. exact known-good MLC runtime restore;
11. full Flutter Android debug/native compile with v6 version `0.0.5` / code `19`;
12. both validators again after native build.

No v6 APK has been released yet. Treat all v6 code as pre-release until the workflow is fully green and final signed APK verification passes.

## Release gate

Do not publish v6 until all are green:

1. 21 Skills exactly cover all 23 canonical tools.
2. Every canonical tool representative satisfies its required schema after repair.
3. TXT, DOCX and audio user regression families pass.
4. Parser cannot leak recognizable tool calls into final prose.
5. Python compile passes.
6. Flutter analyze passes without new blocking errors.
7. Full Android/Kotlin/Java/Chaquopy/MLC build passes.
8. Thinking panel is accessible and manual mode is inspectable.
9. Tool diagnostic log is copyable/shareable and secrets are redacted.
10. New conversation + history list + switch + rename + delete + restart persistence are wired to Isar and Python session resync.
11. APK package/version/signature/ARM64/runtime checks pass.
12. This handoff is updated with final source commit, validation/build run, release tag, APK byte size and SHA-256, and known residual risks.

## Final signed v6 release checkpoint

- Release workflow run: https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32907785284
- Release tag: `qwen3-tool-reliability-history-v6`
- APK: `RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`
- APK SHA-256: `9f872f37802f7b362fc9a0f1f15f0d152b2e61c50cbde378e886bae9b2deb001`
- APK size: `499354824` bytes
- versionName/versionCode: `0.0.5` / `19`
- package/applicationId: `ai.navixmind`
- stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- ABI: `arm64-v8a` only
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- Three systemic v6 validators passed before native build, after native build, and immediately before release.

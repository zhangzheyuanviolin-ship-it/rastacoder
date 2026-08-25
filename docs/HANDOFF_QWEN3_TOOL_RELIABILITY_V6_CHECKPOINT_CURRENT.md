# RastaCoder — Current Master Continuation Handoff after v6

Last updated: 2026-08-26
Repository: `zhangzheyuanviolin-ship-it/rastacoder`
Current development branch: `iteration/qwen3-tool-reliability-v6`
Parent branch used before v6: `iteration/qwen3-cn-ui-live-tools-google`
Current branch HEAD before this documentation update: `c17cedd9f56fff8256702387de7a621e59b78871`

This file is the canonical continuation checkpoint for the next ChatGPT/Codex/agent context. Read this file first, then read `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6.md`, the current branch source, and the v6 workflow before changing code.

**Precedence rule:** if any older handoff/checkpoint contains a stale pre-release statement such as “v6 has not been released yet” or otherwise conflicts with this file, treat that statement as historical. This 2026-08-26 master checkpoint is authoritative for current project state.

## 1. Immediate user state and next action

The user has already obtained the final v6 APK download link and has downloaded the APK, but at the time of this handoff has not yet reported a complete real-device v6 test result.

The next context should therefore begin from this state:

- v6 is built and formally released.
- CI/systemic validation is green.
- real-device behavior is still awaiting the user's empirical test, especially local Qwen3-4B tool calling, Thinking visibility, diagnostics, chat history, and benchmark.
- Do not start a speculative v7 rewrite before reading the user's v6 test feedback.
- When the user reports a v6 failure, use the new copy/share per-response tool diagnostics as the first evidence source whenever available, then map the failure back into the compatibility/parser/executor/native layer and add a regression gate for the exact failure shape.

## 2. Non-negotiable project constraints

These constraints came directly from the development history and must survive future contexts.

- Work only in `rastacoder` for this project.
- `local-agent-plaza` may be inspected read-only as a reference sample. Do not modify it, commit to it, build from it, or move this project there.
- Keep package/applicationId `ai.navixmind`.
- Preserve the existing RastaCoder development signing identity so updates install in-place without forcing users to uninstall or lose app data/downloaded local models.
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`.
- Stable signing certificate SHA-1: `74:5D:97:54:87:32:A9:DE:D0:96:6E:A5:58:8E:78:68:8F:85:31:B6`.
- Preserve the known-good MLC runtime byte-for-byte unless a future task explicitly requires replacing it.
- Known-good MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`.
- Known-good MLC runtime size: `38786520` bytes.
- Keep Android release/test line ARM64-only unless the user explicitly changes that requirement.
- Future release versionCode must be greater than `19`.
- Do not send large APKs through sandbox links. Delivery standard is a direct GitHub Release/browser download URL.
- Skill selection stays manual. Do not add automatic Skill selection/router without explicit user approval.
- Thinking mode stays manual and independent from Skill state.
- Keep all 21 user-managed Skills and all 23 canonical local tool functions unless the user explicitly requests a capability change.

## 3. Known-good upstream and model foundation

Upstream application repository:
`alexandertaboriskiy/navixmind`

Known-good upstream commit:
`e165c311eb464722c5db0883426e82af69468330`

Known-good upstream APK:
`https://github.com/alexandertaboriskiy/navixmind/releases/download/v0.5.0-beta/app-debug.apk`

Upstream APK byte size:
`593655513`

Upstream APK SHA-256:
`94f574560ec469772021e284a12eabb71211393d25388c6669d854d58810a8ed`

Known-good local model identity:
- model id: `Qwen3-4B-q4f16_0-MLC`
- model lib: `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
- source currently referenced by the app: `alexandertaboriskiy/Qwen3-4B-q4f16_0-MLC`
- MLC native runtime packaged at `lib/arm64-v8a/libtvm4j_runtime_packed.so`

The user's priority is not raw speed alone. Local Qwen3-4B must remain usable as an offline tool-calling agent even if generation is slow.

## 4. Stable release history that matters

### v4 — last version the user considered broadly tool-functional before Skill grouping

Release tag:
`qwen3-arm64-tools-v4`

Direct APK:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/download/qwen3-arm64-tools-v4/RastaCoder-Qwen3-4B-arm64-tools-v4-update.apk`

Version:
- versionName `0.0.3`
- versionCode `17`

The user tested v4 and confirmed multiple tools worked, including TXT -> DOCX and audio conversion. v4 is therefore the behavioral comparison point for tool reliability.

### v5 — major feature version, but real-device tool reliability regressed

Release tag:
`qwen3-skills-params-stream-v5`

Direct APK:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/download/qwen3-skills-params-stream-v5/RastaCoder-Qwen3-4B-skills-params-stream-v5-update.apk`

Version:
- versionName `0.0.4`
- versionCode `18`

v5 added:
- 21 manually managed Skills/toolpacks;
- local model parameter page;
- exact integer context-token and max-output-token fields;
- manual Thinking mode: model default / enabled / disabled;
- benchmark UI with saved history and clipboard copy;
- MLC generation phase telemetry.

v5 was rejected as a reliable tool-calling build after the user tested it on-device.

### v6 — current final released version

Release name:
`RastaCoder Qwen3 4B Tool Reliability + Chat History v6`

Release tag:
`qwen3-tool-reliability-history-v6`

Release page:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/tag/qwen3-tool-reliability-history-v6`

Direct APK:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/download/qwen3-tool-reliability-history-v6/RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`

Version:
- versionName `0.0.5`
- versionCode `19`

Final APK byte size:
`499354824`

Final APK SHA-256:
`9f872f37802f7b362fc9a0f1f15f0d152b2e61c50cbde378e886bae9b2deb001`

Final release workflow run:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32907785284`

Release-trigger commit:
`4d876cd7936c4526c25c1742d4ceb5b163eee907`

Post-build persisted-source commit:
`c17cedd9f56fff8256702387de7a621e59b78871`

The release job completed all build, validator, signature, package, version, ABI and runtime gates successfully.

## 5. Why v5 failed in real use

The user tested several very simple single-Skill tasks and found systemic regressions.

### Word creation sample

Model attempted `create_docx` with only `content`.

Observed runtime error:
`[MODEL_TOOL_ARGUMENT_ERROR] create_docx missing required parameter(s): output_path. Received: ['content']`

The model then asked the user to provide an output path instead of choosing a safe filename.

### Audio conversion sample

The model emitted this literal text into the final assistant response:

`<tool_call>{"name":"audio_processing","arguments":{"param":"convert analysis_article.mp3 to wav"}}</tool_call>`

Problems exposed by this one sample:
- `audio_processing` was a UI Skill ID, while the executable function is `ffmpeg_process`;
- the parser/executor did not recover the Skill-name hallucination;
- the model used generic `param` instead of the true FFmpeg schema;
- the recognizable tool call leaked to normal assistant prose;
- no actual tool execution occurred.

### TXT creation sample

The user also tested simple TXT writing and observed the same general failure class: model-generated tool-call text and imagined success could appear as final prose without the tool actually executing.

This established that the v5 problem was systemic across the model-output -> parser -> canonicalization -> schema -> path -> executor chain, not a single media/Word bug.

## 6. v6 systemic tool reliability architecture

v6 keeps the 21-Skill UI but changes the model-facing contract.

### Core rule

UI Skill IDs are UI-only.

The local model should see:
- only canonical executable function names belonging to the manually enabled Skills;
- exact function signatures / expected parameter names;
- instructions to use exact canonical names and exact argument keys.

The model should not be shown `audio_processing`, `word`, `text_files`, etc. as callable names.

### Compatibility layer

v6 accepts and repairs common 3B-4B model mistakes before strict schema validation where the repair is deterministic and safe.

Repair families include:
- old aliases;
- v5 Skill-ID hallucinations;
- multi-tool Skill routing for `text_files`, `word`, `powerpoint`, `excel` based on arguments/intent;
- `param`, `request`, `instruction`, `command` free-form mistakes;
- wrong path key aliases;
- missing safe output filenames;
- unique current-attachment inference;
- common format/action aliases;
- audio conversion normalization;
- output path derivation for Office/media operations.

Important example:
`audio_processing + param="convert analysis_article.mp3 to wav"`
should normalize to `ffmpeg_process` with the input file, a generated WAV output, `operation=extract_audio`, and `params.format=wav`.

For Android FFmpeg, audio-target conversions are deliberately routed through the native `extract_audio` branch because the existing native `convert` branch is primarily video-oriented.

### Parser hardening

v6 performs alias/argument-aware normalization before canonical-name rejection.

Recognizable malformed tool wrappers should enter bounded repair/retry handling and must not silently become normal final prose.

Model-caused argument/name errors are returned to the ReAct loop as recoverable tool results so the model can retry the same task with corrected parameters.

### Structured MLC tool streaming

v6 changes native `MLCInferenceChannel.kt` so streamed structured tool calls are accumulated by the real call index across chunks. Argument fragments are merged into the same accumulator instead of allocating a new call object on each fragment.

This matters if MLC starts returning structured function-call deltas instead of plain-text XML tool calls.

## 7. Exact 21 Skills and 23 canonical tools

The UI catalog currently contains 21 Skills grouped into five categories.

### 文件与文档

1. `text_files` -> `read_file`, `write_file`, `file_info`
2. `zip_archive` -> `create_zip`, `file_info`
3. `pdf_read` -> `read_pdf`, `file_info`
4. `pdf_create` -> `create_pdf`
5. `document_convert` -> `convert_document`
6. `word` -> `create_docx`, `read_docx`, `modify_docx`
7. `powerpoint` -> `read_pptx`, `modify_pptx`
8. `excel` -> `read_xlsx`, `modify_xlsx`

### 图像与多媒体

9. `ocr` -> `ocr_image`
10. `image_processing` -> `smart_crop`
11. `video_processing` -> `ffmpeg_process`
12. `audio_processing` -> `ffmpeg_process`
13. `media_download` -> `download_media`

### 网络

14. `web_fetch` -> `web_fetch`
15. `dynamic_web` -> `headless_browser`

### 计算与数据

16. `basic_calculation` -> `python_execute`
17. `scientific_calculation` -> `python_execute`
18. `data_analysis` -> `python_execute`
19. `charts` -> `python_execute`

### Google

20. `gmail` -> `gmail`
21. `google_calendar` -> `google_calendar`

The union is exactly these 23 canonical functions:

`web_fetch`, `headless_browser`, `read_pdf`, `create_pdf`, `convert_document`, `create_docx`, `read_docx`, `modify_docx`, `read_pptx`, `modify_pptx`, `read_xlsx`, `modify_xlsx`, `create_zip`, `download_media`, `ffmpeg_process`, `ocr_image`, `smart_crop`, `google_calendar`, `gmail`, `python_execute`, `file_info`, `read_file`, `write_file`.

Some low-level functions intentionally appear in multiple Skills. The actual local schema passed to the model is deduplicated.

## 8. Thinking visibility and local model observability

The user had explicitly requested a manual expandable/collapsible Thinking area because the v5 mode selector could not be empirically verified from the final answer alone.

v6 behavior:
- local reasoning is captured separately from the final answer where the model/runtime exposes displayable reasoning text;
- the chat bubble has a collapsed Thinking panel;
- the UI explicitly reports whether `/think`, `/no_think`, or model-default behavior was sent;
- reasoning is kept out of subsequent normal assistant history to avoid duplication/prompt pollution;
- if the model returns no displayable reasoning text, the UI still reports the selected/sent mode so the user can distinguish the setting path.

Do not infer Thinking mode from enabled Skills. These settings are independent by design.

## 9. Tool diagnostics

v6 adds a redacted per-response `工具调用诊断` surface.

It is intended to answer the question: did the model fail, did the parser fail, did compatibility repair alter the call, did path resolution fail, did strict schema validation reject it, or did the executor/native tool fail?

Diagnostics should include, where available:
- enabled Skills;
- allowed canonical functions;
- selected local parameters and Thinking mode;
- raw model tool name/arguments;
- canonicalized name/arguments;
- compatibility repair notes;
- resolved paths;
- schema/enum/disabled-tool error stage;
- parser retry state;
- native/executor result/error summary.

Secrets such as API keys, OAuth access tokens and authorization values must remain redacted.

The diagnostic panel supports copy and share. For future real-device failures, ask the user for this diagnostic text before making speculative parser changes when possible.

## 10. Persistent conversation history added in v6

Before v6, the UI kept visible messages only in the in-memory `ChatScreen._messages` list. Restarting the app cleared visible chat, and there was no new-conversation/history UI.

The repository already contained Isar `Conversation`, `Message`, and `ConversationManager` code; v6 wires this existing layer into the app.

Current v6 history design includes:
- initialize `ConversationManager` with the Isar instance;
- create new conversations;
- persistent conversation list;
- load/switch history;
- rename conversations;
- delete/archive conversations;
- auto-title a new conversation from the first user request;
- cold-start restoration;
- persistent attachment paths;
- created output files attached to persisted assistant messages;
- Python `SessionState` resynchronization using `new_conversation` and `sync_full` so the UI-selected conversation and model context stay aligned.

Critical rule for future work: when switching a history thread, update both the visible Isar-backed UI state and Python SessionState. Do not allow a UI/history switch that leaves the model with context from another conversation.

## 11. v5 parameter and benchmark features retained in v6

Local model parameter page retains:
- temperature;
- top_p;
- exact integer context-token field;
- exact integer max-output-token field;
- manual Thinking mode.

Context/output are text fields in Token units. Do not replace them with coarse 4K/8K sliders/presets unless the user asks.

The UI validation introduced in v5 targets:
- context tokens: `512..32768`;
- output tokens: `1..8192`;
- context + output <= `38912` as a safety margin around the current MLC configuration.

Benchmark page retains:
- prompt/completion tokens;
- prefill tok/s;
- decode tok/s;
- TTFT;
- end-to-end latency;
- process PSS;
- Java/native heap where available;
- GPU memory if queryable;
- temperature/top_p;
- model load mode/time;
- save result;
- saved history;
- copy current result to clipboard.

At handoff time the user had not yet reported a completed benchmark test.

## 12. Deterministic v6 patch chain and key files

The v6 workflow reconstructs from the known-good upstream baseline, then reapplies earlier iterations and the complete v6 chain.

Relevant patch order:

1. `scripts/apply_iteration_v2.py`
2. `scripts/apply_iteration_v2_stage2.py`
3. `scripts/apply_iteration_v2_stage3.py`
4. `scripts/apply_iteration_v4_tools.py`
5. `scripts/apply_iteration_v4_android.py`
6. `scripts/apply_iteration_v5.py`
7. `scripts/run_iteration_v6.py`
8. `scripts/apply_iteration_v6_reliability2.py`
9. `scripts/apply_iteration_v6_reliability3.py`
10. `scripts/apply_iteration_v6_ui.py`
11. `scripts/apply_iteration_v6_observability2.py`
12. `scripts/apply_iteration_v6_history.py`
13. `scripts/apply_iteration_v6_history2.py`
14. `scripts/apply_iteration_v6_history3.py`
15. `scripts/apply_iteration_v6_native.py`

Validators:
- `scripts/validate_iteration_v5.py`
- `scripts/validate_iteration_v6.py`
- `scripts/validate_iteration_v6_extended.py`
- `scripts/validate_iteration_v6_deep.py`

Current main workflow:
- `.github/workflows/v6-validation.yml`

Important runtime/source files:
- `python/navixmind/agent.py`
- `python/navixmind/session.py`
- `python/navixmind/tools/__init__.py`
- `python/navixmind/tools/compat.py`
- `python/navixmind/tools/documents.py`
- `lib/core/models/tool_skill.dart`
- `lib/core/services/storage_service.dart`
- `lib/core/services/local_llm_service.dart`
- `lib/core/services/conversation_manager.dart`
- `lib/core/bridge/bridge.dart`
- `lib/features/chat/presentation/chat_screen.dart`
- `lib/features/chat/presentation/conversation_history_screen.dart`
- `lib/features/chat/presentation/widgets/message_bubble.dart`
- `lib/features/settings/tool_skills_screen.dart`
- `lib/features/settings/local_model_parameters_screen.dart`
- `lib/features/settings/local_model_benchmark_screen.dart`
- `android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt`
- `lib/core/services/native_tool_executor.dart`

## 13. v6 CI evidence

Formal release run:
`32907785284`

All important steps completed successfully in that run:
- exact v5 reconstruction;
- v5 baseline invariant validation;
- compilation of the complete v6 patch chain;
- application of all v6 reliability/observability/history/native patches;
- all systemic 21-Skill/23-tool regression matrices;
- Python compilation;
- Flutter dependency resolution;
- Flutter Analyze;
- known-good MLC runtime restoration/verification;
- full Flutter Android native build including Kotlin/Java/Chaquopy/MLC;
- all v6 validators rerun after native build;
- stable signing restoration;
- final signed v6 candidate build;
- package/version/signature/ABI/runtime verification;
- final v6 source persistence;
- GitHub Release publication.

The validators cover the user's exact failure families and broader equivalents, including TXT writing, content-only DOCX creation, MP3-to-WAV, parser leakage, Skill-name hallucinations, generic free-form arguments, attachment/path inference, Office/media aliases, single-Skill prompt isolation, all canonical required schemas, history lifecycle markers, Thinking directive visibility, diagnostic raw/canonical call preservation, and native streamed tool-call accumulation.

CI cannot guarantee every future generative choice from a 4B model. The correct confidence statement is that v6 removes the identified systemic application-layer defects and regression-tests those defect families; real-device testing remains the final empirical gate.

## 14. CRITICAL: current branch HEAD does not exactly equal final APK packaging configuration

This is the most important handoff warning for the next developer.

The final v6 APK was verified as:
- package `ai.navixmind`;
- version `0.0.5` / code `19`;
- stable RastaCoder signing certificate;
- `arm64-v8a` only;
- exact known-good MLC runtime.

However, after release, the workflow persisted the generated v6 functional source back to the branch in commit `c17cedd9f56fff8256702387de7a621e59b78871`. The current static `android/app/build.gradle` at branch HEAD again shows upstream-style ABI filters:

`armeabi-v7a`, `arm64-v8a`, `x86_64`

and its debug buildType does not statically include the stable RastaCoder signing override.

The release workflow obtains the correct deliverable by reconstructing the known-good baseline, applying the v4/v5/v6 patch chain, restoring the verified runtime, injecting the stable signing configuration for the release-triggered debug APK, and then verifying the finished APK.

Therefore:

- Do not take raw current HEAD and run a naive `flutter build apk` and assume that output is equivalent to the released v6 APK.
- The v6 workflow is currently the release source of truth for ABI/signing/runtime packaging.
- Before a future v7 release, strongly consider normalizing the persisted branch `android/app/build.gradle` so the static source also reflects ARM64-only packaging and the intended signing strategy, while keeping secrets out of ordinary source files.
- If a future agent continues using deterministic replay, preserve the current release verification gates even after normalizing HEAD.
- Never remove the final APK ABI/signature/runtime verification just because source settings look correct.

This discrepancy does not invalidate the already released v6 APK; the final asset was inspected and verified after build. It is a maintainability hazard for future development and must be understood before producing v7.

## 15. Google OAuth issue remains separate

A prior Google sign-in `ApiException 10` issue is an external OAuth configuration problem: Android OAuth client registration must match package `ai.navixmind` and the signing SHA-1.

Do not confuse this with local-model tool reliability. v6 does not magically solve a missing/mismatched Google Cloud Android OAuth client registration.

## 16. Recommended real-device v6 test sequence

When the user tests v6, prioritize regressions before adding more features.

Suggested sequence:

1. Install v6 over v5/v4 and confirm existing local model files/app data remain available.
2. Enable only `text_files` and ask the local model to create a TXT file with supplied text.
3. Enable only `word` and ask it to create a DOCX without manually specifying a path.
4. Enable only `audio_processing`, attach an MP3, and request MP3 -> WAV conversion.
5. Test TXT -> DOCX document conversion again.
6. Enable only one read tool at a time and test path/attachment inference: PDF, DOCX, PPTX, XLSX, OCR.
7. Test ZIP creation and file_info.
8. Test ffmpeg trim/extract/frame/video conversion.
9. Test Python calculation/data/chart Skills.
10. Test ordinary web_fetch and dynamic browser Skills.
11. Test Gmail/Calendar only after valid Google OAuth connection exists.
12. Enable several Skills simultaneously and repeat a simple creation/conversion request to measure whether model selection remains reliable with a larger schema.
13. Intentionally ask for a disabled tool and confirm execution boundary blocks it.
14. Test Thinking model-default, enabled and disabled; inspect the collapsed Thinking/status surface.
15. On any failure, expand/copy `工具调用诊断` and preserve it for the next development turn.
16. Create several conversations, switch between them, rename, delete, restart the app, and confirm history persistence plus context isolation.
17. Run the benchmark and test Save + Copy to Clipboard.

## 17. How to handle the next bug report

For each new v6 failure, classify it before editing code:

A. Model selection/name error
- wrong canonical function;
- Skill ID emitted as tool;
- unsupported alias.

B. Parser/format error
- XML/raw JSON/function syntax not extracted;
- literal tool call leaked into final answer;
- streamed structured call fragmented.

C. Argument repair/schema error
- wrong key;
- missing output filename;
- enum/action mismatch;
- generic free-form parameter.

D. File/path error
- attachment basename not resolved;
- wrong persistent path after history reload;
- output directory issue.

E. Executor/native error
- function was correctly parsed/canonicalized, then Python/native implementation failed.

F. Conversation-state error
- selected UI history and Python SessionState diverged;
- attachments unavailable after reload;
- duplicate context insertion.

G. Thinking/observability error
- directive not sent;
- reasoning returned but not shown;
- diagnostics missing raw/canonical state.

After identifying the class:
- patch the smallest correct layer;
- add the user's exact failing shape to a validator;
- add at least one sibling/generalized case so the fix is systemic;
- run all existing v6 gates before creating a new APK.

## 18. Future release discipline

For v7 or later:

- versionCode must be >= `20`.
- keep package `ai.navixmind`.
- keep stable signing identity.
- keep ARM64-only unless explicitly changed.
- verify exact MLC runtime or document/verify any deliberate replacement.
- run 21-Skill/23-tool coverage and behavior matrices.
- run Python compile and Flutter Analyze.
- run full Android native build.
- inspect final APK package/version/cert/ABI/runtime.
- persist source and update this handoff before delivering.
- direct GitHub Release URL is the user-facing delivery method.

## 19. Documents to read in a fresh context

Read in this order:

1. `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6_CHECKPOINT_CURRENT.md` — this file, current master checkpoint.
2. `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6.md` — detailed v6 development history/root-cause record.
3. `.github/workflows/v6-validation.yml` — current deterministic build/release truth.
4. `scripts/validate_iteration_v6.py`
5. `scripts/validate_iteration_v6_extended.py`
6. `scripts/validate_iteration_v6_deep.py`
7. `python/navixmind/tools/compat.py`
8. `python/navixmind/tools/__init__.py`
9. `python/navixmind/agent.py`
10. `lib/features/chat/presentation/chat_screen.dart`
11. `lib/core/services/conversation_manager.dart`
12. `android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt`
13. `android/app/build.gradle`, with the packaging discrepancy warning above in mind.

## 20. Final handoff state

As of 2026-08-26:

- v6 development is complete enough to have produced a fully green CI release.
- the final signed APK exists and has been delivered to the user.
- the user has downloaded it.
- comprehensive real-device v6 testing has not yet been reported back.
- the next meaningful development input should be the user's v6 test results and copied diagnostics if failures occur.
- no capability should be removed merely to make the test suite pass.
- the primary goal remains maximizing actual local Qwen3-4B tool-call reliability across all 21 manually controlled Skills while preserving the parameter, benchmark, Thinking, diagnostics, history, cloud-tool and offline-agent functionality already added.

# RastaCoder Qwen3 Tool Reliability + Chat History v6 — Post-Release Handoff

Last verified against repository state: 2026-08-26
Repository: `zhangzheyuanviolin-ship-it/rastacoder`
Current development branch: `iteration/qwen3-tool-reliability-v6`
Branch HEAD observed immediately before this documentation update: `1fad59928c7f7380b1a2b8abc0dd4b8e50fa899b`
Base v5 source commit: `6c50af4917f7908da0cce9b0ec15646f35bd3f30`
Post-build persisted v6 source commit: `c17cedd9f56fff8256702387de7a621e59b78871`

## AUTHORITATIVE CURRENT STATE

v6 IS BUILT AND FORMALLY RELEASED.

The user has already downloaded the final v6 APK. At the moment this handoff is written, the user has NOT yet reported a complete real-device test result for v6.

Therefore the next agent/context must start from this exact state:

- Do not rebuild v6 merely because an older historical note says it was still pre-release.
- Do not start a speculative v7 rewrite before receiving the user's v6 real-device feedback, unless the user explicitly asks for further development first.
- CI/systemic validation passed; real-device behavior still requires empirical confirmation.
- Highest-priority real-device checks are tool-call reliability, Thinking visibility, tool diagnostics, persistent chat history/new-conversation behavior, and benchmark behavior.
- If the user reports a v6 tool failure, first request/use the new copyable per-response tool diagnostics whenever available, then map the failure to model output, parser/canonicalization, compatibility repair, path resolution, strict schema, executor, or native layer. Add the exact observed failure shape to a regression gate before the next release.

This file and `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6_CHECKPOINT_CURRENT.md` are the continuation documents. Any older statement saying “v6 has not been released yet” is historical and must be ignored.

## FINAL V6 RELEASE

Release name: `RastaCoder Qwen3 4B Tool Reliability + Chat History v6`

Release tag: `qwen3-tool-reliability-history-v6`

Release page:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/tag/qwen3-tool-reliability-history-v6`

Direct APK:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/releases/download/qwen3-tool-reliability-history-v6/RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`

Release workflow run:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32907785284`

Release-trigger commit:
`4d876cd7936c4526c25c1742d4ceb5b163eee907`

Persisted final source commit produced by the release workflow:
`c17cedd9f56fff8256702387de7a621e59b78871`

Final APK metadata:
- versionName: `0.0.5`
- versionCode: `19`
- package/applicationId: `ai.navixmind`
- APK filename: `RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`
- APK byte size: `499354824`
- APK SHA-256: `9f872f37802f7b362fc9a0f1f15f0d152b2e61c50cbde378e886bae9b2deb001`
- ABI: `arm64-v8a` only
- stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- stable signing certificate SHA-1: `74:5D:97:54:87:32:A9:DE:D0:96:6E:A5:58:8E:78:68:8F:85:31:B6`
- known-good MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- known-good MLC runtime byte size: `38786520`

The GitHub Release asset currently exists and has been downloaded. The user explicitly confirmed they downloaded it but had not yet tested it when this handoff was updated.

## NON-NEGOTIABLE PROJECT CONSTRAINTS

- Work only in `rastacoder` for this project.
- `local-agent-plaza` is read-only reference material. Never modify/build/release from it.
- Preserve package/applicationId `ai.navixmind`.
- Preserve the stable signing identity so future APKs remain in-place upgrades and do not force loss of app data or downloaded local models.
- Future release versionCode must be greater than `19`.
- Preserve the known-good ARM64 MLC runtime unless the user explicitly requests a runtime replacement.
- Keep release/test APKs ARM64-only unless the user changes that requirement.
- Deliver large APKs through direct GitHub Release/browser URLs, never sandbox links.
- Keep all 21 manually managed Skills and all 23 canonical local tool functions unless the user explicitly requests capability changes.
- Skill selection remains manual. No automatic Skill router without explicit approval.
- Thinking mode remains manual and independent from Skill selection.
- Context-token and max-output-token settings remain exact integer Token text fields; do not replace them with coarse sliders/presets unless requested.

## WHY V6 WAS NECESSARY

v4 was slow but the user confirmed multiple local tools worked, including TXT -> DOCX and audio conversion. v4 is the practical tool-reliability comparison point.

v5 added the 21-Skill UI, local parameter page, benchmark page, manual Thinking mode, and MLC phase telemetry, but real-device tool reliability regressed systemically.

User-confirmed v5 failures included:

1. Word creation: `create_docx` was called with `content` but no `output_path`, causing `[MODEL_TOOL_ARGUMENT_ERROR]` and an unnecessary request for a path.

2. Audio conversion: the model emitted literal final prose containing `<tool_call>{"name":"audio_processing","arguments":{"param":"convert analysis_article.mp3 to wav"}}</tool_call>`; the Skill ID was not executable, arguments were malformed, and the call leaked into normal assistant text.

3. TXT writing: the same general failure family appeared, including model tool-call text / imagined success without actual execution.

4. Thinking mode could not be empirically checked because the final chat UI did not reliably expose local model reasoning.

5. Tool errors lacked a complete copy/export diagnostic path.

6. Chat was effectively a single transient thread: visible messages lived in memory, history/new-conversation UI was missing, and restarting the app cleared the visible conversation.

## V6 TOOL RELIABILITY ARCHITECTURE

The 21 Skill IDs remain UI concepts only. The local model should see only enabled canonical executable functions and their exact parameter signatures.

Key behavior:
- model-facing prompt omits UI-only labels such as `audio_processing`, `word`, and `text_files` as callable names;
- model sees exact canonical names such as `ffmpeg_process`, `create_docx`, `write_file`;
- model sees exact parameter signatures;
- compatibility repair runs before strict schema rejection where a repair is deterministic and safe;
- legacy aliases and v5 Skill-name hallucinations are tolerated as fallback compatibility inputs;
- multi-tool Skill aliases such as `text_files`, `word`, `powerpoint`, and `excel` are routed deterministically from intent/arguments;
- generic `param/request/instruction/command` shapes are repaired when their meaning is safely recoverable;
- unique current attachments can be inferred when unambiguous;
- safe output filenames are synthesized for creation/conversion/modification tasks;
- recognizable malformed tool wrappers enter bounded repair/retry handling and must not silently leak as normal final prose;
- model-caused tool name/argument errors are returned to the ReAct loop as recoverable errors so the model can retry.

The exact user audio regression is a dedicated compatibility/test case. `audio_processing + param="convert analysis_article.mp3 to wav"` should normalize to canonical `ffmpeg_process` with the input file, generated WAV output, `operation=extract_audio`, and `params.format=wav`.

The Android native `convert` path is primarily video-oriented, so audio-target conversion is deliberately normalized to the native `extract_audio` branch for MP3/WAV/M4A/AAC/FLAC/OGG-style outputs.

## 21 SKILLS / 23 CANONICAL TOOLS

Current Skill catalog:

- `text_files` -> `read_file`, `write_file`, `file_info`
- `zip_archive` -> `create_zip`, `file_info`
- `pdf_read` -> `read_pdf`, `file_info`
- `pdf_create` -> `create_pdf`
- `document_convert` -> `convert_document`
- `word` -> `create_docx`, `read_docx`, `modify_docx`
- `powerpoint` -> `read_pptx`, `modify_pptx`
- `excel` -> `read_xlsx`, `modify_xlsx`
- `ocr` -> `ocr_image`
- `image_processing` -> `smart_crop`
- `video_processing` -> `ffmpeg_process`
- `audio_processing` -> `ffmpeg_process`
- `media_download` -> `download_media`
- `web_fetch` -> `web_fetch`
- `dynamic_web` -> `headless_browser`
- `basic_calculation` -> `python_execute`
- `scientific_calculation` -> `python_execute`
- `data_analysis` -> `python_execute`
- `charts` -> `python_execute`
- `gmail` -> `gmail`
- `google_calendar` -> `google_calendar`

Union of canonical functions remains exactly 23, with shared low-level functions deduplicated in the actual model schema.

## THINKING + DIAGNOSTICS

v6 preserves local reasoning separately from final answer where the runtime/model exposes displayable reasoning text.

Expected behavior:
- collapsed, accessible Thinking panel in chat;
- manual mode remains `model_default / enabled / disabled`;
- UI reports the selected/sent Thinking mode even if no displayable reasoning text is returned;
- reasoning does not get duplicated into the final answer or normal subsequent assistant history;
- per-response `工具调用诊断` panel can be expanded, copied, and shared;
- diagnostics are intended to distinguish model formatting, parser normalization, compatibility repair, path resolution, schema validation, executor error, and native error;
- API keys/OAuth tokens/authorization values must remain redacted.

For future failures, use copied diagnostics as primary evidence before speculative changes whenever possible.

## PERSISTENT CHAT HISTORY

v6 wires the repository's existing Isar `Conversation` / `Message` data layer and `ConversationManager` into the UI and Python SessionState.

Expected functionality:
- new conversation;
- persistent conversation history list;
- switch/load conversation;
- rename conversation;
- delete conversation;
- restore selected conversation after cold start;
- persist user/assistant/error messages and attachment paths;
- auto-title a new conversation from its first request;
- resync the same conversation into Python via `new_conversation` / `sync_full` so UI history and model context cannot silently diverge.

Critical invariant: switching a UI conversation must also switch/sync Python SessionState. Never implement a history UI that leaves the model using another thread's context.

## MLC STRUCTURED TOOL STREAM HARDENING

v6 also fixes native structured tool-call accumulation in `MLCInferenceChannel.kt`:
- accumulate `choice.delta.tool_calls` by actual streamed call index;
- reuse the same accumulator for fragments of the same call;
- merge argument fragments instead of allocating/replacing calls incorrectly.

This protects the structured function-call path if the MLC runtime/model emits streamed tool-call deltas instead of plain-text XML-style calls.

## V5 FEATURES RETAINED

v6 retains the v5 local model parameter page and benchmark page.

Local parameters include temperature, top_p, exact context tokens, exact max output tokens, and manual Thinking mode.

The benchmark implementation includes prefill/decode throughput, TTFT, end-to-end latency, memory metrics where available, result history, save, and clipboard copy. The user had not yet tested the benchmark at the time this handoff was written.

## VALIDATION / RELEASE STATUS

Formal release workflow Run `32907785284` completed successfully.

The final release path passed systemic validators around the tool contract and regression cases, Python compilation, Flutter static analysis, Android/Kotlin/Java/Chaquopy/MLC build, stable signing checks, package/version checks, ARM64 ABI checks, and known-good MLC runtime verification.

Dedicated regression coverage includes the user-reported TXT write, content-only DOCX creation, document conversion, MP3-to-WAV/Skill-alias failure family, parser leak prevention, Skill coverage, Thinking/diagnostics markers, persistent chat-history integration, and native structured-tool-call accumulation.

Important limitation: CI validation proves code/schema/build invariants and deterministic regression cases. It does not substitute for real Qwen3-4B behavior on the user's Android device. v6 must still be treated as awaiting empirical user acceptance.

## NEXT ACTION FOR ANY CONTINUING AGENT

1. Read this file and `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6_CHECKPOINT_CURRENT.md` first.
2. Inspect current branch source before editing; do not assume an older patch staging state.
3. Treat v6 as already released and downloaded by the user.
4. Wait for/use the user's actual v6 test feedback as the next development input.
5. If a failure is reported, capture its exact prompt, visible output, copied diagnostic log, enabled Skill(s), Thinking mode, attachment names, and whether the tool actually executed.
6. Add that exact failure as a deterministic regression case before producing a follow-up APK.
7. Preserve package/signing/runtime/in-place-upgrade constraints.
8. Do not remove the 21-Skill architecture solely to mask a parser/compatibility defect; fix the systemic layer if a new systemic defect is proven.

Current status in one sentence: **v6 has been formally released and downloaded by the user; repository/CI gates are green, while complete real-device v6 acceptance testing is still pending.**

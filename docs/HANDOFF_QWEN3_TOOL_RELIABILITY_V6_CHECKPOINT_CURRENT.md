# RastaCoder v6 — Current Continuation Checkpoint

Date: 2026-08-25
Branch: `iteration/qwen3-tool-reliability-v6`
Primary handoff: `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6.md`
Target release: `0.0.5` / versionCode `19`
Target tag: `qwen3-tool-reliability-history-v6`
Target APK: `RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`

This is the newest operational checkpoint. Read it first if the development context changes.

## User requirements that block release

The user rejected v5 because local Qwen3-4B tool calling regressed systemically after the 21-Skill grouping. v6 must repair the whole 21-Skill/23-canonical-tool chain, preserve manual Skill control, provide empirically inspectable Thinking behavior, copy/share diagnostics, and persistent multi-conversation chat management. The exact user failure families include TXT writing, content-only DOCX creation, MP3-to-WAV conversion, Skill IDs emitted as tool names, generic `param` calls, raw `<tool_call>` leakage into final prose, and hallucinated success after a call was never executed.

## Complete v6 deterministic patch order

Starting from exact persisted v5 source commit `6c50af4917f7908da0cce9b0ec15646f35bd3f30`:

1. `scripts/run_iteration_v6.py` — core systemic tool reliability, parser retry, base Thinking/diagnostics.
2. `scripts/apply_iteration_v6_reliability2.py` — generalized TXT/DOCX/PDF free-form creation recovery.
3. `scripts/apply_iteration_v6_reliability3.py` — third-pass systemic aliases, destination inference, Word routing, ZIP/document/media/Office/Calendar hardening, true raw model-call diagnostics. This file is a syntax-safe replay wrapper around immutable source commit `b51c293bf33084e779618e3706122d5ae0489b64`.
4. `scripts/apply_iteration_v6_ui.py` — accessible collapsed Thinking and diagnostic panels plus copy/share.
5. `scripts/apply_iteration_v6_observability2.py` — explicitly reports whether `/think`, `/no_think`, or model-default was sent and whether displayable reasoning returned.
6. `scripts/apply_iteration_v6_history.py` — initializes existing Isar Conversation/Message/ConversationManager and wires new/history/switch/rename/delete/auto-title to ChatScreen and Python SessionState.
7. `scripts/apply_iteration_v6_history2.py` — fixes cold-start `runApp(initializing:true)` -> `runApp(initializing:false)` lifecycle via `didUpdateWidget`.
8. `scripts/apply_iteration_v6_history3.py` — persists incoming attachment paths before database storage and attaches created output files to persisted assistant messages so history reload can rebuild Python file maps.
9. `scripts/apply_iteration_v6_native.py` — fixes MLC streamed structured tool-call accumulation by actual call index and merges argument fragments.

## Full release gates

Three validators now run before and after native build:
- `scripts/validate_iteration_v6.py` — established 21-Skill/23-tool systemic gate. It is a small replay wrapper over the established validator retained in commit `d7e09da6f5e288ef71bb3c8ffde34d755796f5e3`; only its stale parser source-string assertion was updated to accept the new auditable `parser_repairs` variable.
- `scripts/validate_iteration_v6_extended.py` — representative required-argument satisfaction for every canonical tool plus exact TXT/DOCX/audio families and MLC/history checks.
- `scripts/validate_iteration_v6_deep.py` — single-Skill prompt isolation for all 21 Skills, canonical required-signature presence, extra ZIP/document/media/Office/Calendar aliases, full LocalLLMClient parser no-leak tests, raw model-call preservation, explicit Thinking directive display, durable history attachment gates.

Additional gates:
- Python compile.
- Flutter Analyze.
- exact known-good MLC runtime restoration and SHA/size verification.
- full Flutter Android native build (Kotlin/Java/Chaquopy/MLC).
- release APK package/version/signing certificate/ARM64-only/runtime verification.

## Validation history and current state

Run 7 completed fully green for the pre-history3/pre-reliability3 chain:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32864312731`

Run 8 failed at patch-script syntax compilation and published nothing:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32866141935`

Run 9 compiled patches but failed because the third-pass patch expected a deliberately repeated anchor to occur once. It published nothing:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32866415736`

Run 10 applied the complete patch chain successfully. It then exposed one stale source-string assertion in the old base validator after `parser_repairs` was added. It published nothing:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32866562649`

Current run 11:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32866696097`
Head: `05e8bfaaa8f632e7124edab670790bcc01670c4b`

At the latest check run 11 has passed:
- exact v5 reconstruction and v5 baseline invariants;
- compilation and application of the complete nine-stage v6 patch chain;
- all three systemic/deep 21-Skill/23-tool regression validators;
- Python source compilation;
- Flutter dependencies;
- Flutter Analyze;
- known-good MLC runtime verification.

It is currently inside the full Android native compile gate. No APK has been released yet.

## Release workflow

`.github/workflows/v6-release.yml` is updated to the same complete nine-stage patch chain and the same three validators. It builds version `0.0.5` / versionCode `19`, restores the stable RastaCoder development signing identity, verifies `ai.navixmind`, ARM64-only ABI, certificate SHA-256, and exact MLC runtime, persists final v6 source, then creates tag `qwen3-tool-reliability-history-v6`.

The release workflow has a narrowly scoped push trigger only for:
`docs/RELEASE_V6_TRIGGER.md`

Do NOT create that trigger file until run 11 is completely green. The workflow also retains manual `workflow_dispatch`.

## Release identity constraints

- package: `ai.navixmind`
- versionName: `0.0.5`
- versionCode: `19`
- signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- MLC runtime size: `38786520`
- ABI: `arm64-v8a` only

## Immediate continuation steps

1. Confirm run 11 completes native build, post-build three-validator rerun and summary fully green.
2. If any gate is red, fetch the failed job log and fix it before release.
3. When run 11 is fully green, create `docs/RELEASE_V6_TRIGGER.md` once to trigger formal release.
4. Monitor release through signed APK verification, final source persistence and GitHub Release publication.
5. Fetch final release asset size/SHA-256, release run ID, final persisted source commit and direct APK URL.
6. Update the primary handoff and this checkpoint with final evidence.
7. Deliver the direct GitHub APK/release URL only; no sandbox APK link.

## Correct final confidence wording

CI cannot mathematically guarantee that a 4B generative model will choose a correct tool call on every handset prompt. The justified claim after green release is that v6 removes the identified systemic prompt/Skill-ID/parser/argument/path/stream/history defects, directly regression-tests the user's failure families plus broader equivalents across all 21 Skills and 23 canonical contracts, and passes the full Android build plus final APK identity/runtime verification. Real handset testing remains the final empirical check.
# RastaCoder v6 — Current Continuation Checkpoint

Date: 2026-08-25
Branch: `iteration/qwen3-tool-reliability-v6`
Primary handoff: `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6.md`
Target release: `0.0.5` / versionCode `19`

This file is the newest checkpoint and should be read together with the primary handoff if the development agent/context changes.

## Current user requirements

The user has rejected v5 as having systemic local-tool regressions. The next release must address the whole 21-Skill/23-tool call chain, not only individual Word/audio/TXT examples. It must also add verifiable Thinking visibility, copy/share tool diagnostics, and persistent multi-conversation chat management (new chat + history list/switch/rename/delete + restart restoration).

## Latest root-cause/audit addition

A cold-start lifecycle race was found after the main history patch was staged:

- `main.dart` intentionally calls `runApp(NavixMindApp(initializing: true))` before database/service initialization.
- It calls `runApp(NavixMindApp(initializing: false, isar: isar))` again after initialization.
- Flutter may retain the existing `ChatScreen` State across this widget update.
- Therefore history initialization only in `ChatScreen.initState()` is insufficient when the original widget was created with `initializing=true`.

Fix staged in:
`scripts/apply_iteration_v6_history2.py`

It adds `ChatScreen.didUpdateWidget()` and explicitly handles `oldWidget.initializing && !widget.initializing && !_conversationLoaded`, scheduling `_initializeConversationHistory()` after the frame. This makes cold-start history restoration deterministic instead of timing-dependent.

## Current patch application order

1. restore exact v5 source/baseline as required by the workflow;
2. `scripts/run_iteration_v6.py` — core systemic tool reliability patch;
3. `scripts/apply_iteration_v6_reliability2.py` — generalized TXT/DOCX/PDF free-form creation recovery;
4. `scripts/apply_iteration_v6_ui.py` — Thinking + diagnostic observability;
5. `scripts/apply_iteration_v6_history.py` — Isar conversation history/new-chat integration;
6. `scripts/apply_iteration_v6_history2.py` — cold-start lifecycle race hardening;
7. `scripts/apply_iteration_v6_native.py` — MLC streamed structured-call accumulation fix.

## Validation state

Current full validation run:
`https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32864312731`

Run number: 7
Head when triggered: `c92ec4369117939e8a4548599a3530e4b7360f22`

At the latest check it had passed:
- known-good baseline restore;
- exact deterministic v5 reconstruction;
- v5 baseline invariant gate;
- compilation of all v6 patch runners/validators including `history2`;
- complete v6 patch application;
- both 21-Skill/23-tool systemic regression matrices;
- exact TXT/DOCX/audio regression families;
- representative required-argument satisfaction for all 23 canonical tools;
- Python compile;
- Flutter dependency install;
- Flutter Analyze;
- exact known-good MLC runtime restoration.

It is currently in the full Flutter Android native compile gate (`flutter build apk --debug --build-name=0.0.5 --build-number=19`). After that, both validators and the cold-start marker gate run again. This validation workflow does not publish an APK.

## Release workflow

Manual-only release workflow exists at:
`.github/workflows/v6-release.yml`

Latest release-workflow commit including `history2`:
`9665f6c69cae3390627c076dad24d1a65d2cf3cc`

It is intentionally NOT triggered yet. Do not release until the current full validation run is completely green.

Once validation is green, the release workflow must be triggered. If no workflow-dispatch action is available through the connector, add a narrowly scoped push trigger on `.github/workflows/v6-release.yml`, causing the workflow-file update itself to start the release. The release workflow restores exact persisted v5 source commit `6c50af4917f7908da0cce9b0ec15646f35bd3f30`, applies the complete v6 chain including `history2`, revalidates, builds with stable signing, verifies package/version/certificate/ARM64/runtime, persists final v6 source, and publishes GitHub Release tag `qwen3-tool-reliability-history-v6`.

## Release identity constraints

- package: `ai.navixmind`
- versionName: `0.0.5`
- versionCode: `19`
- signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- ABI: `arm64-v8a` only
- expected APK filename: `RastaCoder-Qwen3-4B-tool-reliability-history-v6-update.apk`
- expected tag: `qwen3-tool-reliability-history-v6`

## Remaining steps

1. Confirm validation run 7 finishes fully green.
2. If red, read completed job logs and fix before release.
3. If green, trigger the formal release workflow.
4. Monitor release build through final APK verification and GitHub Release publication.
5. Fetch final asset metadata, APK SHA-256/size, final persisted source commit, and release URLs.
6. Update the primary handoff with final delivery evidence and residual-risk statement.
7. Deliver only the direct GitHub APK/release URL to the user; no sandbox APK link.

## Residual-risk wording for final delivery

Do not claim that synthetic/CI validation mathematically guarantees Qwen3-4B will produce a correct call every time on handset. The proper claim is that v6 removes the identified systemic prompt/alias/parser/argument/path/MLC/history defects, directly regression-tests the exact user failure families, exercises every Skill and every canonical tool contract, and passes the full Android build. Final empirical confidence still comes from handset testing with the real local model.

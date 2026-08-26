# V12 Live Progress / Emergency Handoff

Branch: `iteration/qwen3-workspace-alias-hardening-v12`
Baseline: exact verified V11 final source HEAD `6911c61bb42fc33cbe0f4bea1b22970fc3f1a727`
Started: 2026-08-26

## User real-device failure that triggered V12

The first V11 local-model task failed:

User request: inspect the workspace directory and report files.

Model emitted:
```json
{"name":"list_files","arguments":{"path":"/workspace","recursive":false,"pattern":null,"include_directories":true}}
```

Execution log reached `paths_resolved` with the path still exactly `/workspace`, then failed:
`Directory not found or inaccessible: /workspace`

The model then ended the turn and told the user it could not access the workspace.

## Immediate confirmed defect

V11 did not canonicalize the absolute workspace alias `/workspace` to the app's real workspace/output root. The V11 implementation primarily normalized relative aliases such as `.`, `output`, and `workspace`. Because `/workspace` remained an absolute filesystem path, the executor attempted to access a literal OS path that does not exist in the Android runtime.

This means the V11 workspace hardening was incomplete. The prior diagnosis covered several real bugs, but it did not close the complete model-facing path contract.

## V12 non-negotiable goals

1. Audit the exact V11 final source before modifying behavior further.
2. Define one canonical model-facing workspace namespace that accepts the forms small models naturally generate, including at minimum `.`, `workspace`, `output`, `/workspace`, `/output`, and safe workspace-relative nested paths.
3. Ensure list/read/write/modify/delete/file-info/archive/Office/media follow-up operations resolve the same namespace consistently.
4. Do not let a model-generated virtual workspace alias escape into literal Android/Linux absolute-path handling.
5. Preserve legitimate explicitly supported Android common roots (downloads/documents/pictures/screenshots/camera) and uploaded-file resolution.
6. Add exact regression coverage for the user's literal failing call `path="/workspace"`.
7. Add systemic regression cases for other likely absolute virtual aliases and multi-step workspace workflows.
8. Audit model prompt/schema guidance so Qwen3-4B is strongly biased toward the canonical workspace path and can recover from a path error without immediately ending the task.
9. Preserve V11 OpenAI-compatible provider and all inherited V9/V10/V11 gates.
10. Follow release discipline: one deterministic no-APK preflight; only after it is green, one formal stable-signed ARM64 APK build/release.

## Work status

- [x] Created V12 branch from exact V11 final HEAD.
- [x] Recorded the user's exact failure and first confirmed defect in-repo before code changes.
- [ ] Fetch/audit exact V11 workspace resolver, compatibility normalization, tool schema/prompt, executor error-recovery code, and V11 handoff.
- [ ] Identify all root causes exposed by this failure, including any second-order recovery/prompt issue.
- [ ] Patch V12.
- [ ] Add exact and systemic validator coverage.
- [ ] Commit progress checkpoints after each major phase.
- [ ] Run no-APK preflight.
- [ ] Run one formal release build only after preflight is green.
- [ ] Persist verified source + final handoff with hashes/URLs.

## Handoff rule if this agent is interrupted

Continue only from this branch and this document. Do not restart from main or from an earlier V11 patch script. Re-read the user's literal failure above, fetch the exact files listed in the audit section once populated, and continue from the latest commit on this branch. Do not trigger an APK build until the deterministic V12 validator and inherited gates are green in a no-APK preflight.

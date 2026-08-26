# V12 release gate checkpoint

Branch: `iteration/qwen3-workspace-alias-hardening-v12`

## Preflight history

### First no-APK preflight
- Run: `32966081018`
- Result: FAILURE in the new V12-only logical-path gate.
- V9, V10 and V11 inherited gates had already passed.
- Failure exposed a real second-order defect: `execute_tool()` resolved `list_files(path='.')` to the physical workspace before `list_files` executed, so the model-facing `requested_path` leaked the physical workspace root.
- No APK build was triggered.

### Precise fix
- Script: `scripts/apply_iteration_v12_list_boundary_fix.py`
- Generated marker: `RASTACODER_V12_PRESERVE_LIST_LOGICAL_PATH`
- `list_files` now retains its normalized logical path through the executor boundary and resolves it internally using the configured workspace root.

### Second no-APK preflight
- Run: `32966400251`
- Result: SUCCESS.
- Passed patch compilation/application, generated Python compilation, V9, V10, V11 and V12 functional gates, Java/Flutter setup, Flutter dependency resolution and Flutter static analysis.
- Exact `list_files(path='/workspace')` regression is green.
- Model-facing listing contains logical paths and no physical workspace root.

## Formal release authorization

The deterministic release gate is now satisfied. Exactly one formal V12 stable-signed ARM64 APK build may be triggered.

Formal release workflow:
`.github/workflows/v12-release.yml`

Planned artifact identity:
- package: `ai.navixmind`
- versionName: `0.0.11`
- versionCode: `25`
- tag: `qwen3-workspace-alias-hardening-v12`
- APK: `RastaCoder-Qwen3-4B-workspace-alias-hardening-v12-update.apk`
- expected stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- expected MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`

If the current agent is interrupted now, read `docs/V12_LIVE_PROGRESS_AND_HANDOFF.md` and this checkpoint. Trigger the formal release only once. If it fails, inspect the exact failed step before making any code/workflow change; do not blindly rebuild.

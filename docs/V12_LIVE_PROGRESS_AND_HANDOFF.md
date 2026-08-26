# V12 Live Progress / Emergency Handoff

Branch: `iteration/qwen3-workspace-alias-hardening-v12`
Baseline: exact verified V11 final source HEAD `6911c61bb42fc33cbe0f4bea1b22970fc3f1a727`
Started: 2026-08-26

## User real-device failure that triggered V12

User asked the local Qwen3-4B model to inspect the workspace and report its files. The model emitted:
```json
{"name":"list_files","arguments":{"path":"/workspace","recursive":false,"pattern":null,"include_directories":true}}
```
The V11 diagnostics reached `paths_resolved` with `/workspace` unchanged and failed with:
`Directory not found or inaccessible: /workspace`.
The next local-model response ended the turn instead of recovering.

## Exact V11 audit completed

Audited from exact V11 final source:
- `python/navixmind/tools/compat.py`
- `python/navixmind/tools/__init__.py`
- `python/navixmind/tools/extended_tools.py`
- `python/navixmind/agent.py`
- `scripts/apply_iteration_v11_workspace_openai.py`
- `scripts/validate_iteration_v11.py`
- `.github/workflows/v11-preflight.yml`
- `docs/HANDOFF_QWEN3_WORKSPACE_OPENAI_COMPAT_V11.md`

### Confirmed V11 root causes

1. V11 compatibility recognized relative aliases `.`, `output`, `workspace`, but omitted `/workspace`, `/output`, and nested virtual absolute aliases. The user's literal call therefore recorded no repair.
2. Global `_workspace_relative_path()` returned every absolute path unchanged before virtual-workspace interpretation. `/workspace` therefore escaped the V11 mapping layer.
3. `extended_tools._resolve_workspace_path()` and `_resolve_list_target()` repeated the same absolute-path bypass at a lower layer.
4. `_tool_error_for_model()` supplied no workspace-specific recovery for `Directory not found`; Qwen3-4B was free to end the turn after one failure. The general prompt's file-not-found guidance also leaned toward asking for reattachment, which is wrong for workspace discovery.
5. Successful V11 `list_files` results still exposed physical `directory`, `workspace_root`, and `entries[*].path` values to the model, undermining the intended logical workspace namespace during multi-step tasks.

## V12 implementation

Primary patch:
`scripts/apply_iteration_v12_workspace_alias_hardening.py`

Primary validator:
`scripts/validate_iteration_v12.py`

The patch creates `python/navixmind/tools/path_contract.py` and implements one explicit logical model namespace:
- workspace root: `.`
- accepted compatibility aliases: `workspace`, `output`, `/workspace`, `/output`, including nested forms
- supported logical Android roots: `downloads`, `documents`, `pictures`, `screenshots`, `camera`, including defensive leading-slash variants
- uploaded/trusted real absolute paths remain valid
- traversal outside selected logical roots remains rejected

The patch also:
- normalizes `/workspace` to `.` before execution
- makes executor and extended file tools use the same central resolver
- strengthens the local prompt/schema to tell Qwen3-4B to use `path='.'` for workspace root
- adds workspace-specific retry guidance after list/path errors
- converts `list_files` entries back to logical paths before local/cloud-compatible model prefill so physical app paths are not taught back to the model

## First V12 no-APK preflight — intentionally stopped a residual defect

Run: `32966081018`
URL: `https://github.com/zhangzheyuanviolin-ship-it/rastacoder/actions/runs/32966081018`
Result: FAILURE, no APK produced.

Passed before the V12-specific failure:
- patch/validator compile
- patch application
- generated Python compile
- V9 inherited gates
- V10 inherited gates
- V11 inherited workspace/OpenAI-compatible gates

V12-specific failure traceback showed the actual model payload still contained:
`workspace_path: /tmp/<physical-workspace>`
while `entries[*]` had already been correctly logicalized.

### Second-order cause discovered by preflight

`execute_tool()` globally resolved `list_files(path='.')` into the physical `output_dir` before `extended_tools.list_files()` ran. The listing itself therefore succeeded, but `list_files.requested_path` received the physical path. `_list_files_payload_for_model()` faithfully emitted that value as `workspace_path`, creating one remaining physical-path leak.

This is a real implementation defect; the validator is correct and must remain strict.

### Precise boundary fix

Added:
`scripts/apply_iteration_v12_list_boundary_fix.py`

Marker in generated source:
`RASTACODER_V12_PRESERVE_LIST_LOGICAL_PATH`

Behavior:
- `execute_tool()` does not run `list_files.path` through the generic input-path resolver.
- `list_files` retains the normalized logical path (`.`, `folder/sub`, `downloads/...`).
- `list_files` itself resolves that logical path to the physical target using `resolve_list_path(..., _output_dir)`.
- all other tools keep the universal physical input-path resolver.
- exact `/workspace` device call still becomes `.` in compatibility normalization before this boundary.
- the model-facing `requested_path` can therefore remain `.` instead of the private filesystem root.

## V12 exact/systemic regression requirements

The V12 validator requires all of the following:
1. Exact user call `list_files(path='/workspace', recursive=false, ...)` succeeds against the real configured workspace.
2. `/output` is equivalent to workspace root.
3. `/workspace/folder/sub` resolves correctly.
4. `/workspace/...` can be reused by `read_file`.
5. `/workspace/generated.txt` writes inside the configured workspace rather than literal Linux `/workspace`.
6. Lower extended-tool resolver independently follows the same contract.
7. Leading-slash logical Android roots are normalized safely.
8. `/workspace/../...` traversal is rejected.
9. Model-facing list payload contains logical paths and contains no physical workspace root.
10. Prompt/schema explicitly teach `path='.'`.
11. `Directory not found` recovery explicitly instructs one corrected `path='.'` retry.
12. Trusted real absolute attachment paths remain usable.
13. All inherited V9/V10/V11 gates remain green.

## Release discipline

- No APK build has been triggered during V12 debugging.
- First no-APK preflight caught the residual boundary leak before release.
- A second deterministic no-APK preflight will run the primary patch plus the precise boundary fix and all inherited/new gates.
- Only after that entire preflight is green may one formal stable-signed ARM64 V12 APK build/release be triggered.
- No random APK build/release trial-and-error.

## Work status

- [x] Created V12 branch from exact V11 final HEAD.
- [x] Recorded user failure before code changes.
- [x] Completed exact V11 root-cause audit.
- [x] Implemented central V12 path contract and model-facing logical list results.
- [x] Added exact + systemic V12 validator.
- [x] Ran first no-APK preflight; inherited V9/V10/V11 gates all green.
- [x] Diagnosed first preflight V12 failure as a real logical/physical boundary leak.
- [x] Added precise `list_files` executor-boundary fix.
- [ ] Run second deterministic no-APK preflight with boundary fix.
- [ ] If and only if fully green, create/run one formal V12 release build.
- [ ] Persist verified generated source and final V12 handoff.
- [ ] Record final APK/release metadata, source HEAD, checksums, run URLs.

## Emergency handoff rule

If this agent is interrupted, continue only from `iteration/qwen3-workspace-alias-hardening-v12` and read this document first. Use the latest branch commit. The generated V12 source is produced by applying, in this order:
1. `scripts/apply_iteration_v12_workspace_alias_hardening.py`
2. `scripts/apply_iteration_v12_list_boundary_fix.py`

Then run inherited V9/V10/V11 validators and `scripts/validate_iteration_v12.py`. Do not trigger an APK build until the dedicated second no-APK preflight is completely green. Preserve V11 OpenAI-compatible support, package/signing identity, MLC runtime, 25-Skill/37-tool invariant, and all inherited gates.

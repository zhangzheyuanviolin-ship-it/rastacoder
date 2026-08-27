# RastaCoder Qwen3 Local Tool Contract Recovery v17 — verified release handoff

Branch: `iteration/qwen3-local-tool-contract-recovery-v17`
Release tag: `qwen3-local-tool-contract-recovery-v17`
Version: `0.0.16` / code `30`
Package: `ai.navixmind`
Full no-APK preflight: `33052838100`
MLC/native binary probe: `33041507127`

## Product priority and historical diagnosis
- Local-model tool calling is the primary product capability. Cloud-provider tool calling remains secondary and must never regress the on-device path.
- The copied V16 phone diagnostic showed Qwen3-4B emitting `list_files(path="/")` for the logical workspace root; the raw slash survived normalization and path resolution, reached Android `/`, and failed with EACCES.
- The latent code defect entered with the V12 central path contract. It recognized `.`, `workspace`, `output`, `/workspace` and `/output`, while bare `/` was omitted and could fall through to the generic absolute-path branch.
- V13 through V16 inherited the same underlying hole. V14 is the last release explicitly user-confirmed on device with local Qwen3-4B tools working, so V17 keeps every later runtime/cloud fix while restoring and hardening the local-first contract.

## V17 systemic path and trust recovery
- Bare `/` is a first-class logical workspace-root alias at the central path layer.
- The 3B-4B compatibility ABI independently normalizes `list_files(path="/")` to `path="."` and records the repair.
- The rule is generalized to the entire path family: model-invented `/foo.txt`, `/folder/result.pdf`, `/data/...`, `/system/...` and similar absolute-looking paths are workspace-relative unless they belong to documented Android public roots or were explicitly trusted by application state.
- Attachment trust is explicit. The executor derives an exact absolute-path whitelist from `context['_file_map']`; merely guessing an existing filesystem path does not make it trusted.
- CI uses the runner's real existing `/etc/passwd` as a negative case and verifies it is virtualized under the workspace when it is absent from the whitelist.
- CI creates a real external attachment as the positive case, then verifies `read_file` can read it through the file map and `file_manage copy` can copy it into the workspace through both path-resolution layers.
- Existing paths inside the workspace and documented Android logical roots remain usable.
- Generated destinations are always workspace-owned. `output_path`, `extract_zip.output_dir` and `file_manage.destination_path` go through the strict output boundary and never inherit attachment trust.
- Scalar path keys, array path keys and nested Office operation paths all use the same explicit-trust policy.
- Model-facing list results are logicalized before reinjection, so private app filesystem paths are not taught back to the 4B model for its next call.

## V17 complete local-tool audit
- Exactly 25 manually controlled Skills remain present.
- The union of enabled local Skills exposes exactly 37 canonical functions, matching the canonical registry.
- The projected 4B schemas contain all 37 functions and every canonical function retains a compact local prompt hint.
- CI automatically inventories every path-bearing field exposed across the 37 local schemas. A future new `*_path`, `*_paths` or `*_dir` field changes the inventory and forces a deliberate central-path audit instead of silently bypassing it.
- The exact V16 phone call is replayed through compatibility, shared path resolution, direct tool execution and the executor boundary.
- Manual Skill enforcement is explicitly tested after compatibility repair so a disabled function cannot be repaired into an executable call.
- Structured 4B compatibility is strengthened for `file_manage`, `list_zip`, `extract_zip`, `pdf_manage`, `create_pptx`, `create_xlsx`, `image_compose`, `convert_document`, `anysearch_extract` and `anysearch_get_sub_domains` using deterministic aliases/container repairs only.
- Safe deterministic output filenames cover local creation/conversion operations where the app can choose a filename itself, reducing small-model failures caused by root-only or missing output paths.
- File, Office, archive, PDF, image, media, Python, search and connected-service tool surfaces retain inherited V9-V16 safeguards.
- Every V9-V17 host regression is run before the build and again against the verified release source after the single formal build.

## Runtime/build invariants retained
- Exact known-good MLC runtime remains unchanged.
- Exactly the five already-verified MLC model libraries remain registered; V17 adds no unverified model library.
- Chaquopy Python 3.13, cffi 1.17.1 and pinned curl-cffi 0.16.2 Android ARM64 payload remain under V15/V16 compatibility/native gates.
- Stable package ID and signing identity remain unchanged.
- Formal output is ARM64-only and is produced by exactly one `flutter build apk` command after the locked no-APK preflight succeeds.

## Final verified artifact
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- curl-cffi private native companion: `libc++_shared-d523468d.so`
- curl-cffi private companion SHA-256: `4f46ac4bd5f3f2f16e7c34bef7a7f65544d91bdc18853f201cf588e1d3d604c3`
- APK SHA-256: `689e736da9723d9ce37425ba39920600724a8bb3e187557bf0744d36800eea13`
- APK size: `527182699` bytes

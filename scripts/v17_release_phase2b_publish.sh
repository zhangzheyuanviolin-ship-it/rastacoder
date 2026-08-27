#!/usr/bin/env bash
set -euo pipefail

: "${EXPECTED_RUNTIME_SHA256:?}"
: "${EXPECTED_CERT_SHA256:?}"
: "${EXPECTED_PACKAGE:?}"
: "${BUILD_NAME:?}"
: "${BUILD_NUMBER:?}"
: "${OUTPUT_APK:?}"
: "${RELEASE_TAG:?}"
: "${PREFLIGHT_RUN:?}"
: "${RUNTIME_PROBE_RUN:?}"
: "${PRIVATE_CURL_LIB:?}"
: "${GH_TOKEN:?}"

test -s /tmp/v17-release.env
# shellcheck disable=SC1091
source /tmp/v17-release.env
test -s "$OUTPUT_APK"
test -n "$OUT_SHA"
test -n "$OUT_SIZE"
test "$CERT_SHA" = "$EXPECTED_CERT_SHA256"
test -n "$PRIVATE_SHA"

python3 -m pip install --upgrade pip
python3 -m pip install \
  anthropic requests beautifulsoup4 lxml pypdf reportlab \
  python-docx python-pptx openpyxl Pillow yt-dlp \
  'numpy<2' 'pandas<3' 'matplotlib<4'
python3 scripts/run_validate_iteration_v9.py
python3 scripts/validate_iteration_v10.py
python3 scripts/validate_iteration_v11.py
python3 scripts/validate_iteration_v12.py
python3 scripts/validate_iteration_v13.py
python3 scripts/validate_iteration_v14.py
python3 scripts/validate_iteration_v15.py
python3 scripts/validate_iteration_v15_curl_cffi_compat.py
python3 scripts/validate_iteration_v16.py
python3 scripts/validate_iteration_v17.py

test "$(sha256sum "$OUTPUT_APK" | awk '{print $1}')" = "$OUT_SHA"
test "$(stat -c '%s' "$OUTPUT_APK")" = "$OUT_SIZE"

rm -f android/app/rastacoder-dev.p12 android/key.properties android/local.properties upstream-known-good.apk
rm -rf android/app/vendor
rm -f "android/app/src/main/jniLibs/arm64-v8a/$PRIVATE_CURL_LIB"

cat > docs/HANDOFF_QWEN3_LOCAL_TOOL_CONTRACT_RECOVERY_V17.md <<EOF
# RastaCoder Qwen3 Local Tool Contract Recovery v17 — verified release handoff

Branch: \`iteration/qwen3-local-tool-contract-recovery-v17\`
Release tag: \`$RELEASE_TAG\`
Version: \`$BUILD_NAME\` / code \`$BUILD_NUMBER\`
Package: \`$EXPECTED_PACKAGE\`
Full no-APK preflight: \`$PREFLIGHT_RUN\`
MLC/native binary probe: \`$RUNTIME_PROBE_RUN\`

## Product priority and historical diagnosis
- Local-model tool calling is the primary product capability. Cloud-provider tool calling remains secondary and must never regress the on-device path.
- The copied V16 phone diagnostic showed Qwen3-4B emitting \`list_files(path="/")\` for the logical workspace root; the raw slash survived normalization and path resolution, reached Android \`/\`, and failed with EACCES.
- The latent code defect entered with the V12 central path contract. It recognized \`.\`, \`workspace\`, \`output\`, \`/workspace\` and \`/output\`, while bare \`/\` was omitted and could fall through to the generic absolute-path branch.
- V13 through V16 inherited the same underlying hole. V14 is the last release explicitly user-confirmed on device with local Qwen3-4B tools working, so V17 keeps every later runtime/cloud fix while restoring and hardening the local-first contract.

## V17 systemic path and trust recovery
- Bare \`/\` is a first-class logical workspace-root alias at the central path layer.
- The 3B-4B compatibility ABI independently normalizes \`list_files(path="/")\` to \`path="."\` and records the repair.
- The rule is generalized to the entire path family: model-invented \`/foo.txt\`, \`/folder/result.pdf\`, \`/data/...\`, \`/system/...\` and similar absolute-looking paths are workspace-relative unless they belong to documented Android public roots or were explicitly trusted by application state.
- Attachment trust is explicit. The executor derives an exact absolute-path whitelist from \`context['_file_map']\`; merely guessing an existing filesystem path does not make it trusted.
- CI uses the runner's real existing \`/etc/passwd\` as a negative case and verifies it is virtualized under the workspace when it is absent from the whitelist.
- CI creates a real external attachment as the positive case, then verifies \`read_file\` can read it through the file map and \`file_manage copy\` can copy it into the workspace through both path-resolution layers.
- Existing paths inside the workspace and documented Android logical roots remain usable.
- Generated destinations are always workspace-owned. \`output_path\`, \`extract_zip.output_dir\` and \`file_manage.destination_path\` go through the strict output boundary and never inherit attachment trust.
- Scalar path keys, array path keys and nested Office operation paths all use the same explicit-trust policy.
- Model-facing list results are logicalized before reinjection, so private app filesystem paths are not taught back to the 4B model for its next call.

## V17 complete local-tool audit
- Exactly 25 manually controlled Skills remain present.
- The union of enabled local Skills exposes exactly 37 canonical functions, matching the canonical registry.
- The projected 4B schemas contain all 37 functions and every canonical function retains a compact local prompt hint.
- CI automatically inventories every path-bearing field exposed across the 37 local schemas. A future new \`*_path\`, \`*_paths\` or \`*_dir\` field changes the inventory and forces a deliberate central-path audit instead of silently bypassing it.
- The exact V16 phone call is replayed through compatibility, shared path resolution, direct tool execution and the executor boundary.
- Manual Skill enforcement is explicitly tested after compatibility repair so a disabled function cannot be repaired into an executable call.
- Structured 4B compatibility is strengthened for \`file_manage\`, \`list_zip\`, \`extract_zip\`, \`pdf_manage\`, \`create_pptx\`, \`create_xlsx\`, \`image_compose\`, \`convert_document\`, \`anysearch_extract\` and \`anysearch_get_sub_domains\` using deterministic aliases/container repairs only.
- Safe deterministic output filenames cover local creation/conversion operations where the app can choose a filename itself, reducing small-model failures caused by root-only or missing output paths.
- File, Office, archive, PDF, image, media, Python, search and connected-service tool surfaces retain inherited V9-V16 safeguards.
- Every V9-V17 host regression is run before the build and again against the verified release source after the single formal build.

## Runtime/build invariants retained
- Exact known-good MLC runtime remains unchanged.
- Exactly the five already-verified MLC model libraries remain registered; V17 adds no unverified model library.
- Chaquopy Python 3.13, cffi 1.17.1 and pinned curl-cffi 0.16.2 Android ARM64 payload remain under V15/V16 compatibility/native gates.
- Stable package ID and signing identity remain unchanged.
- Formal output is ARM64-only and is produced by exactly one \`flutter build apk\` command after the locked no-APK preflight succeeds.

## Final verified artifact
- ABI: \`arm64-v8a\` only
- Stable signing certificate SHA-256: \`$EXPECTED_CERT_SHA256\`
- MLC runtime SHA-256: \`$EXPECTED_RUNTIME_SHA256\`
- curl-cffi private native companion: \`$PRIVATE_CURL_LIB\`
- curl-cffi private companion SHA-256: \`$PRIVATE_SHA\`
- APK SHA-256: \`$OUT_SHA\`
- APK size: \`$OUT_SIZE\` bytes
EOF

cat > docs/V17_LIVE_PROGRESS_AND_HANDOFF.md <<EOF
# RastaCoder V17 local-first final recovery progress and handoff

- Full V9-V17 no-APK preflight \`$PREFLIGHT_RUN\`: SUCCESS.
- Exact MLC/native binary probe \`$RUNTIME_PROBE_RUN\`: SUCCESS.
- V12 introduced the latent missing bare-slash alias; V13-V16 inherited it. V14 is the last user-confirmed real-device local-tool-good checkpoint.
- Exact Qwen3-4B \`list_files(path="/")\` phone failure is covered at compatibility, central path, direct tool and executor layers.
- All model-invented absolute-looking paths are virtualized unless the application explicitly trusts them through the file map or they are documented Android public roots.
- A real existing system path is covered as a negative trust case; real external attachment read/copy are covered as positive trust cases.
- Automatic path-field inventory covers all 37 local schemas; scalar, array, nested Office, destination and output-directory paths are gated.
- Model-facing tool results remain logicalized and manual Skill enforcement remains authoritative.
- Structured 4B ABI repair/defaults cover the thinner file/archive/PDF/Office/image utility surfaces.
- Complete local surface remains 25 manually controlled Skills / 37 canonical functions.
- All inherited V9-V16 cloud/runtime/document/media/sandbox safeguards remain green.
- Flutter static analysis and exact Chaquopy ARM64 dependency resolution passed before the single formal APK build.
- Verified APK SHA-256: \`$OUT_SHA\`.
- Verified APK size: \`$OUT_SIZE\` bytes.
EOF

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -u
git add python/navixmind/tools/compat.py python/navixmind/tools/path_contract.py \
  docs/HANDOFF_QWEN3_LOCAL_TOOL_CONTRACT_RECOVERY_V17.md docs/V17_LIVE_PROGRESS_AND_HANDOFF.md
if ! git diff --cached --quiet; then
  git commit -m 'feat: persist verified local-first tool contract recovery v17 [skip ci]'
  git push origin HEAD:iteration/qwen3-local-tool-contract-recovery-v17
fi

cat > release-notes.md <<EOF
RastaCoder Qwen3 4B Local Tool Contract Recovery v17

Version: $BUILD_NAME ($BUILD_NUMBER)
Package: $EXPECTED_PACKAGE
ABI: arm64-v8a only
APK SHA-256: $OUT_SHA
APK size: $OUT_SIZE bytes
Signing certificate SHA-256: $CERT_SHA
MLC runtime SHA-256: $EXPECTED_RUNTIME_SHA256
curl-cffi private native companion: $PRIVATE_CURL_LIB
curl-cffi private companion SHA-256: $PRIVATE_SHA

V17 is the local-first final recovery release. The copied V16 device diagnostic showed Qwen3-4B calling list_files with path "/" for its workspace and Android returning EACCES. A latent V12 path-contract omission allowed that virtual root notation to reach the operating-system root.

V17 repairs the exact call at two layers and then generalizes the contract across the complete on-device surface. Model-invented absolute-looking paths are workspace-relative by default; only documented Android public roots and exact application-trusted attachment paths can cross that boundary. The CI suite includes an existing-system-path negative test, real attachment read/copy positive tests, automatic inventory of all path-bearing fields across the 37 local schemas, scalar/array/nested/destination/output-directory coverage, structured small-model ABI recovery, logical result reinjection and manual Skill enforcement.

Exactly 25 manually controlled Skills / 37 canonical functions remain exposed. Every V9-V17 regression, Flutter analysis, curl-cffi Android native gate and exact ARM64 Chaquopy dependency gate passed before the one formal APK build. The fixed known-good MLC runtime and stable signing identity remain unchanged.

Full no-APK preflight: https://github.com/${GITHUB_REPOSITORY}/actions/runs/$PREFLIGHT_RUN
MLC/native binary probe: https://github.com/${GITHUB_REPOSITORY}/actions/runs/$RUNTIME_PROBE_RUN
EOF

gh release create "$RELEASE_TAG" "$OUTPUT_APK" \
  --target iteration/qwen3-local-tool-contract-recovery-v17 \
  --title 'RastaCoder Qwen3 4B Local Tool Contract Recovery v17' \
  --notes-file release-notes.md

echo "V17 release published: $RELEASE_TAG"
echo "APK SHA-256: $OUT_SHA"
echo "APK size: $OUT_SIZE"

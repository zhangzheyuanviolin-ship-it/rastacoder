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
- Local-model tool calling is the primary product capability. Cloud-provider tool calling remains secondary and must not regress the on-device path.
- The real-device V16 failure was Qwen3-4B emitting \`list_files(path="/")\` for the logical workspace root. The call reached Android \`/\` and failed with EACCES.
- The latent code defect entered with the V12 central path contract: the workspace alias set covered \`.\`, \`workspace\`, \`output\`, \`/workspace\` and \`/output\`, while bare \`/\` was omitted; the generic absolute-path branch then preserved it as an operating-system path.
- V13 through V16 inherited that path-contract behavior. V14 is the last release for which local Qwen3-4B tool calls were explicitly user-confirmed working on device, so V17 treats V14 as the last real-device local-tool-good checkpoint while retaining all later fixes.

## V17 shared path-contract recovery
- Bare \`/\` is a first-class logical workspace-root alias at the central executor path boundary.
- The local 3B-4B compatibility ABI independently normalizes \`list_files(path="/")\` to \`path="."\` and records that repair in diagnostics.
- The fix is generalized beyond the exact crash: model-invented absolute-looking children such as \`/foo.txt\` and \`/folder/result.pdf\` are virtual workspace paths unless they are already-resolved trusted files or documented Android public-root aliases.
- Arbitrary Android/Linux directories are no longer promoted merely because a small model wrote an absolute path.
- Already-resolved attachment files, workspace paths and documented Android logical roots remain usable.
- The common scalar resolver covers image/input/pdf/file/path/source/destination/zip/docx/pptx/xlsx path fields.
- Array path inputs \`image_paths\`, \`file_paths\` and \`input_paths\` stay under the same central path contract.
- Nested Office operation attachment paths remain resolved through the shared attachment/workspace boundary.
- \`file_manage.destination_path\` is now included in the shared path boundary.
- \`extract_zip.output_dir\` is now included in the shared output boundary alongside \`output_path\`.
- Root-only output values are never treated as filenames; safe deterministic workspace filenames are synthesized where the operation permits it.

## V17 25-Skill / 37-function local ABI audit
- Exactly 25 manually controlled Skills remain present.
- The union of enabled local Skills exposes exactly the same 37 canonical functions as the canonical tool registry.
- The projected 4B tool schemas still contain all 37 functions, and every canonical function retains a compact local prompt hint.
- Structured local-tool compatibility was strengthened for \`file_manage\`, \`list_zip\`, \`extract_zip\`, \`pdf_manage\`, \`create_pptx\`, \`create_xlsx\`, \`image_compose\`, \`convert_document\`, \`anysearch_extract\` and \`anysearch_get_sub_domains\` using deterministic aliases/defaults only.
- Creation/conversion tools which can safely choose an output name now receive deterministic workspace-relative defaults, reducing small-model failures caused by meaningless Android absolute paths.
- Exact replay of the copied phone failure is covered at compatibility, shared resolver, direct tool and executor levels.
- Leading-slash variants are regression-tested across every shared scalar path field plus output file/directory boundaries.
- File, Office, ZIP, PDF, image and media path families are covered centrally rather than with a list_files-only patch.
- Network/search, Google-service, Python sandbox, media runtime, Office serialization and cloud compatibility safeguards remain covered by inherited V9-V16 gates.
- All V9-V16 regressions remain green together with the new V17 gate before and after the formal build.

## Runtime/build invariants retained
- Exact known-good MLC runtime remains unchanged.
- Exactly the five previously verified MLC model libraries remain exposed; no unverified model library is introduced by V17.
- Chaquopy Python 3.13, cffi 1.17.1 and the pinned curl-cffi 0.16.2 Android ARM64 payload remain under the V15/V16 compatibility and native-companion gates.
- Stable signing identity and package ID are unchanged.
- Formal output remains ARM64-only and is produced by exactly one APK build command after the locked no-APK preflight succeeds.

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
- V12 introduced the latent missing bare-slash workspace alias; V13-V16 inherited it. V14 is the last user-confirmed real-device local-tool-good checkpoint.
- Exact copied Qwen3-4B \`list_files(path="/")\` failure is covered at the compatibility ABI, shared path contract, direct tool and executor levels.
- The same family is generalized: arbitrary model leading-slash children are workspace-relative, while trusted files and documented Android public roots remain usable.
- Shared path coverage includes scalar, array and nested Office paths, plus \`file_manage.destination_path\` and \`extract_zip.output_dir\`.
- Structured file/archive/PDF/Office/image compatibility and deterministic output defaults are covered for 4B local models.
- Complete local surface invariant remains 25 manually controlled Skills / 37 canonical functions.
- All inherited V9-V16 cloud/runtime/document/media/sandbox safeguards remain under regression gates.
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

V17 is the local-first final recovery release. The exact real-device V16 failure was Qwen3-4B calling list_files with path "/" for its workspace. A latent V12 contract hole omitted bare slash from the logical workspace aliases, allowing the operating-system root to reach the tool implementation. V17 fixes that centrally and generalizes the rule to arbitrary model-invented leading-slash workspace children.

The audit was expanded across the entire on-device surface: 25 manually controlled Skills / 37 canonical functions, scalar/array/nested path families, destination and output-directory boundaries, structured file/archive/PDF/Office/image compatibility, deterministic output naming, tool-result/runtime regressions, Flutter analysis and exact Android ARM64 dependency resolution. All inherited V9-V16 safeguards remain green. The fixed MLC runtime and stable signing identity remain unchanged.

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

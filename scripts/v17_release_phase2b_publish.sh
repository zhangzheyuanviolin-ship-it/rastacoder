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

## Priority and root cause
- Local-model tool calling remains the product's primary capability; cloud providers remain secondary.
- The exact V16 phone failure was Qwen3-4B emitting \`list_files(path="/")\`; both the V12 list-files compatibility alias set and the V12 central workspace alias set omitted bare \`/\`, allowing Android filesystem root access and EACCES.
- V14, V15 and V16 inherited the same path-contract blob; V14 was the last user-confirmed local-tool-good release, so the defect was latent until the model selected the missing alias.

## V17 verified fixes
- Bare \`/\` is now a first-class model-facing workspace-root alias in the shared path contract.
- The small-model list_files compatibility ABI independently normalizes \`/\` to \`.\` and records the repair, so diagnostics no longer pass a raw Android root through the tool boundary.
- Exact replay of the copied V16 phone call \`list_files(path="/", recursive=false, include_directories=true)\` lists the temporary workspace successfully.
- file_manage list with \`path="/"\` is covered through the same central contract.
- All ten shared scalar path keys (image/input/pdf/file/path/source/zip/docx/pptx/xlsx) are regression-tested so bare slash resolves to workspace root at the common executor layer.
- Trusted already-resolved attachment/output absolute paths and documented Android logical roots remain usable.
- Exactly 25 manually controlled Skills / 37 canonical local functions remain exposed when all local Skills are enabled.
- All V9-V16 regression gates remain green.

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
# RastaCoder V17 local-tool recovery live progress and handoff

- Complete V9-V17 no-APK preflight \`$PREFLIGHT_RUN\`: SUCCESS.
- Exact MLC/native binary probe \`$RUNTIME_PROBE_RUN\`: SUCCESS.
- Exact copied Qwen3-4B list_files(path="/") phone regression is covered at the compatibility ABI, path contract, direct tool and executor levels.
- 25 Skills / 37 canonical local functions preserved.
- V14 is the last user-confirmed local-tool-good release; V12 introduced the latent missing-slash alias and V14/V15/V16 retained the same path-contract blob.
- V15/V16 cloud/runtime hardening remains covered by inherited gates.
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
  git commit -m 'feat: persist verified local tool contract recovery v17 [skip ci]'
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

V17 is a priority local-model recovery release. The exact V16 real-device failure was Qwen3-4B calling list_files with path "/" when asked to inspect its workspace. A latent V12 contract hole omitted bare slash from both workspace-alias layers, so Android root was reached and returned EACCES. V17 repairs the alias at both the local small-model ABI boundary and the shared path contract, replays that exact call in CI, covers file_manage and every shared scalar path key, and preserves the complete 25-Skill / 37-function local tool surface.

All V9-V16 safeguards, including the V15/V16 cloud/runtime fixes, remain under regression gates. The fixed known-good MLC runtime and stable signing identity are unchanged.

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

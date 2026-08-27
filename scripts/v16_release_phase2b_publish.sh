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

test -s /tmp/v16-release.env
# shellcheck disable=SC1091
source /tmp/v16-release.env
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

test "$(sha256sum "$OUTPUT_APK" | awk '{print $1}')" = "$OUT_SHA"
test "$(stat -c '%s' "$OUTPUT_APK")" = "$OUT_SIZE"

rm -f android/app/rastacoder-dev.p12 android/key.properties android/local.properties upstream-known-good.apk
rm -rf android/app/vendor
rm -f "android/app/src/main/jniLibs/arm64-v8a/$PRIVATE_CURL_LIB"

cat > docs/HANDOFF_QWEN3_RESIDUAL_RUNTIME_HARDENING_V16.md <<EOF
# RastaCoder Qwen3 Residual Runtime Hardening v16 — verified release handoff

Branch: \`iteration/qwen3-residual-runtime-hardening-v16\`
Release tag: \`$RELEASE_TAG\`
Version: \`$BUILD_NAME\` / code \`$BUILD_NUMBER\`
Package: \`$EXPECTED_PACKAGE\`
Full no-APK preflight: \`$PREFLIGHT_RUN\`
MLC/native binary probe: \`$RUNTIME_PROBE_RUN\`

## V16 verified fixes
- Preserves exactly 25 manually controlled Skills / 37 canonical local functions and all V9-V15 safeguards.
- Safe Python os.path facade provides exists/isfile/isdir/getsize/getmtime inside OUTPUT_DIR while arbitrary filesystem probing remains blocked.
- create_xlsx normalizes canonical 2-D rows, compatibility sheet_name/data/item payloads, and object-record rows to one matrix representation; it reopens saved workbooks and verifies cell values before reporting success.
- download_media packages every wheel-private hashed native dependency required by the pinned official curl-cffi Android ARM64 wheel; native import/dlopen failures also return an explicit browser-impersonation-runtime diagnostic.
- Packaged curl-cffi private companion \`$PRIVATE_CURL_LIB\` is byte-identical to the pinned wheel payload; SHA-256 \`$PRIVATE_SHA\`.

## MLC model compatibility audit
- Current fixed runtime was binary-probed and contains exactly the five model_lib IDs already represented by the download list.
- No unverified MLC model was added in V16. Future expansion requires compiling its model library into the Android MLC runtime and passing real-device load/inference/tool-use acceptance tests before it enters the list.

## Final verified artifact
- ABI: \`arm64-v8a\` only
- Stable signing certificate SHA-256: \`$EXPECTED_CERT_SHA256\`
- MLC runtime SHA-256: \`$EXPECTED_RUNTIME_SHA256\`
- APK SHA-256: \`$OUT_SHA\`
- APK size: \`$OUT_SIZE\` bytes
EOF

cat > docs/V16_LIVE_PROGRESS_AND_HANDOFF.md <<EOF
# RastaCoder V16 live progress and handoff

- Complete V9-V16 no-APK preflight \`$PREFLIGHT_RUN\`: SUCCESS.
- Exact MLC/native binary probe \`$RUNTIME_PROBE_RUN\`: SUCCESS.
- 25 Skills / 37 canonical local functions preserved.
- Safe os.path, XLSX create/read roundtrip, and curl-cffi Android native companion fixes are covered by V16 regression gates.
- Flutter static analysis and exact Chaquopy ARM64 dependency resolution passed before the single formal APK build.
- Current MLC runtime is proven to support exactly the five existing download-list model_lib IDs; V16 intentionally adds no speculative model entries.
- Verified APK SHA-256: \`$OUT_SHA\`.
- Verified APK size: \`$OUT_SIZE\` bytes.
EOF

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -u
git add docs/HANDOFF_QWEN3_RESIDUAL_RUNTIME_HARDENING_V16.md docs/V16_LIVE_PROGRESS_AND_HANDOFF.md
if ! git diff --cached --quiet; then
  git commit -m 'feat: persist verified residual runtime hardening v16 source and handoff [skip ci]'
  git push origin HEAD:iteration/qwen3-residual-runtime-hardening-v16
fi

cat > release-notes.md <<EOF
RastaCoder Qwen3 4B Residual Runtime Hardening v16

Version: $BUILD_NAME ($BUILD_NUMBER)
Package: $EXPECTED_PACKAGE
ABI: arm64-v8a only
APK SHA-256: $OUT_SHA
APK size: $OUT_SIZE bytes
Signing certificate SHA-256: $CERT_SHA
MLC runtime SHA-256: $EXPECTED_RUNTIME_SHA256
curl-cffi private native companion: $PRIVATE_CURL_LIB
curl-cffi private companion SHA-256: $PRIVATE_SHA

V16 closes the three residual issues from the cloud-model regression: safe os.path exists/isfile/isdir/getsize/getmtime support inside OUTPUT_DIR, robust create_xlsx/read_xlsx roundtrips across canonical and compatibility payload structures, and Android packaging of curl-cffi's wheel-private native dependency so download_media can enter its browser-impersonation path on-device. It preserves the previous 25 Skills / 37 canonical functions and all V9-V15 safeguards.

The current fixed MLC runtime was binary-audited and contains exactly the five model_lib IDs already exposed by the existing local-model download list. V16 therefore adds no speculative model entries; additional models require a separately compiled MLC runtime plus real-device acceptance tests.

Full no-APK preflight: https://github.com/${GITHUB_REPOSITORY}/actions/runs/$PREFLIGHT_RUN
MLC/native binary probe: https://github.com/${GITHUB_REPOSITORY}/actions/runs/$RUNTIME_PROBE_RUN
EOF

gh release create "$RELEASE_TAG" "$OUTPUT_APK" \
  --target iteration/qwen3-residual-runtime-hardening-v16 \
  --title 'RastaCoder Qwen3 4B Residual Runtime Hardening v16' \
  --notes-file release-notes.md

echo "V16 release published: $RELEASE_TAG"
echo "APK SHA-256: $OUT_SHA"
echo "APK size: $OUT_SIZE"

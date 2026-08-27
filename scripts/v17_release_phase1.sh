#!/usr/bin/env bash
set -euo pipefail

: "${PREFLIGHT_RUN:?}"
: "${RUNTIME_PROBE_RUN:?}"
: "${GH_TOKEN:?}"

preflight="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${PREFLIGHT_RUN}" --jq '.conclusion')"
probe="$(gh api "repos/${GITHUB_REPOSITORY}/actions/runs/${RUNTIME_PROBE_RUN}" --jq '.conclusion')"
test "$preflight" = "success"
test "$probe" = "success"
echo "Locked V17 full no-APK preflight: $PREFLIGHT_RUN = $preflight"
echo "Locked MLC/native binary probe: $RUNTIME_PROBE_RUN = $probe"

grep -F 'version "3.13"' android/app/build.gradle
grep -F 'install "cffi==1.17.1"' android/app/build.gradle
grep -F 'vendor/curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl' android/app/build.gradle
grep -F 'com.chaquo.python:gradle:16.1.0' android/build.gradle

python3 -m py_compile \
  scripts/apply_iteration_v17_local_tool_recovery.py \
  scripts/apply_iteration_v17_prompt_legacy_guard.py \
  scripts/validate_iteration_v17.py \
  scripts/prepare_curl_cffi_android_wheel.py \
  scripts/prepare_curl_cffi_native_companion_v16.py
python3 scripts/apply_iteration_v17_local_tool_recovery.py
python3 scripts/apply_iteration_v17_prompt_legacy_guard.py
python3 -m py_compile \
  python/navixmind/agent.py \
  python/navixmind/tools/__init__.py \
  python/navixmind/tools/compat.py \
  python/navixmind/tools/path_contract.py \
  python/navixmind/tools/documents.py \
  python/navixmind/tools/extended_tools.py \
  python/navixmind/tools/code_executor.py \
  python/navixmind/tools/media.py

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
python3 scripts/validate_iteration_v16.py
python3 scripts/validate_iteration_v17.py

flutter pub get
python3 - <<'PY'
import os
from pathlib import Path
pub = Path(os.environ['PUB_CACHE']) / 'hosted' / 'pub.dev'
candidates = sorted(pub.glob('flutter_inappwebview_android-*/android/build.gradle'))
if not candidates:
    raise SystemExit('flutter_inappwebview_android build.gradle not found')
p = candidates[-1]
text = p.read_text()
for old, new in {
    'compileSdkVersion 33': 'compileSdkVersion 35',
    'compileSdkVersion 34': 'compileSdkVersion 35',
    'compileSdk 33': 'compileSdk 35',
    'compileSdk 34': 'compileSdk 35',
}.items():
    text = text.replace(old, new)
p.write_text(text)
PY
flutter analyze --no-fatal-infos --no-fatal-warnings

echo 'V17 release phase 1 passed: exact phone regression, arbitrary leading-slash family, full 25/37 local-tool invariant, V9-V17 host regressions and Flutter analysis are green.'

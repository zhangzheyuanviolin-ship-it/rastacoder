#!/usr/bin/env bash
set -euo pipefail

: "${SOURCE_APK_URL:?}"
: "${SOURCE_APK_SHA256:?}"
: "${EXPECTED_RUNTIME_SHA256:?}"
: "${EXPECTED_CERT_SHA256:?}"
: "${EXPECTED_PACKAGE:?}"
: "${BUILD_NAME:?}"
: "${BUILD_NUMBER:?}"
: "${OUTPUT_APK:?}"
: "${PRIVATE_CURL_LIB:?}"

python3 scripts/prepare_curl_cffi_android_wheel.py
python3 scripts/validate_iteration_v15_curl_cffi_compat.py
python3 scripts/prepare_curl_cffi_native_companion_v16.py | tee /tmp/v16-native-prep.log
grep -F "required companion: $PRIVATE_CURL_LIB" /tmp/v16-native-prep.log
test -s "android/app/src/main/jniLibs/arm64-v8a/$PRIVATE_CURL_LIB"

python3 - <<'PY'
import hashlib, os
from pathlib import Path
p = Path('android/app/src/main/jniLibs/arm64-v8a') / os.environ['PRIVATE_CURL_LIB']
data = p.read_bytes()
assert data.startswith(b'\x7fELF')
print('curl-cffi private companion SHA-256:', hashlib.sha256(data).hexdigest())
print('curl-cffi private companion size:', len(data))
PY

FLUTTER_BIN="$(command -v flutter)"
FLUTTER_SDK="$(cd "$(dirname "$FLUTTER_BIN")/.." && pwd)"
SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/usr/local/lib/android/sdk}}"
cat > android/local.properties <<EOF
sdk.dir=$SDK_ROOT
flutter.sdk=$FLUTTER_SDK
flutter.versionName=$BUILD_NAME
flutter.versionCode=$BUILD_NUMBER
EOF

gradle -p android :app:generateDebugPythonRequirements --no-daemon 2>&1 | tee /tmp/v16-release-python-resolution.log
verify_dep() {
  local pattern="$1"
  if grep -Eiq "$pattern" /tmp/v16-release-python-resolution.log; then return 0; fi
  if find android/app/build -print 2>/dev/null | grep -Eiq "$pattern"; then return 0; fi
  echo "Required Android Python dependency was not resolved: $pattern" >&2
  exit 1
}
verify_dep 'curl[_-]cffi.*0\.16\.2|curl[_-]cffi-0\.16\.2'
verify_dep 'cffi.*1\.17\.1|cffi-1\.17\.1'
verify_dep 'matplotlib.*3\.8\.4|matplotlib-3\.8\.4'
verify_dep 'pandas.*2\.1\.3|pandas-2\.1\.3'
verify_dep 'numpy.*1\.26\.2|numpy-1\.26\.2'
test -s "android/app/src/main/jniLibs/arm64-v8a/$PRIVATE_CURL_LIB"

curl -L --fail --retry 5 --retry-delay 3 -o upstream-known-good.apk "$SOURCE_APK_URL"
echo "$SOURCE_APK_SHA256  upstream-known-good.apk" | sha256sum -c -
test "$(stat -c '%s' upstream-known-good.apk)" -eq 593655513
python3 - <<'PY'
import hashlib, os, pathlib, zipfile
src = pathlib.Path('upstream-known-good.apk')
dst = pathlib.Path('android/mlc4j/output/arm64-v8a/libtvm4j_runtime_packed.so')
dst.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(src) as z:
    data = z.read('lib/arm64-v8a/libtvm4j_runtime_packed.so')
assert len(data) == 38786520, len(data)
digest = hashlib.sha256(data).hexdigest()
assert digest == os.environ['EXPECTED_RUNTIME_SHA256'], digest
dst.write_bytes(data)
print('Restored verified MLC runtime:', digest)
PY

git fetch origin main
git show origin/main:.github/signing/rastacoder-dev-keystore.p12.b64 | base64 -d > android/app/rastacoder-dev.p12
test "$(sha256sum android/app/rastacoder-dev.p12 | awk '{print $1}')" = "7048dea7d7152b80255716de2338eea539acd898cc3b8ecf8a9ca2203f21b169"
cat > android/key.properties <<'EOF'
storeFile=rastacoder-dev.p12
storePassword=RastaCoderDev2026!
keyAlias=rastacoder-dev
keyPassword=RastaCoderDev2026!
EOF

cp android/app/build.gradle /tmp/v16-build.gradle-before-signing
python3 - <<'PY'
from pathlib import Path
p = Path('android/app/build.gradle')
text = p.read_text()
text = text.replace('abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"', 'abiFilters "arm64-v8a"')
start = text.find('        debug {')
end = text.find('        release {', start)
if start < 0 or end < 0:
    raise SystemExit('debug/release buildTypes not found')
block = text[start:end]
signing = "            signingConfig keystoreProperties.containsKey('storeFile') ? signingConfigs.release : signingConfigs.debug\n"
lines = [line for line in block.splitlines(True) if 'signingConfig keystoreProperties.containsKey' not in line]
rebuilt = ''.join(lines)
anchor = '            buildConfigField "boolean", "NAVIXMIND_DEBUG", "true"\n'
if anchor not in rebuilt:
    raise SystemExit('debug signing anchor not found')
rebuilt = rebuilt.replace(anchor, anchor + signing, 1)
text = text[:start] + rebuilt + text[end:]
p.write_text(text)
PY

# Exactly one formal APK build in V16.
flutter build apk --debug --build-name="$BUILD_NAME" --build-number="$BUILD_NUMBER"
cp build/app/outputs/flutter-apk/app-debug.apk "$OUTPUT_APK"
test -s "$OUTPUT_APK"

APKSIGNER="$(find "$SDK_ROOT/build-tools" -name apksigner -type f | sort -V | tail -n 1)"
if [ -z "$APKSIGNER" ]; then
  sdkmanager 'build-tools;35.0.0' >/dev/null
  APKSIGNER="$SDK_ROOT/build-tools/35.0.0/apksigner"
fi
AAPT="$(dirname "$APKSIGNER")/aapt"
BADGING="$($AAPT dump badging "$OUTPUT_APK" | head -n 1)"
echo "$BADGING"
echo "$BADGING" | grep -F "package: name='$EXPECTED_PACKAGE'"
echo "$BADGING" | grep -F "versionCode='$BUILD_NUMBER'"
echo "$BADGING" | grep -F "versionName='$BUILD_NAME'"
"$APKSIGNER" verify --verbose --print-certs "$OUTPUT_APK" | tee apksigner.txt
CERT_SHA="$(awk -F': ' '/certificate SHA-256 digest/{print tolower($NF); exit}' apksigner.txt | tr -d ':')"
test "$CERT_SHA" = "$EXPECTED_CERT_SHA256"

python3 - <<'PY'
import hashlib, os, zipfile
from pathlib import Path
apk = os.environ['OUTPUT_APK']
with zipfile.ZipFile(apk) as z:
    names = z.namelist()
    abis = sorted({n.split('/')[1] for n in names if n.startswith('lib/') and len(n.split('/')) >= 3})
    assert abis == ['arm64-v8a'], abis
    runtime = z.read('lib/arm64-v8a/libtvm4j_runtime_packed.so')
    assert len(runtime) == 38786520, len(runtime)
    runtime_sha = hashlib.sha256(runtime).hexdigest()
    assert runtime_sha == os.environ['EXPECTED_RUNTIME_SHA256'], runtime_sha
    private_name = 'lib/arm64-v8a/' + os.environ['PRIVATE_CURL_LIB']
    assert private_name in names, private_name
    packed_private = z.read(private_name)
    source_private = (Path('android/app/src/main/jniLibs/arm64-v8a') / os.environ['PRIVATE_CURL_LIB']).read_bytes()
    assert packed_private == source_private, 'curl-cffi native companion bytes changed during packaging'
    assert packed_private.startswith(b'\x7fELF')
    print('Verified APK curl-cffi companion SHA-256:', hashlib.sha256(packed_private).hexdigest())
PY

OUT_SHA="$(sha256sum "$OUTPUT_APK" | awk '{print $1}')"
OUT_SIZE="$(stat -c '%s' "$OUTPUT_APK")"
PRIVATE_SHA="$(sha256sum "android/app/src/main/jniLibs/arm64-v8a/$PRIVATE_CURL_LIB" | awk '{print $1}')"
cat > /tmp/v16-release.env <<EOF
OUT_SHA=$OUT_SHA
OUT_SIZE=$OUT_SIZE
CERT_SHA=$CERT_SHA
PRIVATE_SHA=$PRIVATE_SHA
EOF

# Restore the source build.gradle so only reviewed V16 source changes are persisted later.
cp /tmp/v16-build.gradle-before-signing android/app/build.gradle

echo "Final V16 APK SHA-256: $OUT_SHA"
echo "Final V16 APK size: $OUT_SIZE"
echo 'V16 release phase 2A passed: one APK built and package/signature/ABI/MLC/curl-cffi native payload verified.'

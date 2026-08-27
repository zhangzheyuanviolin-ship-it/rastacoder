#!/usr/bin/env python3
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
gradle = (ROOT / 'android/app/build.gradle').read_text(encoding='utf-8')
preparer = (ROOT / 'scripts/prepare_curl_cffi_android_wheel.py').read_text(encoding='utf-8')
wheel = ROOT / 'android/app/vendor/curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl'

assert 'install "cffi==1.17.1"' in gradle, 'Chaquopy cffi 1.17.1 pin missing'
assert 'install "vendor/curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl"' in gradle, 'Local verified curl-cffi wheel install missing'
assert 'V15 ABI probe run 33034762510' in gradle, 'Compatibility probe provenance marker missing'
assert '58598186eccd24d2b2e126f945d8a5bdca0066a2789052023d3d8370ebadca30' in preparer, 'Official Android wheel SHA pin missing'
assert 'Requires-Dist: cffi>=1.17.1' in preparer, 'Metadata compatibility requirement missing'
assert wheel.is_file(), f'Prepared wheel missing: {wheel}'

with zipfile.ZipFile(wheel) as zf:
    metadata_names = [name for name in zf.namelist() if name.endswith('.dist-info/METADATA')]
    assert len(metadata_names) == 1, metadata_names
    metadata = zf.read(metadata_names[0]).decode('utf-8')
    compact = metadata.lower().replace(' ', '')
    assert 'requires-dist:cffi>=1.17.1' in compact, metadata
    assert 'requires-dist:cffi>=2' not in compact, metadata
    assert any(name.startswith('curl_cffi/') and name.endswith('.so') for name in zf.namelist()), 'curl-cffi native wrapper missing'

print('V15 curl-cffi compatibility validation passed: official Android binary retained, metadata targets proven CFFI 1.17.1 ABI.')

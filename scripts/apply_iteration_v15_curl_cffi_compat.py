#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('.')
PATH = ROOT / 'android/app/build.gradle'
text = PATH.read_text(encoding='utf-8')
old = '                install "curl-cffi==0.16.2"'
new = '''                // curl-cffi==0.16.2 official Android ARM64 binary; V15 ABI probe run 33034762510\n                // proved its wrapper + HTTPS Chrome impersonation with cffi/_cffi_backend 1.17.1.\n                // prepare_curl_cffi_android_wheel.py changes only the wheel dependency metadata.\n                install "cffi==1.17.1"\n                install "vendor/curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl"'''
if new not in text:
    if old not in text:
        raise RuntimeError('V15 curl-cffi compatibility anchor not found in android/app/build.gradle')
    text = text.replace(old, new, 1)
    PATH.write_text(text, encoding='utf-8')
print('V15 curl-cffi/Chaquopy compatibility patch applied.')

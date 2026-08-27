#!/usr/bin/env python3
"""Package curl-cffi's exact wheel-private DT_NEEDED companions into jniLibs.

The official Android wheel is SHA-pinned and prepared by the V15 wheel preparer.
Chaquopy installs the Python extension, but Android's dynamic loader cannot
reliably discover wheel-private hashed shared libraries from that location.
V16 copies every byte-identical wheel-private hashed DT_NEEDED member into the
APK native-library search path under the exact filename requested by _wrapper.so.
System libraries such as libc.so and libm.so are intentionally left alone.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHEEL = ROOT / 'android/app/vendor/curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl'
JNI_DIR = ROOT / 'android/app/src/main/jniLibs/arm64-v8a'
PRIVATE_NEEDED_RE = rb'lib[A-Za-z0-9+_.-]+-[0-9a-fA-F]+\.so'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if not WHEEL.is_file():
        raise SystemExit(f'Prepared curl-cffi wheel not found: {WHEEL}')

    packaged = []
    with zipfile.ZipFile(WHEEL, 'r') as zf:
        wrapper_names = [n for n in zf.namelist() if n.endswith('.so') and '/_wrapper' in n]
        if len(wrapper_names) != 1:
            raise SystemExit(f'Expected one curl-cffi _wrapper.so, found {wrapper_names}')
        wrapper = zf.read(wrapper_names[0])

        # ELF dynamic strings contain exact DT_NEEDED names. Restrict extraction
        # to wheel-private hashed names so Android system libraries are untouched.
        needed = sorted(set(m.decode('ascii') for m in re.findall(PRIVATE_NEEDED_RE, wrapper)))
        if not needed:
            raise SystemExit('No wheel-private hashed DT_NEEDED libraries found in curl-cffi wrapper')

        JNI_DIR.mkdir(parents=True, exist_ok=True)
        for needed_name in needed:
            matches = [n for n in zf.namelist() if Path(n).name == needed_name]
            if len(matches) != 1:
                raise SystemExit(
                    f'Official wheel does not contain required native companion {needed_name}: {matches}'
                )
            payload = zf.read(matches[0])
            if len(payload) < 1024 or not payload.startswith(b'\x7fELF'):
                raise SystemExit(
                    f'Invalid native companion payload: {matches[0]} ({len(payload)} bytes)'
                )
            out = JNI_DIR / needed_name
            out.write_bytes(payload)
            packaged.append((needed_name, matches[0], out, len(payload), sha256(payload)))

    print(f'curl-cffi wrapper member: {wrapper_names[0]}')
    print(f'wheel-private DT_NEEDED companions: {len(packaged)}')
    for needed_name, member, out, size, digest in packaged:
        print(f'required companion: {needed_name}')
        print(f'official wheel member: {member}')
        print(f'packaged jniLib: {out.relative_to(ROOT)}')
        print(f'companion size: {size}')
        print(f'companion SHA-256: {digest}')


if __name__ == '__main__':
    main()

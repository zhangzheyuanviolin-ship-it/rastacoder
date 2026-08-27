# RastaCoder Qwen3 Tool Runtime Hardening v15 — verified release handoff

Branch: `iteration/qwen3-tool-runtime-hardening-v15`
Release tag: `qwen3-tool-runtime-hardening-v15`
Version: `0.0.14` / code `28`
Package: `ai.navixmind`
Full no-APK preflight: `33034877280`
curl-cffi/CFFI compatibility probe: `33034762510`

## V15 verified fixes
- Preserves exactly 25 manually controlled Skills / 37 canonical local functions and all V9-V14 safeguards.
- PPTX speaker notes package resources are extracted for python-pptx notesMaster creation.
- ZIP extraction accepts archive-declared zero-byte files while retaining strict postconditions for unexpected empty outputs.
- FFmpeg audio filtering chooses codecs from the output target; numeric mix duration is treated as an output time limit; convert and extract-frame paths remain covered.
- Image conversion normalizes jpg/jpeg/png/webp/bmp/gif/tif/tiff aliases before Pillow save.
- Python OUTPUT_DIR files can be read back in the same execution; safe os.path and safe package-version diagnostics are enabled while dangerous os and dunder access remain blocked.
- OCR reports explicit no-text state.
- XLSX values mode falls back to formulas when cached formula values are absent instead of returning an all-null matrix.
- download_media has clear non-media URL handling and browser TLS impersonation support.
- Unlimited tool-call mode uses zero as an explicit sentinel and removes both the call counter and tool-driven ReAct iteration ceiling; 15/25/50/100 limits remain available.

## Android browser impersonation runtime
- Official curl-cffi 0.16.2 CPython 3.13 Android ARM64 wheel source SHA-256 is pinned to `58598186eccd24d2b2e126f945d8a5bdca0066a2789052023d3d8370ebadca30`.
- Probe run `33034762510` proved curl-cffi import, HTTPS and Chrome impersonation with cffi/_cffi_backend 1.17.1.
- The Android packaging shim changes only the wheel dependency metadata to the proven cffi 1.17.1 backend; all official executable/package payload members remain byte-identical.

## Final verified artifact
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `529c49e7041257ff3a907fbb95ac90feaa7a8db0e116c0975b96d9b975e2f1d7`
- APK size: `525218486` bytes

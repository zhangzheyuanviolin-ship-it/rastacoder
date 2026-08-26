# RastaCoder Qwen3 Complete Skills v7 — verified release handoff

Current branch: `iteration/qwen3-complete-skills-v7`
Release tag: `qwen3-complete-skills-accessibility-v7`
Version: `0.0.6` / code `20`

## User-verified v6 starting point
V6 real-device testing confirmed the repaired local Qwen3-4B tool chain successfully executed document-format conversion, autonomous TXT/Word creation, and audio-format conversion. V7 preserves that reliability architecture and expands the capability surface.

## V7 systemic changes
- 21 Skills remain manually selected to control local-model context size.
- The obsolete “23 original tools = complete” invariant is removed. V7 covers 31 canonical local functions: the legacy 23, upstream post-baseline `image_compose` and `list_files`, plus six new structured functions for complete file/archive/PDF/Office coverage.
- File/text operations now include list/discover, mkdir, copy, move, rename, delete, touch and existence checks.
- ZIP supports directory-aware creation, archive listing and safe extraction.
- Image processing supports resize/upscale/downscale, format conversion, concat, overlay, crop, adjust, grayscale, blur, rotate, flip and smart face crop.
- FFmpeg keeps the advanced custom escape hatch and adds structured multi-input concat, audio mixing and video/audio merge.
- PDF adds merge/split/extract/reorder/delete/rotate page management.
- PowerPoint and Excel can now be created; Office modification actions are expanded.
- Media download now saves the resolved media file instead of returning only a URL.
- Google Calendar adds update; Gmail remains read-only because the app deliberately requests only gmail.readonly.
- Attached paths are resolved for ZIP/file operations and nested Office image operations.
- Chat-history and new-conversation buttons have explicit accessibility semantics.
- Thinking and tool-diagnostics panels are independently focusable stateful expand/collapse controls with dynamic screen-reader labels.
- Fresh installs default to local Qwen3-4B; the last explicitly selected model is persisted and the preferred downloaded local model is restored into the MLC runtime on cold start. Cloud models remain explicit options.

## Verification
- Final v7 preflight passed Python compilation, functional smoke tests and Flutter Analyze before any APK build.
- Release build used the exact released v6 functional source as baseline, then the complete v7 patch chain.
- Final package: `ai.navixmind`
- Final ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `0a9838fa90e5dff0c45778e472ebca7c11de9a6b77e747488db72299b3a9757c`
- APK size: `499371304` bytes

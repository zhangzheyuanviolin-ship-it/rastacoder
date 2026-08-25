# Qwen3 4B known-good baseline

This repository now preserves an exact source baseline for the Android build that is known to execute Qwen3 4B offline tool calls correctly.

- Source project: `alexandertaboriskiy/navixmind`
- Release: `v0.5.0-beta`
- Source commit: `e165c311eb464722c5db0883426e82af69468330`
- Preserved branch in this repository: `baseline/qwen3-official-v0.5.0`
- Official APK: `app-debug.apk`
- Official APK size: `593655513` bytes
- Official APK SHA-256: `94f574560ec469772021e284a12eabb71211393d25388c6669d854d58810a8ed`
- Qwen3 model id: `Qwen3-4B-q4f16_0-MLC`
- Qwen3 model lib: `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
- arm64 runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`

The current RastaCoder `main` source tree contains compile inconsistencies introduced by the later broad rename from NavixMind/Coderasta to RastaCoder. The automated legacy source build is therefore disabled until those changes are reintroduced deliberately against this known-good baseline.

The first project APK is produced by verifying the exact upstream known-good APK byte-for-byte, retaining its tested Qwen3/runtime payload, and replacing its signing identity with the stable RastaCoder project development certificate. This gives the project a reproducible installable baseline before source-level changes are layered back incrementally.

Development signing certificate SHA-256:

`87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`

Build trigger provenance: this line was added through the repository Contents API so GitHub receives a normal push event for the deterministic baseline workflow.

Self-check trigger: 2026-08-25 11:58 +08:00. This is a no-code-change push used only to start the active `Produce Qwen3 Known-Good Baseline APK` workflow after revalidating the repository Actions state.

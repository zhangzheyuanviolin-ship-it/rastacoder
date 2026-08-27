# V16 MLC downloadable-model compatibility audit

## Decision

Do not add additional downloadable local-model entries in V16 unless their exact `model_lib` is already compiled into the fixed verified Android MLC runtime and the weight repository matches that library.

## Why an arbitrary MLC weight repository is not sufficient

The Android inference bridge calls `chatModule.reload(modelPath, modelLib)`. The downloaded model directory supplies weights/configuration, while the APK's packed MLC runtime supplies compiled model code identified by `model_lib`. Therefore a repository which merely contains MLC-formatted weights is not, by itself, proof that this application can load it.

Adding a genuinely new architecture, parameter configuration, or incompatible quantization normally requires rebuilding the MLC package/runtime so the matching model library is compiled into the Android native runtime. Even where MLC permits one compiled library to be shared by compatible variants, this project requires device-level loading/inference proof before exposing the variant to users.

## Exact V16 binary audit

The no-APK runtime probe extracts the exact known-good `libtvm4j_runtime_packed.so` whose SHA-256 is:

`5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`

It enumerates exact model-library identifiers matching the application's supported MLC families and strictly compares the full set. The runtime contains exactly these five:

- `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
- `qwen2_q4f16_0_ce81ef8767dfb3f843c79deb0b3f66fc`
- `qwen2_q4f16_0_1be22ffdc6429c5019af9af8dae22086`
- `qwen2_q4f16_0_ecc0cde57625a5817018e8d547361bb3`
- `ministral3_q4f16_0_68e08feb72d08c3826f6a0b3623b81fc`

Those are already the five entries exposed by `ModelRegistry`, `mlc-app-config.json`, and `mlc-package-config.json`. The V16 validator locks all three registries to this exact proven set.

## Result for V16

No new downloadable model is added. This is intentional: the current runtime contains no additional hidden compiled model library that can be exposed with the requested guarantee.

## Safe route for future expansion

A future model-expansion iteration should select candidate models first, then run the MLC packaging/compiler for each exact architecture/parameter/quantization combination, build the resulting Android runtime, and perform device smoke tests covering download, `reload`, first-token inference, multi-turn inference, and tool-calling behavior where applicable. Only models which pass those gates should be added to the user-visible downloadable list.

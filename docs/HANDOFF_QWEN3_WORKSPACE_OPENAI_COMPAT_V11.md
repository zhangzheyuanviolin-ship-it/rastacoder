# RastaCoder Qwen3 Workspace + OpenAI-Compatible v11 — verified release handoff

Current branch: `iteration/qwen3-workspace-openai-compat-v11`
Release tag: `qwen3-workspace-openai-compat-v11`
Version: `0.0.10` / code `24`

## V11 workspace/tool reliability fixes
- Removed human-readable optional-argument question-mark suffixes from compact local tool hints so Qwen3 4B no longer learns literal keys such as directory?, path?, recursive? and pattern?.
- Added a generic argument-key sanitizer that repairs trailing optional punctuation before schema validation, preserves canonical keys on collision, and records the repair.
- list_files now exposes one canonical model-facing path concept instead of competing directory/path semantics. Its path defaults to the app workspace root; common Android roots use path prefixes such as downloads/ and documents/.
- Boolean optionality pollution such as directory=true is repaired safely to the workspace default.
- list_files, file_manage, read tools, Office/media input paths and output paths now share one workspace-relative resolver. '.', './', output, workspace and output/... aliases converge on the same real output root.
- Relative nested paths such as folder/sub/file.txt are reusable across successive tool calls. output/... output names no longer create an accidental output/output directory.
- Workspace traversal outside the writable root is rejected before file access.
- Exact real-device failure calls from the V10 report are permanent V11 regression gates, plus a nested list/read/write multi-step chain.

## V11 OpenAI-compatible cloud provider
- Added an accessible settings screen for Base URL, API Key and Model ID using secure storage for credentials.
- Added an OpenAI Compatible model choice without changing the local-first default.
- Supports service root URLs, /v1 base URLs and complete /chat/completions endpoints.
- Converts the existing canonical tool schemas to OpenAI function tools and converts tool_calls, legacy function_call, finish_reason and token usage back into the existing Agent internal format.
- Assistant tool calls and tool results round-trip through native OpenAI assistant/tool roles while sharing the same compatibility normalization, tool executor, postconditions and bounded tool-result layer used by the rest of the app.
- API keys are injected privately from secure storage and are excluded from model-facing tool arguments.

## Inherited capability invariant
- 25 manually controlled Skills / exactly 37 canonical local functions.
- All V9 systemic postcondition/search/Office/media gates remain green.
- All V10 context-safe result, bounded local continuation and accessible conversation-history gates remain green.

## Final verification
- Package: `ai.navixmind`
- ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `18d6885dab2ccf6374081cc4536d39c950c03c4fa5a432a5fa3329364cdf28be`
- APK size: `517029980` bytes

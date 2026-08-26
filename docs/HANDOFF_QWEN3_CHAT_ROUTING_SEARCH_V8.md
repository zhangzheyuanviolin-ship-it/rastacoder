# RastaCoder Qwen3 Chat Routing + Search v8 — verified release handoff

Current branch: `iteration/qwen3-chat-routing-search-v8`
Release tag: `qwen3-chat-routing-search-v8`
Version: `0.0.7` / code `21`

## V8 real-device regressions addressed
- Cold-start inference routing now synchronizes the persisted selected model with the actual MLC runtime before every send. Normal chat text can no longer be consumed as a Claude API key.
- Tool activity is aggregated into one dedicated per-turn tool-progress region instead of many system-message rows.
- The assistant region contains the final answer, optional created-file links, one real Thinking expand/collapse control, and one independently collapsible Tool Diagnostics control.
- Thinking content is sanitized so structured tool calls/results are excluded; /no_think mode exposes no model reasoning and the UI explicitly says when the turn has no thinking content.
- Decorative role glyphs are excluded from the accessibility tree and repeated long-press/system semantic chatter is removed.
- File operations now resolve model-facing relative paths against the real output workspace. Recursive delete is post-verified; a still-existing or missing target cannot report false success.
- Four separate web-search Skills are added from local-agent-plaza: AnySearch, Exa, LangSearch, and Tavily. Each has independent manual enablement and secure per-provider API-key configuration.

## Capability invariant
- 25 manually controlled Skills.
- 37 canonical local functions with exact schema/Skill coverage equality.
- Search credentials are stored through Android secure storage and injected only into private execution context, never model-visible tool arguments.

## Verification
- Preflight and release gates reproduce output/subfolder/TXT recursive deletion against a real temporary filesystem and verify physical absence afterward.
- Search adapters are exercised with mocked HTTP requests for all four providers and missing-key failure gates.
- Flutter Analyze passes before the single formal APK build.
- Final package: `ai.navixmind`
- Final ABI: `arm64-v8a` only
- Stable signing certificate SHA-256: `87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`
- MLC runtime SHA-256: `5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- APK SHA-256: `e7b4ee6a444c46856bb7225fc64801578d6b1b91aa03f559b33e05285b4e220d`
- APK size: `516975512` bytes

# RastaCoder V12 post-release field failures -> V13 systemic tool ABI audit handoff

> 这是给下一上下文/下一智能体的强制接管文档。不要从聊天记忆猜测项目状态；先读本文件，再读 `docs/HANDOFF_QWEN3_WORKSPACE_ALIAS_HARDENING_V12.md`，然后从 V12 最终已验证源码开始审计。

## 0. Frozen baseline / 禁止误用旧基线

- Repository: `zhangzheyuanviolin-ship-it/rastacoder`
- Upstream fork source: `BoozeLee/rastacoder`
- Current released branch: `iteration/qwen3-workspace-alias-hardening-v12`
- V12 verified final HEAD before this documentation-only checkpoint: `a42715cc33668b43e01d1fed35bf59b20f80a451`
- V12 release tag: `qwen3-workspace-alias-hardening-v12`
- Version: `0.0.11` / code `25`
- Package: `ai.navixmind`
- 25 manually controlled Skills / exactly 37 canonical local functions.
- V11 OpenAI-compatible Chat Completions provider exists in Python/Flutter configuration code, but V12 real-device testing has now proved its UI send routing is broken before the request reaches that provider.

**Do not build V13 immediately.** First perform the systemic audit below. Freeze new Skills/features until a new end-to-end golden-path suite exists and passes.

## 1. Latest real-device status from the user

### 1.1 What V12 fixed successfully

The user's first V12 retest confirmed workspace listing now works. The previous `/workspace` failure that drove V12 is therefore considered fixed on real hardware.

### 1.2 DOCX basic read still fails end-to-end

Exact real-device log supplied by the user:

```text
正在调用工具：llm_generate
正在执行 1 tool(s)...
准备调用工具：read_docx - params: docx_path=dignitas_dynamic_report.docx, extract=true
工具调用失败：[MODEL_TOOL_ARGUMENT_ERROR] read_docx.extract received 'true'; allowed values: ['text', 'tables', 'all']. Retry with one allowed value.
正在调用工具：llm_generate
正在执行 1 tool(s)...
准备调用工具：read_docx - params: docx_path=dignitas_dynamic_report.docx, extract=text
工具调用成功：got 45015 chars
正在调用工具：llm_generate
本地模型连续达到单次输出上限，且没有产生可用正文。请调高“最大输出 Token”后重试。
```

Important interpretation:

- The DOCX parser itself demonstrably opened this file and extracted content: the corrected second call returned **45,015 characters**.
- The first failure is a model-facing tool-contract failure: Qwen3-4B interpreted the argument named `extract` as a boolean switch and emitted `true`, while the executor schema requires enum `text|tables|all`.
- The final user-visible task failed after tool success because the large extracted document result was fed back into the local-model ReAct loop and the model repeatedly hit its output limit without producing usable final prose.
- Telling the user to simply raise max output tokens is not an acceptable primary recovery strategy for document reading. This needs orchestration/result-ingestion redesign.

### 1.3 PPTX basic read still fails end-to-end / at least contract stage is confirmed broken

Exact real-device log supplied by the user:

```text
正在调用工具：llm_generate
正在执行 1 tool(s)...
准备调用工具：read_pptx - params: pptx_path=表演基础_情绪与角色塑造关键词_视觉增强版.pptx, extract=True
工具调用失败：[MODEL_TOOL_ARGUMENT_ERROR] read_pptx.extract received True; allowed values: ['text', 'slides', 'notes', 'all']. Retry with one allowed value.
正在调用工具：llm_generate
正在执行 1 tool(s)...
准备调用工具：read_pptx - params: pptx_path=表演基础_情绪与角色塑造关键词_视觉增强版.pptx, extract=text
工具调用成功：got 6979 chars
正在调用工具：llm_generate
```

Interpretation:

- The PPTX parser also successfully opened this real file after the model self-corrected, returning **6,979 characters**.
- The exact same semantic mismatch occurred: `extract=True` versus enum `text|slides|notes|all`.
- The pasted log ends at the subsequent `llm_generate`; the exact terminal state after that point is not included, so do not invent one. The user reports the PPT task did not complete normally.

### 1.4 PDF is suspected, not yet confirmed

The user has not supplied an equivalent PDF failure log yet. They reasonably suspect the same class of problem may appear. Treat PDF as a required regression target, not as a confirmed device failure.

### 1.5 OpenAI-compatible cloud model is currently blocked by Claude-key UI routing

Exact user-visible failure after configuring an OpenAI-compatible endpoint/key/model and selecting the cloud model:

```text
当前选择的是云端模型，但尚未配置 Claude API Key。请到设置中配置 API Key，您的聊天文本不会再被当作 API Key 输入。
```

This has been confirmed directly in V12 final source `lib/features/chat/presentation/chat_screen.dart`.

Current `_ensureSelectedRouteReadyForSend()` logic only distinguishes:

1. offline model -> local readiness/load checks;
2. every other model -> `StorageService.hasApiKey()` and Claude API-key gate.

Therefore `openai-compatible` is classified as generic cloud and is rejected before Python's `OpenAICompatibleClient` can be reached. The exact Chinese error above is hard-coded in that generic cloud branch.

Meanwhile `lib/core/bridge/bridge.dart` does correctly retrieve `getOpenAICompatibleConfig()` and inject `openai_compatible` context when `preferredModel == 'openai-compatible'`. Thus the feature is partially wired: storage/bridge/Python client exist; the Flutter send-readiness gate is wrong.

This is a deterministic integration bug and a validation-strategy failure. V11/V12 tests proved component pieces but did not test the real path: **select OpenAI Compatible -> no Claude key -> press Send -> request reaches OpenAI-compatible endpoint**.

## 2. Confirmed architectural problem: model-facing Tool ABI is still too executor-shaped

The current V12 model-facing schemas expose optional execution knobs that a 4B local model does not need to decide for ordinary user intent.

Examples from `python/navixmind/tools/__init__.py`:

- `read_docx(docx_path, extract)` where `extract` enum = `text|tables|all`
- `read_pptx(pptx_path, extract)` where `extract` enum = `text|slides|notes|all`
- `read_pdf(pdf_path, pages)`
- `read_xlsx(xlsx_path, sheet, range, extract)`

The compact local hints likewise expose these parameters directly. A small model naturally treats a verb-like field named `extract` as a boolean capability flag. Both real-device logs show exactly that behavior (`true` / `True`).

### 2.1 This enum design predates our Skill grouping

A first upstream audit was already performed against `BoozeLee/rastacoder` main. Upstream `python/rastacoder/tools/__init__.py` already defines:

- `read_docx.extract` as string enum `text|tables|all`, default `all`;
- `read_pptx.extract` as string enum `text|slides|notes|all`, default `all`;
- `read_xlsx.extract` as string enum `values|formulas|all`;
- `read_pdf.pages` as optional string.

Therefore the enum mismatch was not invented by our later Skill grouping.

However, our current local-small-model layer still exposes this upstream executor-oriented contract too directly. The project now specifically targets Qwen3-4B local tool use, so V13 must introduce a deliberate small-model Tool ABI instead of assuming Claude-shaped schemas are suitable for a 4B model.

### 2.2 Do not overstate upstream culpability yet

Upstream contains substantial local-LLM code/tests and may have had different behavior in its own original tool-selection/prompt path. The user explicitly suspects our Skill grouping or subsequent patches might have degraded existing local adaptations. This question is still open and MUST be audited historically in V13 before editing core contracts.

Required archaeology:

- identify the exact fork/base commit from which our NavixMind/tool-Skill changes diverged;
- compare upstream `python/rastacoder/agent.py`, `tools/__init__.py`, `tools/documents.py`, Flutter chat routing, native tool executor, local LLM client, and tests with our current counterparts;
- identify which local-model-specific normalization/retry/prompt behaviors existed upstream and were removed, bypassed, renamed, or superseded;
- classify every current failure as upstream-preexisting, introduced by our changes, or exposed by the new Qwen3-4B target.

Do not guess this classification from file names alone.

## 3. Confirmed architectural problem: long document results are only generically bounded

V10 introduced `_tool_result_char_budget()` and `_prepare_tool_result_for_model()` in `python/navixmind/agent.py`.

Current behavior:

- search tools have special structured result compaction;
- `list_files` has special logical/structured compaction;
- Office readers / PDF / generic long file readers fall mostly into generic text trimming/wrapping.

That is insufficient for a 45,015-character document when the user's actual task is typically “read/summarize/analyze this document”. A hard character ceiling does not create a good document-reading pipeline. It can discard important sections, leave an incoherent prefix, and still force a 4B model to digest a large block in one step.

V13 must treat `read_file`, `read_docx`, `read_pptx`, `read_pdf`, `read_xlsx`, large `web_fetch`, and similar content-producing tools as a **document/content ingestion family**, not as unrelated tools that happen to return strings.

Required direction:

- tool output should have structured sections/chunks + metadata/outline;
- compute available model budget after reserving system prompt, enabled tool schemas, conversation history, and output allowance;
- for long content, give the model a bounded outline/manifest plus query-relevant chunks;
- support staged chunk summarization / map-reduce / query-focused retrieval for long documents;
- preserve source/slide/page/table boundaries so follow-up reasoning can request more chunks deterministically;
- acceptance criterion is a usable final answer, not merely “tool returned N chars”.

The user should not be forced to increase output-token limits just to complete basic document reading.

## 4. V13 required systemic redesign: one small-model-facing Tool ABI for all 37 functions

Do not patch `read_docx.extract=True` alone. Do not patch `read_pptx` independently and move on. Build a reusable contract layer.

### 4.1 Separate model-owned intent from app-owned execution defaults

For every canonical local function, classify each parameter as:

- **model-essential**: the model must choose it to express user intent;
- **app-defaultable**: hide or default it in normal local-model calls;
- **advanced-only**: expose only when the user's request explicitly requires it.

Likely basic-reader examples:

- ordinary `read_docx`: model-facing call should normally need only `{docx_path}`; app can default to a safe comprehensive/text mode;
- ordinary `read_pptx`: normally `{pptx_path}`;
- ordinary `read_pdf`: normally `{pdf_path}`, page selection exposed only for explicit page-range requests or continuation;
- `read_xlsx`: path is essential; sheet/range may be task-dependent; extract mode should default safely.

Internal executor functions may retain richer schemas. The model-facing ABI and executor ABI do not have to be identical.

### 4.2 Generic compatibility/coercion rules across tools

Build deterministic normalization primitives and apply them systematically where semantics are clear:

- boolean / string-boolean supplied to enum-like “extract/mode” fields -> safe canonical default when unambiguous;
- case normalization (`True`, `TEXT`, etc.);
- trailing punctuation in keys (already partly handled from V11);
- null/empty optional fields;
- common aliases;
- scalar-vs-object repair only where deterministic;
- retain diagnostics for every repair;
- ambiguous repairs must fail with concise model-actionable guidance rather than silently changing intent.

### 4.3 Contract fuzz suite across all 37 canonical functions

Create a generated/systemic validator that exercises small-model-like mistakes for every function where applicable:

- booleans in enum fields;
- string booleans;
- enum capitalization;
- omitted optionals;
- explicit nulls;
- `?` suffix keys;
- common alias keys;
- scalar/object confusion;
- workspace aliases/path variants;
- duplicate canonical/alias collision policy.

The goal is to prove the adapter layer, not accumulate 37 unrelated patches.

## 5. Provider routing must become explicit capability routing

Replace the current binary worldview `isOffline ? local : Claude` with explicit provider identity/capabilities, at minimum:

- `local`
- `anthropic`
- `openai_compatible`

Readiness requirements:

- local -> model downloaded and loaded;
- Anthropic -> Claude API key required;
- OpenAI-compatible -> Base URL + Model ID required; API key optional because current Python client intentionally supports endpoints with no auth.

Both `_syncModelRouteState()` and `_ensureSelectedRouteReadyForSend()` must use provider identity. Do not send or require a Claude key on the OpenAI-compatible path.

Add an end-to-end Flutter/bridge/Python route test with a mocked local HTTP server that proves:

1. preferred model is `openai-compatible`;
2. Claude key is absent;
3. OpenAI-compatible Base URL + Model ID are configured;
4. user presses Send;
5. the request reaches the mocked `/v1/chat/completions` endpoint with the configured model/tool schema;
6. tool-call round trip returns through the same Agent loop.

Component-only client tests are no longer sufficient.

## 6. Golden-path end-to-end acceptance suite before any V13 APK

Freeze feature expansion and create realistic job tests. At minimum:

1. List workspace root and nested files.
2. Read a short DOCX and answer a question.
3. Read a long DOCX (~45k chars or larger) and summarize it without max-token failure.
4. Read a PPTX and summarize slide structure/content.
5. Read a multi-page PDF and answer a question; include a long-PDF case.
6. Read XLSX, identify sheets/range, perform a basic calculation/analysis.
7. Read a long text file.
8. Search provider returns several results and local model produces final answer.
9. `web_fetch` / headless browser basic content read.
10. `python_execute` scientific calculation and basic pandas-style data analysis.
11. Create Office file -> list -> reopen/read back -> modify -> reopen/verify.
12. OpenAI-compatible cloud model sends successfully with no Claude key.

Each test must assert the **user task completes with useful final prose/output**, not only that a tool function returned success.

## 7. Release discipline for V13

- Start from V12 final verified source, plus documentation checkpoint only.
- Create a dedicated V13 branch after audit.
- Do not trigger APK builds while still discovering architectural failures.
- Use deterministic no-APK preflight first.
- Only after all inherited V9/V10/V11/V12 gates + new V13 Tool-ABI/content-ingestion/provider-routing/golden-path gates are green, perform one formal APK build.
- Preserve package `ai.navixmind`, stable signing identity, ARM64-only and known-good MLC runtime unless a separately proven reason requires a change.
- Persist verified generated source and a final handoff before release publication.

## 8. Current engineering judgment / 项目是否值得继续

Current evidence does **not** show a fundamental technological impossibility.

Evidence:

- Qwen3-4B repeatedly chooses the correct canonical reader tool.
- It self-corrects after a schema error.
- Real DOCX parser returned 45,015 characters.
- Real PPTX parser returned 6,979 characters.
- Workspace listing now works on device after V12.
- OpenAI-compatible failure has an exact deterministic UI routing cause.

These are strong signs that the execution engines and local model can participate in a working agent. The current bottleneck is the adapter/orchestration architecture and our validation methodology.

The prior iteration strategy has been too reactive: a real-device symptom appears, then a narrow compatibility patch is added around that tool/model output. V9-V12 improved real pieces, but this strategy does not scale to 37 functions and 25 Skills.

V13 should be treated as an architectural checkpoint. If a unified small-model Tool ABI, structured long-content ingestion, explicit provider routing, and realistic golden-path suite can be made green, the project remains technically credible. If these systemic gates expose deeper failures across most tool families even after the adapter redesign, then reassess scope with evidence rather than continuing patch-by-patch.

## 9. Immediate first actions for the next context

1. Read this file and V12 verified handoff.
2. Fetch current V12 branch HEAD; recognize documentation-only commits after `a42715...` and locate the last verified source commit.
3. Perform upstream/fork history archaeology before editing.
4. Audit all 37 model-facing schemas and compact hints; produce a parameter-ownership inventory.
5. Audit `_prepare_tool_result_for_model()` and local context/output budgeting for document-family tools.
6. Audit Flutter model selection/readiness routing and bridge/provider selection end to end.
7. Write the proposed V13 architecture and acceptance matrix back into the repository before code changes.
8. Only then create V13 code changes and no-APK validation.

No V13 APK has been requested or authorized by this handoff itself; the next context should first report the audit/architecture to the user if that is the user's instruction.

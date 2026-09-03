# RastaCoder Stable v1.0.0 — 全项目终版交接与“本地智能体广场”下一阶段融合说明

> 本文档是当前 RastaCoder/Qwen3 本地智能体项目在进入下一阶段仓库融合前的总交接文件。新的上下文/新的 Agent 应优先读取本文件，再根据需要读取文末列出的历史交接与源码。不要依赖旧聊天上下文猜测当前状态。

## 0. 当前结论与稳定基线

截至 2026-09-03，用户已经在真实 Android 设备上完成 V17 版本测试，并明确确认“已经没有问题”。因此 V17 的应用源码与二进制产物被提升为当前项目第一条正式稳定产品基线，稳定发布标签使用 `stable-v1.0.0`。

仓库：`zhangzheyuanviolin-ship-it/rastacoder`

上游来源：`BoozeLee/rastacoder`

稳定源码基线分支：`iteration/qwen3-local-tool-contract-recovery-v17`

最后一条经过 V17 正式构建和构建后回归验证的应用源码提交：

`4da9cd51cf488fbd6164d01a41de076f95e8d050`

V17 迭代标签：`qwen3-local-tool-contract-recovery-v17`

稳定发布标签：`stable-v1.0.0`

应用内部版本：`0.0.16` / versionCode `30`

Package/Application ID：`ai.navixmind`

正式 APK：`RastaCoder-Qwen3-4B-local-tool-contract-recovery-v17-update.apk`

稳定发布复用同一字节内容，仅在 Stable Release 中可使用更清晰的稳定版文件名。禁止仅为了把 Android `versionName` 改成 `1.0.0` 而重新构建一个未经用户真机验证的新 APK。

APK SHA-256：

`689e736da9723d9ce37425ba39920600724a8bb3e187557bf0744d36800eea13`

APK 大小：`527182699` bytes

ABI：仅 `arm64-v8a`

稳定签名证书 SHA-256：

`87d560a2d8f7a7c7fb8fd66b40ac6a40fb8f210a4f436fa468ecbbaa5b6170b8`

已知良好 MLC runtime SHA-256：

`5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`

curl-cffi 私有 native companion：`libc++_shared-d523468d.so`

curl-cffi companion SHA-256：

`4f46ac4bd5f3f2f16e7c34bef7a7f65544d91bdc18853f201cf588e1d3d604c3`

V17 正式 Release workflow：`33053247983`，SUCCESS。

V17 锁定的全量 no-APK preflight：`33052838100`，SUCCESS。

锁定的 MLC/native binary probe：`33041507127`，SUCCESS。

### 关于仓库已有 `v1.0.0` 标签

仓库历史中已经存在一条 2026-03 的旧 annotated tag `v1.0.0`，它属于早期 Production Release 历史并指向旧提交。不得重写、强推或删除该标签。当前经过 Qwen3 本地工具链长期迭代并得到真机确认的第一条稳定发布使用 `stable-v1.0.0`，以保留历史可追溯性。

---

## 1. 项目当前产品定义

RastaCoder 当前稳定形态是一款 Android 本地优先智能体应用。核心价值并非单纯在手机上运行一个本地语言模型，而是让小型本地模型能够通过统一 Tool ABI、安全工作区、兼容修复层和 Android/Python 执行层完成真正的文件、Office、数据、媒体、网页、搜索与连接服务任务。

当前首要本地模型是 Qwen3-4B。项目围绕 3B～4B 级小模型的实际行为做过大量专门适配，包括：

- 只向模型暴露 canonical function 名，Skill ID 仅供 UI 手动选择；
- 模型面对的 schema 与 executor schema 可以分离；
- 隐藏可由应用决定的参数，降低小模型 enum/boolean/selector 错误；
- 对确定性的轻微参数错误进行兼容归一；
- 统一路径语义，屏蔽 Android 私有真实路径；
- 附件绝对路径采用显式白名单信任；
- 输出路径强制归属应用工作区；
- 对长工具结果压缩、结构化并重新注入模型；
- 支持连续多工具 ReAct；
- 工具调用诊断可区分 parser、compat、schema、path、executor、native 等阶段；
- Skill 启用/禁用始终由用户手动控制；
- local、Anthropic、OpenAI-compatible provider 路由分离。

当前稳定产品暴露 **25 个手动 Skill、37 个去重后的 canonical local functions**。

---

## 2. 总体执行架构

理解下一阶段融合时，建议把当前系统拆成以下层次：

### 2.1 Flutter UI 与状态层

关键文件：

- `lib/core/models/tool_skill.dart`
- `lib/features/settings/tool_skills_screen.dart`
- `lib/features/chat/presentation/chat_screen.dart`
- `lib/core/services/local_llm_service.dart`
- `lib/core/services/conversation_manager.dart`

职责：

- 展示 25 个手动 Skill；
- 存储用户启用的 Skill；
- 选择本地/云端模型；
- 管理聊天、Thinking、工具诊断和历史；
- 将附件、模型设置、搜索 API 配置等上下文送入 Python Agent；
- 维护本地模型加载和 MLC 推理状态。

### 2.2 Dart/Python Bridge

关键文件：

- `lib/core/bridge/bridge.dart`
- `lib/core/bridge/isolate_worker.dart`
- `python/navixmind/bridge.py`
- `android/app/src/main/kotlin/ai/navixmind/PythonMethodChannel.kt`

职责：

- Flutter 与 Chaquopy Python 之间传输请求、上下文、工具结果与日志；
- Python 需要 Android 原生能力时反向调用 native tool；
- 保持可序列化的 JSON 边界；
- 承载工具阶段诊断。

### 2.3 Agent / ReAct 编排层

关键文件：

- `python/navixmind/agent.py`

职责包括：

- 生成当前启用 Skill 对应的模型工具 schema；
- 本地 Qwen3 XML-style tool wrapper 与结构化 tool_calls 解析；
- parser 修复与不完整调用拒绝；
- 工具调用循环；
- 工具结果裁剪/结构化/重新注入；
- 长内容 ingestion；
- max-token/continuation 与 post-tool finalization；
- provider 路由；
- session/history 同步。

### 2.4 Canonical Tool Registry / 小模型 Tool ABI

关键文件：

- `python/navixmind/tools/__init__.py`
- `python/navixmind/tools/compat.py`
- `python/navixmind/tools/path_contract.py`

这是下一阶段最值得复用的架构核心之一。

`tools/__init__.py` 同时维护：

- 完整 executor/cloud schema；
- offline/local model schema；
- 25 Skill -> canonical functions 映射；
- 37 个函数的 compact prompt hint；
- local-small-model schema projection；
- canonical executor map；
- 手动 Skill permission boundary；
- schema validation；
- path/attachment/output normalization；
- native/Python executor dispatch；
- tool result postcondition verification。

`compat.py` 负责确定性兼容修复，包括常见别名、Skill-name hallucination、enum 大小写/boolean 误用、参数容器形状、输出文件名补全等。

`path_contract.py` 负责把模型看到的逻辑路径与真实 Android/应用文件路径分离。

### 2.5 Python/Chaquopy 工具实现层

关键模块：

- `python/navixmind/tools/documents.py`
- `python/navixmind/tools/extended_tools.py`
- `python/navixmind/tools/code_executor.py`
- `python/navixmind/tools/web.py`
- `python/navixmind/tools/media.py`
- `python/navixmind/tools/search_tools.py`
- `python/navixmind/tools/google_api.py`

这部分尤其适合作为下一阶段与“本地智能体广场”做功能融合时的候选可移植模块。

### 2.6 Flutter/Android native tool executor

关键文件：

- `lib/core/services/native_tool_executor.dart`

Python registry 中以下入口会通过 Bridge 调用 native executor：

- `ffmpeg_process` -> native `ffmpeg`
- `ocr_image` -> native `ocr`
- `smart_crop` -> native `smart_crop`
- `headless_browser` -> Flutter WebView/native browser path

因此迁移这些能力时，仅复制 Python schema/adapter 不足以形成完整功能。

### 2.7 MLC Android 推理层

关键文件：

- `android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt`
- `android/app/src/main/kotlin/ai/navixmind/services/ModelDownloadChannel.kt`
- `android/mlc4j/src/main/assets/mlc-app-config.json`
- `mlc-package-config.json`

职责：

- 模型下载与本地路径管理；
- MLC engine reload；
- token streaming；
- structured tool-call delta 合并；
- 性能与状态数据。

---

## 3. 稳定运行时与依赖基线

当前 Android 正式构建固定以下关键条件：

- Flutter：3.22.0
- Java：17
- Gradle：8.4（正式工作流使用）
- Chaquopy：16.1
- Android 内嵌 Python：3.13
- `cffi==1.17.1`
- `curl-cffi==0.16.2`，使用已验证 Android ARM64 wheel
- `numpy==1.26.2`
- `pandas==2.1.3`
- `matplotlib==3.8.4`
- `openpyxl>=3.1.5`
- `python-docx>=0.8.11` / 当前可解析 1.2.x
- `python-pptx>=1.0.2`
- `pypdf`
- `reportlab`
- `Pillow`
- `requests`
- `beautifulsoup4`
- `lxml`
- `yt-dlp`

curl-cffi 的官方 Android wheel `_wrapper.abi3.so` 依赖私有 hashed C++ runtime：

`libc++_shared-d523468d.so`

该文件必须以 exact DT_NEEDED 名称打入 `arm64-v8a` APK，并保持与 wheel 内 companion 字节一致。遗漏它会使 `download_media` 在 Android 上出现 `dlopen failed`。

---

## 4. 当前确认可用的 MLC 模型集合

V16 对最终 APK 所使用的已知良好 MLC runtime 做过二进制探测。该 runtime 内确认存在且当前应用已经注册的 model library 一共 5 个：

1. `ministral3_q4f16_0_68e08feb72d08c3826f6a0b3623b81fc`
2. `qwen2_q4f16_0_1be22ffdc6429c5019af9af8dae22086`
3. `qwen2_q4f16_0_ce81ef8767dfb3f843c79deb0b3f66fc`
4. `qwen2_q4f16_0_ecc0cde57625a5817018e8d547361bb3`
5. `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`

对应当前下载列表中的：

- Qwen3 4B
- Qwen2.5-Coder 0.5B
- Qwen2.5-Coder 1.5B
- Qwen2.5-Coder 3B
- Ministral-3-3B-Instruct-2512

Qwen3-4B 是当前工具调用核心验证模型。

稳定基线禁止凭模型权重格式看起来兼容就把任意 MLC 模型加入列表。新增模型的正确流程是：候选模型 -> 编译/打包匹配 model library/runtime -> Android 真机验证下载、reload、首 token、多轮对话、工具调用 -> 通过后再进入用户列表。

---

## 5. 25 个手动 Skill 与 37 个 canonical function

### 5.1 文件与文档

#### Skill 1：`text_files` — 文件与文本操作

函数：

- `read_file`
- `write_file`
- `file_info`
- `list_files`
- `file_manage`

能力：文本读取/创建、文件元信息、目录枚举、递归查找、mkdir、copy、move、rename、delete、exists、touch。

主要实现：`documents.py` + `extended_tools.py` + central path contract。

融合优先级：**最高**。Office 工具依赖这一组作为底层文件工作区。

#### Skill 2：`zip_archive` — ZIP 压缩与归档

函数：

- `create_zip`
- `list_zip`
- `extract_zip`
- `file_info`
- `list_files`
- `file_manage`

能力：创建 ZIP、压缩/存储模式、查看目录、安全解压、覆盖控制、管理归档文件。

主要实现：Python `zipfile`，`documents.py` + `extended_tools.py`。

融合优先级：高。

#### Skill 3：`pdf_read` — PDF 阅读与页面管理

函数：

- `read_pdf`
- `pdf_manage`
- `file_info`
- `list_files`

能力：全文/指定页读取、页数、合并、拆分、提取页、重排、删除页、旋转页。

主要实现：`pypdf`；基础读取位于 `documents.py`，页面操作位于 `extended_tools.py`。

融合优先级：最高。

#### Skill 4：`pdf_create` — PDF 创建与整理

函数：

- `create_pdf`
- `pdf_manage`
- `image_compose`
- `file_info`
- `list_files`

能力：文本/图片生成 PDF、页面管理、创建前图片处理。

主要实现：`reportlab` + `pypdf` + Pillow 图片路径。

融合优先级：最高。

#### Skill 5：`document_convert` — 文档格式转换

函数：

- `convert_document`
- `read_file`
- `read_pdf`
- `read_docx`
- `file_info`
- `list_files`

支持 TXT、DOCX、PDF、HTML 的文本导向转换。复杂版式转换会简化布局，定位应理解为“内容保真优先”的本地转换器。

主要实现：`documents.py`，依赖 python-docx、pypdf、reportlab、HTML/text parser。

融合优先级：最高。

#### Skill 6：`word` — Word 文档

函数：

- `create_docx`
- `read_docx`
- `modify_docx`
- `convert_document`
- `file_info`
- `list_files`
- `file_manage`

能力：

- 新建 DOCX；
- 读取正文/表格/元数据；
- 替换文本；
- 添加段落；
- 添加 heading/page break/table/image；
- 修改表格单元格；
- 转换格式；
- 文件复制/移动/重命名/删除。

主要实现：`python-docx`，核心在 `documents.py`。

融合优先级：**最高中的最高**，属于下一阶段最应该移植到“本地智能体广场”的办公核心。

#### Skill 7：`powerpoint` — PowerPoint

函数：

- `create_pptx`
- `read_pptx`
- `modify_pptx`
- `file_info`
- `list_files`
- `file_manage`

能力：

- 创建 PPTX；
- 读取 slide text、tables、speaker notes；
- 替换文本；
- 添加幻灯片；
- 更新 shape text；
- 设置备注；
- 文件管理。

主要实现：`python-pptx`；读取/修改在 `documents.py`，创建在 `extended_tools.py`。

V15 曾修复 `modify_pptx set_notes` 的系统性兼容问题，稳定版已经纳入回归。

融合优先级：**最高中的最高**。

#### Skill 8：`excel` — Excel

函数：

- `create_xlsx`
- `read_xlsx`
- `modify_xlsx`
- `file_info`
- `list_files`
- `file_manage`

能力：

- 创建 workbook/sheets；
- 读取 sheet/range/formula/value；
- set cell；
- set formula；
- append row；
- add/delete sheet；
- 文件管理。

主要实现：`openpyxl`；读取/修改在 `documents.py`，创建在 `extended_tools.py`。

V16 对 `create_xlsx` 做了重要兼容增强：接受 canonical `name + rows`、`sheet_name + data`、`{"item": [...]}` wrapper、record-dict rows，并在保存后重新打开 workbook 对每个写入单元格进行 exact round-trip verification。这个验证思路值得移植。

融合优先级：**最高中的最高**。

### 5.2 图像与多媒体

#### Skill 9：`ocr` — OCR 文字识别

函数：

- `ocr_image`
- `image_compose`
- `file_info`
- `list_files`

`ocr_image` 通过 Python registry -> Bridge -> Android/Flutter native OCR，底层使用 Google ML Kit text recognition。`image_compose` 可以在识别前裁剪、旋转、调整图片。

融合优先级：中高。迁移时必须检查目标应用是否已经有 OCR；若已有，优先保留目标应用 native OCR，只复用 canonical schema/工作流。

#### Skill 10：`image_processing` — 完整图片处理

函数：

- `image_compose`
- `smart_crop`
- `file_info`
- `list_files`
- `file_manage`

`image_compose` 覆盖 horizontal/vertical concat、overlay、resize、adjust、crop、grayscale、blur、rotate、flip、convert。主体为 Python/Pillow 路径。

`smart_crop` 通过 native bridge 使用人脸检测辅助裁剪。

融合优先级：中。

#### Skill 11：`video_processing` — 完整视频处理

函数：

- `ffmpeg_process`
- `file_info`
- `list_files`
- `file_manage`

结构化 operation：

- trim
- crop
- resize
- filter
- speed
- extract_frame
- extract_audio
- convert
- concat
- mix_audio
- merge_av
- custom

`ffmpeg_process` 由 Python adapter 通过 Bridge 调用 Dart native executor 的 FFmpeg 实现。`custom` 是高级 raw FFmpeg escape hatch。

融合优先级：中。若“本地智能体广场”已有 FFmpeg 工具，应比较 operation schema 和返回结构后合并，不宜简单重复引入另一套 FFmpeg plugin。

#### Skill 12：`audio_processing` — 完整音频处理

同样调用 `ffmpeg_process`。

覆盖：音频裁剪、MP3/WAV/M4A/AAC/FLAC/OGG/Opus 转换、音量、速度、滤镜、拼接、混音、视频提取音轨。

V6 针对小模型曾出现的 `audio_processing + generic param` hallucination 做过 canonical repair；V15 又修复 filter MP3 codec、mix_audio numeric duration 等真机/云端审计问题。

融合优先级：中。

#### Skill 13：`media_download` — 媒体下载

函数：

- `download_media`
- `file_info`
- `list_files`
- `file_manage`

实现链：`yt-dlp` 负责解析可下载音视频流 -> `curl-cffi` Chrome impersonation 负责最终 CDN transfer -> 写入 workspace。

YouTube 被明确屏蔽；支持平台取决于 yt-dlp extractor 与实际网络端。

V16 修复 Android `libc++_shared-d523468d.so` 缺失问题。迁移时必须连同 wheel/native companion 打包策略一起评估。

融合优先级：中低，除非目标仓库缺失该能力。

### 5.3 网络与搜索

#### Skill 14：`web_fetch` — 网页读取

函数：

- `web_fetch`
- `write_file`
- `file_info`
- `list_files`

`web_fetch` 使用 `requests + BeautifulSoup + lxml`，支持 text/html/links。普通本地模型 schema 会隐藏 `extract_mode`，默认读取可读文本。

融合优先级：中。

#### Skill 15：`dynamic_web` — 动态网页

函数：

- `headless_browser`
- `web_fetch`
- `write_file`
- `file_info`

`headless_browser` 通过 Bridge 调用 Flutter WebView/native implementation，支持 JS 渲染、等待和 CSS selector 提取。

融合优先级：中低，目标仓库若已有浏览器自动化，保留已有实现更稳。

#### Skill 16：`anysearch_search`

函数：

- `anysearch_search`
- `anysearch_extract`
- `anysearch_get_sub_domains`

模型只提交 query/URL/domain 等必要意图；API Key、结果数、域等配置由 UI/context 管理，避免密钥出现在模型工具参数中。

#### Skill 17：`exa_search`

函数：`exa_search`

支持搜索类型、日期、domain include/exclude、正文/摘要/高亮配置，模型-facing tool 只要求 query。

#### Skill 18：`langsearch_search`

函数：`langsearch_search`

支持 freshness/count/summary 配置。

#### Skill 19：`tavily_search`

函数：`tavily_search`

支持 basic/advanced、general/news、时间/域名过滤、answer 等配置。

四套搜索全部主要位于 `search_tools.py`，使用 `requests` 调远端 API。API keys 和 provider settings 从 `_context` 注入。

融合优先级：低到中。该部分早期就是参考/移植自本地智能体广场已有搜索 Skill，因此下一阶段大概率存在重合，应优先比较目标仓库当前版本，避免反向重复移植。

### 5.4 计算与数据

#### Skill 20：`basic_calculation`

函数：

- `python_execute`
- `read_file`
- `write_file`
- `file_info`

#### Skill 21：`scientific_calculation`

函数同上。

#### Skill 22：`data_analysis`

函数：

- `python_execute`
- `read_file`
- `write_file`
- `read_xlsx`
- `create_xlsx`
- `file_info`
- `list_files`

#### Skill 23：`charts`

函数：

- `python_execute`
- `write_file`
- `image_compose`
- `file_info`
- `list_files`

`python_execute` 是受控 Python sandbox。当前白名单包括 math/statistics/json/csv 等标准库，以及 NumPy、Pandas、Matplotlib、dateutil 等。Matplotlib 使用 `Agg` backend。

安全设计：

- restricted builtins；
- import whitelist；
- network module blocked；
- subprocess/socket/ctypes 等 blocked；
- 30 秒执行超时；
- 输出长度限制；
- 文件访问围绕显式输入与 OUTPUT_DIR；
- SafePath/SafeOS facade；
- V16 为 `os.path` 安全 facade 补齐 `exists/isfile/isdir/getsize/getmtime` 等只读探测；
- 任意系统路径访问仍受到 SecurityError 限制。

融合优先级：高。尤其适合补足目标仓库在数据分析、Excel 联动和图表输出方面的本地生产力能力。

### 5.5 Google

#### Skill 24：`gmail`

函数：`gmail`

当前稳定定义聚焦只读 OAuth 权限范围内的邮件 search/list/read。

#### Skill 25：`google_calendar`

函数：`google_calendar`

支持 list/create/update/delete 日程。

实现：`google_api.py`，令牌与 context 从应用层注入。

融合优先级：低到中，应先核对“本地智能体广场”当前 Google 工具体系与 OAuth 实现。

---

## 6. 37 个 canonical function 完整去重清单

下一阶段做工具能力矩阵时，请以这 37 个名字作为 RastaCoder 一侧的 canonical keys：

1. `python_execute`
2. `ffmpeg_process`
3. `smart_crop`
4. `ocr_image`
5. `read_pdf`
6. `create_pdf`
7. `read_file`
8. `write_file`
9. `file_info`
10. `create_zip`
11. `convert_document`
12. `create_docx`
13. `read_docx`
14. `read_pptx`
15. `read_xlsx`
16. `web_fetch`
17. `headless_browser`
18. `download_media`
19. `modify_docx`
20. `modify_pptx`
21. `modify_xlsx`
22. `google_calendar`
23. `gmail`
24. `image_compose`
25. `list_files`
26. `file_manage`
27. `list_zip`
28. `extract_zip`
29. `pdf_manage`
30. `create_pptx`
31. `create_xlsx`
32. `anysearch_search`
33. `anysearch_extract`
34. `anysearch_get_sub_domains`
35. `exa_search`
36. `langsearch_search`
37. `tavily_search`

Skill 可以复用同一个 canonical function。例如 `ffmpeg_process` 同时属于 video/audio；`python_execute` 同时服务基础计算、科学计算、数据分析、图表。模型最终只看去重后的函数集合。

---

## 7. 37 个函数按执行技术栈重新分类

这部分用于下一阶段决定迁移成本。

### 7.1 纯 Python/Chaquopy 为主，可优先模块化迁移

文件/Office/PDF/ZIP：

- `read_pdf`
- `create_pdf`
- `read_file`
- `write_file`
- `file_info`
- `create_zip`
- `convert_document`
- `create_docx`
- `read_docx`
- `read_pptx`
- `read_xlsx`
- `modify_docx`
- `modify_pptx`
- `modify_xlsx`
- `image_compose`
- `list_files`
- `file_manage`
- `list_zip`
- `extract_zip`
- `pdf_manage`
- `create_pptx`
- `create_xlsx`

数据：

- `python_execute`

普通网页：

- `web_fetch`

搜索 API：

- `anysearch_search`
- `anysearch_extract`
- `anysearch_get_sub_domains`
- `exa_search`
- `langsearch_search`
- `tavily_search`

连接服务：

- `gmail`
- `google_calendar`

媒体下载：

- `download_media`，主体 Python，但需要 Android ARM64 curl-cffi native companion，因此应视为“Python + native binary dependency”。

### 7.2 必须依赖 Flutter/Android native executor

- `ffmpeg_process`
- `ocr_image`
- `smart_crop`
- `headless_browser`

迁移这些函数时，需要同时检查目标仓库的 plugin、MethodChannel、权限、Activity/WebView lifecycle 与 ABI。

---

## 8. Office/文档体系：下一阶段最重要的迁移资产

用户下一阶段的主要目标是把当前项目在文档和办公处理方面已经相对完整的工具体系融合进“本地智能体广场”。因此下面这几层应作为一个整体审计，不能只复制几个 Python function。

### 8.1 实现层

核心：

- `documents.py`
- `extended_tools.py`

依赖：

- python-docx
- python-pptx
- openpyxl
- pypdf
- reportlab
- Pillow
- zipfile/shutil/os

### 8.2 Schema 层

核心：`tools/__init__.py`

迁移时要保留：

- executor schema；
- local-small-model projection；
- required/default/advanced 参数分类；
- compact prompt hints。

### 8.3 Compatibility 层

核心：`compat.py`

这是 Office 工具在 4B 模型上稳定工作的重要组成部分。历史上真实出现过：

- `read_docx.extract=true`；
- `read_pptx.extract=True`；
- 输出路径遗漏；
- Skill ID 被模型当函数名；
- 参数 generic wrapper；
- XLSX row/container 形状偏差；
- PPT notes operation 形状偏差。

当前设计会隐藏普通读取中应用可自行决定的 selector，例如本地模型看到 `read_docx(docx_path)`，应用内部再填充安全默认值。

### 8.4 Path contract 层

核心：`path_contract.py` + registry path resolution + `extended_tools.py` 二级边界。

Office 工具必须共享同一套逻辑工作区，否则模型在“创建 -> 列出 -> 再读取 -> 修改 -> 再验证”多步骤任务中很容易把逻辑路径、附件路径和 Android 私有路径混在一起。

### 8.5 Output postcondition 层

创建或修改文件成功后，当前工具链会验证目标文件实际存在、大小/结构合理；V16 XLSX 更进一步执行 reopen + cell-level roundtrip。

建议下一阶段迁移 Office 工具时把“执行成功条件”也一起迁移，避免 executor 返回 success 但文件实际空/损坏。

### 8.6 Long-content ingestion 层

Office reader 返回大文本以后不能直接无界塞回 4B 模型。V13 起将 `read_file/read_docx/read_pptx/read_pdf/read_xlsx` 等视为统一 content-ingestion family，进行预算控制、结构化、chunk/outline 和相关内容注入。

如果本地智能体广场已有自己的 context management，应把这套原则融合到其 Agent 编排层，不必强行复制当前 Agent 整体。

---

## 9. 统一工作区与路径安全模型

路径契约是 V11～V17 期间最重要的系统性成果之一。

### 9.1 模型只使用逻辑路径

模型面对：

- `.` = workspace root
- `folder/file.txt`
- `result.docx`

模型不应学习应用私有 Android 绝对路径。

### 9.2 bare `/` 的历史故障

V16 真机日志显示 Qwen3-4B 调用：

`list_files(path="/")`

旧 V12 path contract 漏掉 bare `/`，导致它落到 Android 操作系统根目录并触发 EACCES。V17 把 `/` 显式定义为 logical workspace root alias，同时在 3B～4B compat 层把这个调用归一成 `path="."`。

### 9.3 模型伪造绝对路径的处理

类似：

- `/foo.txt`
- `/folder/result.pdf`
- `/data/...`
- `/system/...`

只要不是应用明确允许的 Android public root 或显式 trusted attachment，就按 workspace-relative 意图处理，不允许模型通过拼写一个真实系统路径获得额外权限。

### 9.4 附件绝对路径白名单

应用把真实附件放入 `context['_file_map']`。只有 map 中 exact absolute path 被加入 trusted whitelist。

真实存在的系统文件也不会仅因为“存在”而成为可信输入。V17 CI 使用 runner 上真实 `/etc/passwd` 做负例，并用真实外部附件做正例。

### 9.5 输出永远归工作区

- `output_path`
- `output_dir`
- `destination_path`

统一进入严格 output boundary。输入附件的 trust 不能扩散到输出目的地。

### 9.6 迁移建议

下一阶段应优先判断本地智能体广场是否已经有成熟 workspace/path abstraction。若有，Office function 应适配到目标应用的 contract；若没有，建议整体迁移 RastaCoder 的 path contract 思路。不要让两个项目的“workspace”概念并存。

---

## 10. 小模型 Tool ABI 与兼容修复层

当前项目已经证明：把面向大型云模型的 executor schema 原样丢给 4B 模型，真实成功率不够稳定。

V13 以后形成了“小模型 Tool ABI”原则：

1. 参数分为 `model_essential`、`app_defaultable`、`advanced_optional`；
2. 本地模型 schema 是 deep-copied projection；
3. executor/cloud schema 保持完整；
4. 普通任务隐藏 app 可决定的 selector；
5. compatibility repair 在 strict schema reject 前运行；
6. 只做语义确定的 repair；
7. ambiguous repair 失败并返回可执行的简短纠错信息；
8. repair 后仍必须经过手动 Skill permission boundary。

本地模型隐藏参数目前明确包括：

- `read_docx.extract`
- `read_pptx.extract`
- `read_xlsx.extract`
- `web_fetch.extract_mode`

这套设计比单独修某一个工具的 hallucination 更值得迁移。

---

## 11. 工具调用解析、结果回注与多工具循环

V6～V17 逐步加强以下能力：

- UI Skill ID 与 callable function 严格分离；
- local XML tool wrapper parser；
- OpenAI-compatible native `tool_calls`；
- MLC streamed `choice.delta.tool_calls` 按 call index 正确累积；
- JSON brace/array repair；
- incomplete tool call 拒绝；
- malformed call bounded retry；
- model error 回到 ReAct loop 自修复；
- tool result JSON-safe boundary；
- logical path reinjection；
- long-result compaction；
- post-tool finalization recovery；
- 多工具调用不采用低次数硬上限；
- UI token streaming；
- 工具诊断 redaction。

下一阶段融合时，如果“本地智能体广场”的 Agent loop 已经更成熟，建议保留其主循环，把这里的兼容器、schema projection、path/output contract、postcondition 等作为可复用中间层融合进去。

---

## 12. Provider 路由

当前至少区分：

- local
- anthropic
- openai_compatible

readiness 语义：

- local：模型已下载/可加载；
- Anthropic：Claude API key；
- OpenAI-compatible：Base URL + Model ID，API key 可以根据目标 endpoint 需要决定。

V11/V13 期间曾发现 OpenAI-compatible 被 Flutter UI 错误套入 Claude key gate，后续已经系统化修复 provider readiness。

这部分下一阶段不是首要迁移目标，但如果融合时共用目标应用的云模型能力，要避免重复 provider state。

---

## 13. 从 V4 到 Stable v1 的开发演进

这里记录核心技术脉络，供下一上下文判断某段代码为何存在。

### V4：本地工具能力的实用基线

用户真机确认过 TXT -> DOCX、音频转换等本地工具可以工作。V4 后续成为“至少工具真的执行过”的经验比较点。

### V5：Skill UI、参数页、benchmark、Thinking

引入手动 Skill UI、模型参数、benchmark、Thinking 等产品功能，同时真实设备暴露小模型工具可靠性回退。

### V6：Tool Reliability + Chat History

重点：

- Skill ID 只留在 UI；
- canonical function schema；
- compat repair；
- malformed tool call recovery；
- Thinking/工具诊断；
- Isar persistent history；
- MLC structured tool delta accumulation。

### V7：Complete Skills

把完整能力扩展到文件管理、ZIP list/extract、PDF 页面管理、PPTX/XLSX 创建、image_compose 等，形成后来 25 Skill/37 function 的主体结构。

### V8：搜索体系

加入 AnySearch、Exa、LangSearch、Tavily；模型只给 query，key/settings 由应用管理。

### V9：Systemic Tool Hardening

从逐工具补丁转向通用 contract/compat/postcondition 回归，Office、native、search 等统一进入系统性验证。

### V10：Context-safe Search / History

8K context 下搜索结果 compaction、generic long-tool safety、可恢复 max-token continuation、历史 UI 继续加强。

### V11：Workspace + OpenAI-compatible

建立统一 workspace root、跨多步骤路径一致性、optional-key punctuation 修复、OpenAI-compatible native tool_calls roundtrip。

### V12：Workspace Alias Hardening

引入 central path contract，修复 `/workspace`/workspace alias 等真机路径问题，附件与 logical list result 继续规范化。

### V13：Systemic Tool ABI

真实 DOCX/PPTX 日志证明 4B 模型会把 `extract` enum 当 boolean。V13 由此形成全 37 function 参数分类、小模型 schema projection、schema-aware coercion、长文档 ingestion、provider capability routing。

### V14：Result Serialization / Streaming

JSON-safe shared boundary、brace-array repair、不完整 call 拒绝、post-tool finalization、UI streaming、history clear-all 等。

### V15：Tool Runtime Hardening

针对一次全量工具审计修复多个运行时真实问题，包括 PPTX notes、ZIP zero-byte、FFmpeg filter/mix、JPG case、Python file IO、OCR no-text、XLSX、download_media、`__version__` 等。

### V16：Residual Runtime Hardening + MLC Audit

继续修复：

- SafePath `os.path` 常见只读方法；
- XLSX create/read roundtrip 与兼容输入；
- curl-cffi Android native companion；
- 精确探测 APK MLC runtime 可用 model library；
- 拒绝未经验证的任意 MLC 模型扩张。

### V17：Local Tool Contract Recovery

V16 真机发现 Qwen3 `list_files(path="/")` -> Android root EACCES。V17 修复 exact call，同时对 37 个函数所有 path-bearing fields 自动做 inventory，建立 explicit attachment whitelist、strict model absolute-path boundary、scalar/array/nested/destination/output coverage，并重新跑完整 V9～V17 回归。

用户最终真机确认 V17“已经没有问题”，因此该版本成为 Stable v1 产品基线。

---

## 14. 当前测试与发布纪律

当前项目后期形成的发布原则必须保留：

1. 收集真实设备错误的 exact prompt/日志；
2. 先找系统性根因；
3. 把真实错误形状做成 deterministic regression；
4. no-APK preflight 跑完全量继承回归；
5. MLC/native binary 独立 probe；
6. preflight 全绿后只做一条正式 APK build；
7. 构建后再次运行 V9～当前版本回归；
8. 核对 package、version、ABI、签名、MLC runtime、native companion、APK SHA；
9. 持久化验证过的源码与 handoff；
10. 发布 GitHub Release；
11. 最后以用户真实 Android 验收作为稳定性最高证据。

这套纪律是项目从早期多轮构建试错走向稳定的重要原因。

---

## 15. 下一阶段与“本地智能体广场”融合时的正确工作顺序

新上下文开始后，先不要修改任何仓库，也不要先构建 APK。

### 第一步：读取两边当前源码

RastaCoder 一侧优先读取：

- 本文档；
- `lib/core/models/tool_skill.dart`；
- `python/navixmind/tools/__init__.py`；
- `python/navixmind/tools/compat.py`；
- `python/navixmind/tools/path_contract.py`；
- `documents.py`；
- `extended_tools.py`；
- `code_executor.py`；
- `native_tool_executor.dart`；
- `agent.py`。

然后读取“本地智能体广场”的最新稳定/实验分支、工具注册表、模型调用层、native executor、Python/JS/Kotlin 运行时、文件系统与所有已有工具。

### 第二步：做 exact capability mapping

以本文件第 6 节的 37 canonical functions 为 RastaCoder keys，逐个在目标仓库寻找：

- 同名同语义；
- 名字不同但能力相同；
- 目标仓库功能更强；
- RastaCoder 功能更强；
- 目标仓库完全缺失。

对每个能力最后只做四类决策：

- KEEP TARGET：保留本地智能体广场已有实现；
- PORT RASTACODER：迁移当前实现；
- MERGE：保留目标 executor，融合 RastaCoder schema/compat/功能；
- ADD NEW：目标完全缺失，新增 RastaCoder 能力。

不要看到工具名不同就重复注册两套能力。

### 第三步：第一优先级只处理 Office/文件生产力

建议 Tier A：

- read/write/list/file_manage
- DOCX create/read/modify
- PPTX create/read/modify
- XLSX create/read/modify
- PDF read/create/manage
- document_convert
- ZIP create/list/extract

这是当前项目相对完整、对目标仓库潜在增益最大的资产。

### 第四步：迁移共享 contract

根据目标仓库现状决定是否移植/重写：

- small-model schema projection；
- compat normalization；
- workspace/path contract；
- attachment trust；
- output boundary；
- output postconditions；
- long-content ingestion。

Office function 与这些 contract 一起迁移，真机成功率会显著高于只复制 executor。

### 第五步：第二优先级处理 Python 数据生产力

- python_execute
- Pandas/NumPy
- Matplotlib
- Excel 联动

如果目标仓库已有更成熟的 sandbox，应保留目标 sandbox，补充当前安全白名单/OUTPUT_DIR 语义和缺失包。

### 第六步：最后处理可能重合较大的能力

- OCR
- FFmpeg
- image processing
- media download
- web/browser
- AnySearch/Exa/LangSearch/Tavily
- Gmail/Calendar

这些能力在两个项目间更可能重复，先审计再决定。

---

## 16. 融合的主要技术风险

### 16.1 Schema 名字相同、参数语义不同

最危险的情况不是“没有工具”，而是两边都有同名函数但 required/default/enum/output shape 不一致。必须逐字段比较。

### 16.2 两套 workspace/path 语义冲突

如果目标仓库已有自己的 workspace，不要叠加 `/workspace`、`output` 等另一套虚拟根。确定唯一逻辑 namespace。

### 16.3 Chaquopy/Python 版本冲突

Office/Pandas/curl-cffi 是否能进入目标 APK，取决于它现有 Chaquopy/Python/ABI。尤其注意 numpy/pandas/matplotlib binary wheel 与 Android API level。

### 16.4 Android native plugin 冲突

FFmpeg、ML Kit、WebView、file picker 等 plugin 可能版本不同。应优先复用目标应用已有 native engine。

### 16.5 content:// URI 与真实路径

目标仓库附件入口可能使用 content URI。必须在进入 Python Office 层前有明确 materialize/copy 过程，不能假定所有附件天然是 POSIX path。

### 16.6 模型 tool-call 方言不同

目标应用若使用 llama.cpp/GGUF、MNN、MLC 或自定义模型，其 function calling 模板可能与本项目 Qwen3 XML wrapper 不同。Office executor 可以复用，Agent parser 不一定能原样搬。

### 16.7 APK 体积与 ABI

当前 APK 超过 500 MB。把完整 Python scientific stack、FFmpeg、MLC runtime 全部再叠到目标应用可能进一步增大体积。融合阶段应做 dependency deduplication。

### 16.8 curl-cffi native runtime

迁移 `download_media` 时必须带 exact hashed DT_NEEDED companion；否则 Python import 在桌面测试成功，Android 真机仍会 dlopen 失败。

### 16.9 权限和 scoped storage

RastaCoder 已对 common Android public roots做有限支持。目标应用若 targetSdk/storage policy 不同，需要重新真机验证 Documents/Download/Pictures/DCIM 等访问。

---

## 17. 下一阶段建议的模块化方向

如果目标是长期把两个项目的优势融合成一个应用，建议最终把 Office/文件能力抽象成类似以下逻辑模块，而不是继续把所有逻辑散在一个巨大 registry：

- `tool_contract`：canonical schema / local projection
- `tool_compat`：small-model deterministic repair
- `workspace_contract`：input/output/attachment path
- `office_tools`：DOCX/PPTX/XLSX/PDF/convert
- `archive_tools`：ZIP/file management
- `python_sandbox`：data/scientific/chart
- `native_adapters`：FFmpeg/OCR/WebView
- `tool_result_contract`：postcondition / logicalization / ingestion

下一阶段可以在“本地智能体广场”内部按其架构重新实现这个模块边界，无需保持 RastaCoder 文件名完全一致。

---

## 18. 当前绝对不要丢失的项目不变量

任何后续融合/重构都应显式保护：

1. 当前 Stable APK 的 SHA/签名/runtime 可追溯；
2. package `ai.navixmind` 在本仓库维护线保持不变；
3. 稳定签名 identity 不变；
4. 当前正式 APK ARM64-only；
5. Qwen3-4B 本地工具调用是首要验证场景；
6. 25 个 Skill 由用户手动控制；
7. 37 canonical function 不因 UI 分组重复注册；
8. model-facing Skill ID 不能成为 executable function；
9. compatibility repair 后仍执行 Skill permission check；
10. 模型使用逻辑 workspace path；
11. 附件绝对路径只接受应用显式白名单；
12. generated outputs 始终归 workspace；
13. tool result 返回模型前 logicalize/compact；
14. Office 写入后做 postcondition/roundtrip verification；
15. 不增加未经 matching MLC library + 真机验证的模型；
16. 不用随机多轮 APK 构建探索错误；
17. no-APK gate 全绿后再正式 build；
18. 大型 APK 通过 GitHub Release 交付。

---

## 19. 关键源码索引

### Tool/Skill/Agent

- `lib/core/models/tool_skill.dart`
- `lib/features/settings/tool_skills_screen.dart`
- `python/navixmind/agent.py`
- `python/navixmind/tools/__init__.py`
- `python/navixmind/tools/compat.py`
- `python/navixmind/tools/path_contract.py`

### Office / File / Data

- `python/navixmind/tools/documents.py`
- `python/navixmind/tools/extended_tools.py`
- `python/navixmind/tools/code_executor.py`

### Network / Connected services

- `python/navixmind/tools/web.py`
- `python/navixmind/tools/search_tools.py`
- `python/navixmind/tools/media.py`
- `python/navixmind/tools/google_api.py`

### Native bridge

- `python/navixmind/bridge.py`
- `lib/core/bridge/bridge.dart`
- `lib/core/bridge/isolate_worker.dart`
- `lib/core/services/native_tool_executor.dart`
- `android/app/src/main/kotlin/ai/navixmind/PythonMethodChannel.kt`

### MLC

- `lib/core/services/local_llm_service.dart`
- `android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt`
- `android/app/src/main/kotlin/ai/navixmind/services/ModelDownloadChannel.kt`
- `android/mlc4j/src/main/assets/mlc-app-config.json`
- `mlc-package-config.json`

---

## 20. 历史交接文档索引

如需追溯每一阶段为什么修改，可按顺序读取：

- `docs/HANDOFF_QWEN3_TOOL_RELIABILITY_V6.md`
- `docs/HANDOFF_QWEN3_COMPLETE_SKILLS_V7.md`
- `docs/HANDOFF_QWEN3_CHAT_ROUTING_SEARCH_V8.md`
- `docs/HANDOFF_QWEN3_SYSTEMIC_TOOL_HARDENING_V9.md`
- `docs/HANDOFF_QWEN3_CONTEXT_SAFE_SEARCH_HISTORY_V10.md`
- `docs/HANDOFF_QWEN3_WORKSPACE_OPENAI_COMPAT_V11.md`
- `docs/HANDOFF_QWEN3_WORKSPACE_ALIAS_HARDENING_V12.md`
- `docs/NEXT_CONTEXT_V13_SYSTEMIC_TOOL_ABI_AUDIT_HANDOFF.md`
- `docs/HANDOFF_QWEN3_SYSTEMIC_TOOL_ABI_V13.md`
- `docs/HANDOFF_QWEN3_SYSTEMIC_RESULT_STREAMING_V14.md`
- `docs/HANDOFF_QWEN3_TOOL_RUNTIME_HARDENING_V15.md`
- `docs/HANDOFF_QWEN3_RESIDUAL_RUNTIME_HARDENING_V16.md`
- `docs/V16_MLC_MODEL_COMPATIBILITY_AUDIT.md`
- `docs/HANDOFF_QWEN3_LOCAL_TOOL_CONTRACT_RECOVERY_V17.md`

---

## 21. 给下一上下文的启动指令

下一上下文接手时，可以把本节视为任务起点：

1. 先完整读取 `docs/STABLE_V1_FULL_PROJECT_HANDOFF_FOR_LOCAL_AGENT_SQUARE.md`；
2. 确认 RastaCoder `stable-v1.0.0` Stable Release 和当前源码指纹；
3. 访问用户另一个仓库“本地智能体广场”的最新源码、最新实验分支与交接记录；
4. 不修改任何代码，先穷举目标仓库已有全部工具及执行架构；
5. 用本文件第 6 节 37 canonical functions 与目标仓库逐功能对照；
6. 特别深挖 Word/PPTX/XLSX/PDF/convert/ZIP/file/Python data tools；
7. 对每项给出 KEEP TARGET / PORT RASTACODER / MERGE / ADD NEW 决策；
8. 同时比较 Tool ABI、path contract、attachment、output、postcondition、long-content ingestion，而不只比较 executor 函数；
9. 形成融合架构与迁移计划后先向用户汇报；
10. 用户确认以后，再进入代码修改和单次正式构建流程。

---

## 22. 最终状态一句话

**RastaCoder 当前已经形成一条由 Qwen3-4B 真机验证通过的 Android 本地智能体 Stable v1 基线：25 个手动 Skill / 37 个 canonical function、完整 Office/文件生产力体系、小模型 Tool ABI、统一 workspace/path contract、Python/Chaquopy 与 Android native 混合执行层均已进入可用于下一阶段跨仓库融合的稳定状态。**

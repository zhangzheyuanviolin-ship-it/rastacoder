# RastaCoder 项目交接文档

**用途：这是本项目下一轮开发的首要上下文入口。**

如果新的 ChatGPT / Codex / Agent 会话中，用户只提供下面这个仓库链接：

`https://github.com/zhangzheyuanviolin-ship-it/rastacoder`

接手者应当先读取本文件，再读取当前 `main`、`QWEN.md`、`.github/workflows/build-apk.yml`、`pubspec.yaml`、`mlc-package-config.json`、`android/mlc4j/src/main/assets/mlc-app-config.json` 以及与当前报错直接相关的源码，然后自行继续完成任务。不要要求用户重新解释本文件已经写明的背景、目标、设备、交付方式、历史失败和约束。

本文件记录截至 2026-08-25 的项目目标、当前仓库状态、已验证事实、历史失败、过程错误、仓库隔离要求和下一轮执行规则。

---

## 1. 项目身份与仓库边界

本项目唯一目标仓库：

`zhangzheyuanviolin-ship-it/rastacoder`

上游仓库：

`BoozeLee/rastacoder`

截至本交接文档创建前，用户 fork 的 `main` 与上游 `BoozeLee/rastacoder:main` 已核对为 identical，基线提交为：

`f8f42dfdbcad689a6bc2f9550bc3a6530ae6849e`

本文件提交后，用户 fork 的 `main` 会因为增加本交接文档而领先上游一个文档提交，这是预期变化。

### 强制仓库隔离规则

`local-agent-plaza` 是用户另一个完全独立的项目，和 RastaCoder 没有任何从属关系。

过去一次开发过程中，助手错误地把 `local-agent-plaza` 当成 RastaCoder 的临时 CI / builder 仓库，向其中创建了大量 `rastacoder-*` workflow、脚本、trigger、状态文件和交接文档。这个行为已经被认定为严重的仓库隔离错误。

该污染后来已完成清理：

- `local-agent-plaza/main` 恢复并核验到它自己原来的项目提交。
- 错误分支 `ci/rastacoder-builder-20260824` 已删除。
- 清理用临时分支也已删除。
- RastaCoder 自己此前的错误测试分支 `build/qwen3-4b-test-20260824` 已删除。
- RastaCoder `main` 上一个空的 Qwen3 构建触发提交 `fe594e9d56bf4dc607ef7fd80e160db9374e88a1` 已从主线移除，恢复到 `f8f42df...`。

**以后处理本项目时，不允许为了方便构建、保存日志、跑 Actions、存 APK、存交接文档或任何其他目的去修改 `local-agent-plaza`。RastaCoder 的代码、分支、workflow、构建产物、release 和交接资料都必须留在 `rastacoder` 自己的仓库体系内。**

只有用户在另一项任务中明确要求处理 `local-agent-plaza` 时，才可以进入那个仓库。

---

## 2. 用户的实际目标

用户不会写代码，也不会人工阅读和编辑仓库内容。用户明确要求开发 Agent 自己完成 GitHub 侧的读取、修改、构建、故障排查、验证、清理和交付。

因此，本项目不能把“请用户自己修改某个文件”“请用户自己运行命令”“请用户自己去 GitHub 删除分支”“请用户自己下载日志再发回来”作为正常解决方案。

接手者应当通过可用的 GitHub 工具和云端 workflow 自己完成端到端操作。

### 当前第一阶段明确目标

构建出一个**可以直接安装的 Android APK**，用于用户在真机上测试 RastaCoder 的 Qwen3 4B 本地模型能力。

要求：

1. 目标模型是 **Qwen3 4B**，不能把 Qwen2.5 当成最终测试模型交付。
2. 当前项目使用的目标模型仓库为：
   `alexandertaboriskiy/Qwen3-4B-q4f16_0-MLC`
3. 当前模型量化/运行形态：`q4f16_0`。
4. 当前已验证的 MLC `model_lib`：
   `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
5. 当前模型配置：
   - `context_window_size`: 4096
   - `prefill_chunk_size`: 2048
   - `max_batch_size`: 1
   - `bundle_weight`: false
6. `bundle_weight=false` 是允许的，也是当前项目本来的设计。APK 不需要把约 2.28 GB 的模型权重整个塞进安装包；权重可由应用按需下载。关键是 APK 内必须包含能识别并运行 Qwen3 4B 的正确模型注册信息和对应运行库。
7. 用户目标设备为 Android arm64 真机，主要测试设备为 Redmi K70 Pro，Snapdragon 8 Gen 3，24 GB RAM / 1 TB 存储。
8. 优先交付标准的、可直接安装的 `arm64-v8a` Release APK；不要交付 XAPK。
9. 用户已经亲自安装和测试过项目已有的官方 APK，并确认应用本身有明显继续开发价值。最终目标不止是“编译一次”，后续还要基于成功安装包继续优化和开发大量功能。

### APK 最终交付规范

成功构建后：

- APK 应发布到 `zhangzheyuanviolin-ship-it/rastacoder` 自己的 GitHub Release 或该仓库可稳定访问的 GitHub 构建产物位置。
- 对超过 20 MB 的大型 APK，不要把沙盒下载链接作为最终交付链接。
- 最终向用户提供 GitHub 浏览器可直接访问的下载链接。
- 同时报告：
  - 精确 APK 文件名
  - 精确字节大小
  - SHA-256
  - 源提交 SHA
  - ABI，至少确认 `arm64-v8a`
  - Qwen3 4B `model_id`
  - Qwen3 4B `model_lib`
  - `bundle_weight=false` 状态
  - APK 内是否实际包含需要的 MLC native runtime

---

## 3. 当前源码中已经确认的 Qwen3 事实

当前 `mlc-package-config.json` 已经包含 Qwen3 4B：

- model: `HF://alexandertaboriskiy/Qwen3-4B-q4f16_0-MLC`
- model_id: `Qwen3-4B-q4f16_0-MLC`
- estimated_vram_bytes: 2500000000
- bundle_weight: false
- prefill_chunk_size: 2048
- context_window_size: 4096
- max_batch_size: 1

当前 `android/mlc4j/src/main/assets/mlc-app-config.json` 也已经包含 Qwen3 4B：

- model_id: `Qwen3-4B-q4f16_0-MLC`
- model_lib: `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
- model_url: `https://huggingface.co/alexandertaboriskiy/Qwen3-4B-q4f16_0-MLC`
- estimated_vram_bytes: 2500000000

上游加入 Qwen3 4B 的关键提交：

`c739dada4c67e310eba27cc32e38ebec5b51752b`

提交标题：

`Add Ministral 3B and Qwen3 4B offline models, fix MLC build integration`

这个提交除了加入 Qwen3 4B，还包含 MLC4J Kotlin serialization / TVM jar 可见性等集成修复。

上游后续还有一条与 Qwen3 工具调用直接相关的提交：

`e165c311eb464722c5db0883426e82af69468330`

提交标题：

`Fix offline model tool call parsing for Qwen3 and Ministral`

它处理了 Qwen3 `<think>...</think>`、Markdown code fence、文本形式 tool call、嵌套 JSON 等解析问题。未来验证 Qwen3 工具调用时，这条历史必须纳入检查。

---

## 4. 当前官方构建链事实

当前仓库自带：

`.github/workflows/build-apk.yml`

截至本文件创建时，该 workflow 的主要环境和行为如下：

- `ubuntu-latest`
- Java 17，Zulu
- Flutter `3.19.0` stable
- Android SDK setup
- `flutter pub get`
- 缺少 gradle wrapper 时执行 `gradle wrapper`
- `flutter build apk --debug --split-per-abi`
- `flutter build apk --release --split-per-abi`
- 上传 debug 和 release APK artifact
- tag 构建时尝试创建 GitHub Release

一个关键事实：**这个官方 workflow 当前没有显式运行 `mlc_llm package`，也没有显式生成并复制 `android/mlc4j/output/`。**

与此同时，当前仓库中的 `android/mlc4j/` 只看到 `build.gradle` 和 `src/`，没有提交一个现成的 `output/` 目录。

这个事实需要调查，但不能再次直接跳到“必须自己从零重建整套 MLC/TVM native runtime”的结论。上一轮在没有先跑通应用自身 Flutter/Dart 编译基线之前，过早进入 MLC/TVM 深水区，已经造成大量无效构建。

正确处理方式是：先核对官方/作者实际成功 APK 的构建来源、workflow 运行历史、当前源码可编译性、APK 内 native runtime 来源，然后再基于证据确定缺失环节。

---

## 5. 当前源码中已经验证存在的应用层编译问题

上一轮最后一次较深的构建已经进入 Flutter/Dart 编译阶段，暴露了多个应用源码问题。之后仓库被恢复到原始 `main`，这些源码问题没有被修复；其中至少部分已经重新直接从当前源码核验存在。

### 5.1 `pubspec.yaml` 的依赖问题

当前 `pubspec.yaml` 仍包含：

- `flutter_gradient_widgets: ^1.0.0`
- `flutter_custom_clippers: ^2.1.1`

上一轮云端 `flutter pub get` 过程中已经实际出现：

- `flutter_custom_clippers ^2.1.1` 无法解析，当时可见版本为 `2.1.0`。
- `flutter_gradient_widgets` 当时无法从 pub.dev 正常解析，并且仓库代码搜索没有发现实际 import 使用。

这属于真实构建失败记录。下一轮应重新基于当前包源验证，不能直接假定问题已经自然消失。

### 5.2 旧包名 `coderasta`

当前项目 `pubspec.yaml` 的 package name 是：

`rastacoder`

但当前源码 `lib/features/legal/legal_acceptance_dialog.dart` 等法律页面仍然存在：

`import 'package:coderasta/...';`

上一轮 Flutter 编译实际报错：

`Couldn't resolve the package 'coderasta' in 'package:coderasta/app/theme.dart'.`

并进一步造成 `RastaTheme`、`StorageService`、`AnalyticsService`、Terms / Privacy 相关符号级联解析失败。

这不是 MLC 问题，是当前应用源码自己的 package/import 一致性问题。

### 5.3 `RastaTheme` 重复静态常量

当前 `lib/app/rasta_theme.dart` 中，“Status indicators” 一组常量被重复声明。

重复项至少包括：

`iconCheck, iconError, iconWarning, iconInfo, iconSend, iconClose, iconMenu, iconAdd, iconSearch, iconSettings, iconHome, iconBack, iconForward, iconRefresh, iconDownload, iconUpload, iconShare, iconCopy, iconDelete, iconEdit, iconSave, iconLock, iconUnlock, iconUser, iconAI, iconBrain, iconSparkle, iconZion, iconBabylon`

上一轮 Dart 编译已经因为这些重复定义失败。

该重复内容在恢复后的原始源码中也重新核验存在。

### 5.4 Flutter API 类型错误

上一轮构建在：

- `lib/app/theme.dart`
- `lib/app/rasta_theme.dart`

遇到：

`The argument type 'CardTheme' can't be assigned to the parameter type 'CardThemeData?'.`

这和实际使用的 Flutter SDK / Material API 版本直接相关。

不要在未确认项目预期 Flutter 版本之前随意换到很新的 Flutter，再把新版本 API 错误当成项目本身设计问题。

当前官方 `build-apk.yml` 明确固定 Flutter `3.19.0`，这是下一轮建立基线时必须优先尊重的事实。

### 5.5 `RastaBrailleSpinner` const 调用

上一轮：

`lib/features/chat/presentation/widgets/status_banner.dart:38`

出现：

`const RastaBrailleSpinner(size: 16)`

`Not a constant expression.`

这个问题需要在使用项目预期 Flutter / Dart 版本的真实基线构建中重新核验。

---

## 6. 历史错误构建路线与失败事实

以下内容用于防止重复踩坑，不代表未来必须继续任何旧路线。

### 6.1 早期 v1-v8 失败类别

过去连续进行了多轮构建尝试，早期失败涉及：

- GitHub Actions 命令/依赖环境问题。
- Flutter package 版本解析问题。
- TVM Python API 时代不匹配。
- 新旧 MLC native API 混用。
- Java binding 与 native runtime 不匹配。
- DLight / native 编译或加载阶段失败。

部分早期日志没有作为独立永久文件保留，所以以后不要编造不存在的逐行日志；只能使用能从 GitHub Actions、提交、当前源码或本文件中核验的事实。

### 6.2 v9：历史 MLC/TVM 全量 native 构建路线

曾经尝试用一套历史 MLC / TVM 快照全量构建 native runtime。

相关历史快照曾定位为：

- MLC: `988383e38de325de0301dd1225d1fe1fd8d08f4b`
- TVM / Relax: `b3d4fe9fa8860804ee166549ad1898276273eb93`
- TVM-FFI: `c78e8b4eefa076c457af97bd3930dd664aec71c3`

v9 历史失败 run：

- Run ID: `32788795937`
- Job ID: `97626091663`

这一轮在 Python JIT 加载 LLVM `PassBuilder` 的静态初始化阶段发生 native segmentation fault，没有生成 APK。

这些历史 SHA 只是失败路线的证据。未来不能因为它们曾经被找到，就默认它们是正确或必须继续的构建基线。

### 6.3 已验证的外部作者 APK / runtime 证据

在排查过程中，还核验过同一开发者生态中的：

`alexandertaboriskiy/navixmind`

`v0.5.0-beta` 的 `app-debug.apk`。

当时核验事实：

- APK 大小：593,655,513 bytes
- APK SHA-256：`94f574560ec469772021e284a12eabb71211393d25388c6669d854d58810a8ed`
- 包含：`lib/arm64-v8a/libtvm4j_runtime_packed.so`
- runtime 大小：38,786,520 bytes
- runtime SHA-256：`5a3bb01f0819e85c07f58602161f6d020ecbf3e7f65922c9dfe898cfa0820c48`
- 其 `mlc-app-config.json` 中出现和本项目一致的 Qwen3 model_lib：
  `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`

这证明同一个 Qwen3 model_lib 曾经存在可运行 Android native runtime 组合。

它仍然只是外部证据。未来是否复用该 runtime，必须根据 RastaCoder 自己的 MLC Java/Kotlin binding、ABI、TVM API 和 APK 构建链进行兼容性验证，不能直接当成无需证明的最终路线。

### 6.4 v10 多次子失败

v10 路线连续暴露了几个不同层次的问题：

#### v10-1

`flutter pub get` 因：

`flutter_custom_clippers ^2.1.1`

无法解析而失败。

#### v10-2

进一步遇到：

`flutter_gradient_widgets`

无法正常从包源解析。仓库内也没有发现对应实际 import 使用。

#### v10-3

包依赖处理后，曾使用较新的 Flutter / Gradle 组合，Flutter Gradle plugin 在 `FlutterPlugin.kt` 出现 `filePermissions`, `user`, `read`, `write` 等 unresolved reference。

后来尝试把临时构建栈改成：

- Gradle 8.10.2
- AGP 8.8.2
- Kotlin 2.2.20
- Chaquopy 16.0.0
- JDK 17
- compileSdk 35

这套配置只是当时的临时实验，不是当前项目的正式构建标准。

#### v10-4

历史 Run：

- Run ID: `32797105750`
- Job ID: `97650554007`

构建到 Android Gradle 阶段后失败：

`Conflicting configuration : 'armeabi-v7a,arm64-v8a,x86_64' in ndk abiFilters cannot be present when splits abi filters are set : armeabi-v7a,x86_64,arm64-v8a`

原因是同时存在：

`abiFilters "armeabi-v7a", "arm64-v8a", "x86_64"`

和：

`flutter build apk --release --split-per-abi`

这个组合直接产生 ABI filter 冲突，浪费了一次云端构建。

之后临时路线改成了 arm64 only：

`flutter build apk --release --target-platform android-arm64`

这同样只是历史试验路线。

#### v10-5：最后一次失败构建

历史 Run：

`32797477397`

Job：

`97651612597`

当时 head SHA：

`8fbb3226eeee36fcda505fbf9f996778c3b16196`

这次构建已经通过了许多 native / dependency 阶段，最终在 Flutter/Dart 应用源码编译失败。

主要报错包括：

1. `package:coderasta/...` 旧包名无法解析。
2. `lib/app/rasta_theme.dart` 大量 static const 重复定义。
3. `CardTheme` 与 `CardThemeData?` API 类型错误。
4. `RastaTheme`、`StorageService`、`AnalyticsService`、Terms / Privacy 等符号的级联错误。
5. `const RastaBrailleSpinner(size: 16)` 不是常量表达式。

构建结尾：

`Target kernel_snapshot_program failed: Exception`

`Execution failed for task ':app:compileFlutterBuildRelease'.`

`Gradle task assembleRelease failed with exit code 1`

最终目标 APK：

`RastaCoder-Qwen3-4B-arm64-v8a-release.apk`

没有生成，也没有上传。

当时 upload-artifact 步骤使用 `if-no-files-found: ignore`，所以 UI 上上传步骤可以显示成功，但实际上日志明确表示：

`No files were found with the provided path ... No artifacts will be uploaded.`

这类“步骤绿色 = APK 存在”的误读以后绝对不能再次发生。

当时唯一存在的是 diagnostics ZIP，不是 APK。

---

## 7. 上一轮助手自身的过程错误

这些错误必须被下一轮接手者当成反例。

### 错误 1：没有先建立完整的应用层编译基线

在连续多轮云端构建中，太早把注意力集中在 MLC、TVM、native runtime、Java binding、Gradle 和 ABI 上。

结果直到 v10-5 才真正暴露当前源码自己的 Dart/Flutter 编译问题。

以后应先确认“当前官方栈 + 当前源码”到底在哪一层第一次失败，再决定下一层怎么处理。

### 错误 2：过早重建复杂 native 技术栈

在充分核实作者已有 APK、相同 Qwen3 model_lib 和 native runtime 之前，花费大量构建轮次尝试重新拼 MLC/TVM。

这造成了 Python API、Java binding、native runtime 和不同历史版本之间的时代错配。

### 错误 3：混用不同年代的 MLC / TVM 接口

旧/new MLC、TVM、TVM-FFI、Java/Kotlin binding 和 native runtime 混合，产生了真实的不兼容。

未来每一个 native 组件都必须能追溯到同一套兼容版本或有明确兼容证明。

### 错误 4：v9 在错误路线持续投入

v9 已经在 LLVM PassBuilder JIT 阶段 native segfault，说明该路线本身风险极高，但此前投入过多。

### 错误 5：自行升级 Flutter / Gradle 栈，偏离项目官方基线

项目当前官方 workflow 明确 Flutter `3.19.0`。

上一轮却在排错中切换到明显更新的 Flutter / Gradle / AGP / Kotlin 组合，引入了额外兼容层问题。

以后首先尊重仓库自己固定的工具链，再有证据地升级。

### 错误 6：ABI 配置冲突

同时使用 `ndk abiFilters` 和 `--split-per-abi`，造成可预防的 AGP 失败。

### 错误 7：对绿色 upload step 产生错误判断风险

`if-no-files-found: ignore` 会让“没有 APK”也出现成功步骤。

以后必须检查 artifact 列表和具体文件，而不是只看步骤颜色。

### 错误 8：连续触发过多云端构建，但没有形成层级化诊断

构建次数很多，却没有严格遵守：

`源码依赖 -> Dart 编译 -> Android/Gradle -> Chaquopy -> MLC Java/Kotlin -> native runtime -> APK 内容 -> 真机加载`

这样的逐层基线。

### 错误 9：污染了另一个完全无关的用户仓库

这是整个过程中最严重的工程管理错误。

把 RastaCoder 的构建内容放进 `local-agent-plaza`，导致两个用户项目被人为混在一起。

虽然之后已经完成清理和恢复，但以后必须执行“一个项目一个仓库”的严格边界。

### 错误 10：给用户制造了本不该存在的手动善后风险

用户明确不会读写代码，也无法依靠视觉界面手动清理 GitHub 仓库。

以后如果助手自己造成分支、workflow、release、tag、文件等污染，助手必须自己负责恢复，不能把善后甩给用户。

---

## 8. 下一轮接手时的执行顺序

下一轮目标仍然是拿到**实际可安装、可验证 Qwen3 4B 的 APK**，不要只写分析报告后停止。

### 第一步：立即读取上下文，不重复询问用户

至少读取：

- `RASTACODER_HANDOFF.md`
- `QWEN.md`
- `README.md`
- `.github/workflows/build-apk.yml`
- `pubspec.yaml`
- `android/app/build.gradle`
- `android/build.gradle`
- `android/settings.gradle`
- `android/mlc4j/build.gradle`
- `mlc-package-config.json`
- `android/mlc4j/src/main/assets/mlc-app-config.json`
- `lib/core/models/*`
- `lib/core/services/local_llm_service.dart`
- `android/app/src/main/.../MLCInferenceChannel.kt`
- 当前 Dart 编译报错涉及的 theme/legal/status widget 文件

同时检查当前上游 `BoozeLee/rastacoder` 是否出现比本交接更新的提交、workflow 或 release。

### 第二步：建立“官方源码 + 官方工具链”的干净基线

优先使用仓库自己的 `build-apk.yml` 所声明的 Flutter 3.19.0 / Java 17 作为第一基线。

第一目标是得到完整、可审计的首次失败点。

如果 `flutter pub get` 因当前依赖版本失败，做最小、可解释、在 RastaCoder 自己仓库内的修复。

如果进入 Dart compile，则先修复应用源码编译错误，不要同时大规模改 MLC/TVM。

每一轮修改应当能回答：

“这次只解决了哪一个已验证阻塞点？”

### 第三步：应用层必须先编译通过

当前已知优先检查：

- `coderasta` -> `rastacoder` package/import 一致性
- `RastaTheme` 重复常量
- `CardTheme` API 与项目实际 Flutter 版本匹配
- `RastaBrailleSpinner` const 问题
- 不可解析或未使用的 pub dependencies

处理这些问题时，保持功能语义，避免为了过编译直接删除用户功能。

### 第四步：再处理 MLC runtime 完整性

应用层通过后，检查最终 Android 构建是否确实拥有：

- 对应 arm64 的 `libtvm4j_runtime_packed.so`
- TVM/MLC Java/Kotlin binding 与 native runtime 一致
- `mlc-app-config.json`
- Qwen3 model_lib `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`

调查 native runtime 的来源时，可参考：

- 上游历史 `c739dada...`
- 当前作者生态已验证 APK
- 当前 MLC package 配置
- 官方 RastaCoder workflow / Actions 历史

但不要预先锁死成旧 v9/v10 的任何路线。

### 第五步：只在 RastaCoder 仓库内构建和发布

允许：

- 在 `rastacoder` 创建专用构建分支
- 在 `rastacoder` 创建/修改 workflow
- 在 `rastacoder` 运行 Actions
- 在 `rastacoder` 创建 Release

禁止：

- 借用 `local-agent-plaza`
- 借用用户其他项目仓库存 RastaCoder 构建文件
- 为了方便把跨项目文件混在一起

### 第六步：成功 APK 必须做内容验证

在宣布成功前，至少验证：

1. APK 文件真实存在。
2. 文件大小大于 0，且符合正常 Android APK 规模。
3. `unzip -l` 或等价方式确认 arm64 native library 存在。
4. APK 中的 MLC app config 包含 Qwen3 4B。
5. model_lib 精确匹配：
   `qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc`
6. 计算 SHA-256。
7. 确认 GitHub Release / asset 真实可访问。
8. 不得因为 upload step 绿色就宣布成功。

### 第七步：最终交付

最终只在真实 APK 完成后向用户报告成功。

提供 GitHub 下载链接和验证信息。

用户拿到 APK 后会真机安装测试；如果真机出现模型下载、模型加载、工具调用或 UI/无障碍问题，再以日志为依据继续迭代。

---

## 9. 成功标准

本阶段只有满足下面条件才算完成：

- 用户能够从 GitHub 直接下载 APK。
- APK 能直接安装到 arm64 Android 设备。
- 应用能启动。
- 应用内可选择/识别 Qwen3 4B。
- 模型下载机制指向正确 Qwen3 4B 仓库。
- 对应 Qwen3 model_lib 已在 APK runtime 配置中注册。
- native runtime 真实存在且 ABI 正确。
- 用户可以继续在真机验证模型加载和本地 Agent / tool calling。

“workflow 运行结束”“某个步骤绿色”“生成 diagnostics ZIP”“源码理论上支持 Qwen3”“模型写在 JSON 里”都不能单独视为最终成功。

---

## 10. 本交接文档对未来 Agent 的直接要求

如果你是后续接手本项目的 Agent：

1. 先读本文件，别让用户再重复历史。
2. 只操作 `zhangzheyuanviolin-ship-it/rastacoder`。
3. 自己读取 GitHub、Actions 和源码，不把技术操作转嫁给用户。
4. 先重新核实当前状态，因为仓库可能在本文件之后继续变化。
5. 把历史失败当证据，不把历史路线当必须继承的方案。
6. 先解决当前第一阻塞点，再进入下一层。
7. 构建失败时读取完整日志，明确实际 fatal error。
8. 每次云端构建前避免可静态发现的配置错误。
9. 最终目标是可安装 Qwen3 4B APK，不要在中途分析阶段自行降低目标。
10. 成功后在 RastaCoder 自己的 GitHub Release 中交付大型 APK。

---

## 11. 当前恢复状态说明

在写入本文件之前，已经专门完成一次仓库善后：

- RastaCoder `main` 已恢复到错误 Qwen3 构建介入之前的 `f8f42df...`。
- 错误 Qwen3 构建分支已删除。
- 用于清理的临时分支已删除。
- 先前错误放入 `local-agent-plaza` 的 RastaCoder 构建分支和文件已经从活动仓库状态移除。
- 两个项目重新隔离。

本文件是清理完成后，**有意写入 RastaCoder 自己仓库**的正式交接文档。

以后更新项目进展时，可以更新本文件，或创建新的明确交接文档，但不得再跨仓库存放。

---

**截至 2026-08-25 的最终一句话：**

当前任务是从已经恢复干净、且源码本身已经包含 Qwen3 4B 注册信息的 RastaCoder 仓库继续开发，先用项目自己的官方构建基线解决现有 Flutter/Dart/依赖阻塞，再验证 MLC native runtime，最终在 RastaCoder 自己的 GitHub 中产出并交付一个可直接安装、可识别 Qwen3 4B 的 arm64-v8a Release APK；任何后续 Agent 都不得再把本项目和 `local-agent-plaza` 混在一起。
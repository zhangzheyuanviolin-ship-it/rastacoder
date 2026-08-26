// RASTACODER_V7_COMPLETE_SKILLS
class LocalToolSkill {
  final String id;
  final String category;
  final String title;
  final String description;
  final List<String> toolNames;
  final List<String> capabilities;

  const LocalToolSkill({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.toolNames,
    required this.capabilities,
  });
}

class LocalToolSkillCatalog {
  // The old v5/v6 invariant used only the Feb-13 Qwen3 known-good baseline.
  // Post-baseline upstream had already added image_compose + list_files, so
  // calling those 23 functions "all original tools" was incorrect.
  static const legacyCoreToolNames = <String>{
    'python_execute', 'ffmpeg_process', 'smart_crop', 'ocr_image',
    'read_pdf', 'create_pdf', 'read_file', 'write_file', 'file_info',
    'create_zip', 'convert_document', 'create_docx', 'read_docx',
    'read_pptx', 'read_xlsx', 'web_fetch', 'headless_browser',
    'download_media', 'modify_docx', 'modify_pptx', 'modify_xlsx',
    'google_calendar', 'gmail',
  };

  static const upstreamExtendedToolNames = <String>{
    'image_compose', 'list_files',
  };

  static const v7AddedToolNames = <String>{
    'file_manage', 'list_zip', 'extract_zip', 'pdf_manage',
    'create_pptx', 'create_xlsx',
  };

  static const allCanonicalToolNames = <String>{
    ...legacyCoreToolNames,
    ...upstreamExtendedToolNames,
    ...v7AddedToolNames,
  };

  static const all = <LocalToolSkill>[
    LocalToolSkill(
      id: 'text_files', category: '文件与文档', title: '文件与文本操作',
      description: '完整管理工作区文件、目录和文本内容。',
      toolNames: ['read_file', 'write_file', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['读取文本', '创建/写入文本', '文件信息', '列出文件与目录', '递归查找', '创建目录', '复制', '移动', '重命名', '删除文件/目录', '检查存在', '创建空文件'],
    ),
    LocalToolSkill(
      id: 'zip_archive', category: '文件与文档', title: 'ZIP 压缩与归档',
      description: '创建、查看和解压 ZIP，并管理归档相关文件。',
      toolNames: ['create_zip', 'list_zip', 'extract_zip', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['创建 ZIP', '压缩/仅存储模式', '查看归档目录', '安全解压', '覆盖控制', '列出工作区文件', '移动/重命名/删除归档'],
    ),
    LocalToolSkill(
      id: 'pdf_read', category: '文件与文档', title: 'PDF 阅读与页面管理',
      description: '读取 PDF 并执行常用页面级操作。',
      toolNames: ['read_pdf', 'pdf_manage', 'file_info', 'list_files'],
      capabilities: ['全文/指定页读取', '页数与文件信息', '合并 PDF', '拆分 PDF', '提取页面', '页面重排', '删除页面', '旋转页面'],
    ),
    LocalToolSkill(
      id: 'pdf_create', category: '文件与文档', title: 'PDF 创建与整理',
      description: '从文本/图片创建 PDF，并进行页面整理。',
      toolNames: ['create_pdf', 'pdf_manage', 'image_compose', 'file_info', 'list_files'],
      capabilities: ['文本创建 PDF', '图片嵌入 PDF', '合并', '拆分', '提取/重排/删除/旋转页面', '创建前处理图片'],
    ),
    LocalToolSkill(
      id: 'document_convert', category: '文件与文档', title: '文档格式转换',
      description: '在 TXT、DOCX、PDF、HTML 之间转换并检查源文件。',
      toolNames: ['convert_document', 'read_file', 'read_pdf', 'read_docx', 'file_info', 'list_files'],
      capabilities: ['TXT 转 DOCX/PDF/HTML', 'DOCX 转 TXT/PDF/HTML', 'PDF 转 TXT/DOCX/HTML', 'HTML 转 TXT/DOCX/PDF', '自动输出命名', '转换前读取检查'],
    ),
    LocalToolSkill(
      id: 'word', category: '文件与文档', title: 'Word 文档',
      description: '创建、读取、修改、转换和管理 DOCX。',
      toolNames: ['create_docx', 'read_docx', 'modify_docx', 'convert_document', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['新建 DOCX', '读取正文/表格', '替换文本', '添加段落', '修改表格单元格', 'DOCX 格式转换', '复制/移动/重命名/删除'],
    ),
    LocalToolSkill(
      id: 'powerpoint', category: '文件与文档', title: 'PowerPoint',
      description: '创建、读取、修改和管理 PPTX 演示文稿。',
      toolNames: ['create_pptx', 'read_pptx', 'modify_pptx', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['新建 PPTX', '读取幻灯片/备注/表格', '替换文本', '添加幻灯片', '更新形状文字', '设置备注', '复制/移动/重命名/删除'],
    ),
    LocalToolSkill(
      id: 'excel', category: '文件与文档', title: 'Excel',
      description: '创建、读取、修改和管理 XLSX 工作簿。',
      toolNames: ['create_xlsx', 'read_xlsx', 'modify_xlsx', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['新建 XLSX', '读取工作表/区域/公式', '设置单元格', '设置公式', '添加行', '添加/删除工作表', '复制/移动/重命名/删除文件'],
    ),
    LocalToolSkill(
      id: 'ocr', category: '图像与多媒体', title: 'OCR 文字识别',
      description: '发现、预处理并识别图片文字。',
      toolNames: ['ocr_image', 'image_compose', 'file_info', 'list_files'],
      capabilities: ['OCR 识别', '列出待识别图片', '裁剪/旋转/调整图片后识别', '图片尺寸/文件信息', '多图片逐一识别'],
    ),
    LocalToolSkill(
      id: 'image_processing', category: '图像与多媒体', title: '完整图片处理',
      description: '覆盖常用图片编辑、尺寸、格式和拼接处理。',
      toolNames: ['image_compose', 'smart_crop', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['横向/纵向拼接', '叠加', '尺寸放大/缩小', '分辨率调整', '格式转换', '裁剪', '亮度/对比度/饱和度/锐度/Gamma', '灰度', '模糊', '旋转', '翻转', '人脸智能裁剪'],
    ),
    LocalToolSkill(
      id: 'video_processing', category: '图像与多媒体', title: '完整视频处理',
      description: '结构化 FFmpeg 视频操作并保留高级 FFmpeg 入口。',
      toolNames: ['ffmpeg_process', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['裁剪时长', '画面裁剪', '缩放', '滤镜', '变速', '抽帧', '提取音轨', '格式/编码转换', '视频拼接', '视频+音频合并', '高级 custom FFmpeg'],
    ),
    LocalToolSkill(
      id: 'audio_processing', category: '图像与多媒体', title: '完整音频处理',
      description: '结构化 FFmpeg 音频编辑并保留高级 FFmpeg 入口。',
      toolNames: ['ffmpeg_process', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['音频裁剪', 'MP3/WAV/M4A/AAC/FLAC/OGG/Opus 转换', '音量/速度/滤镜', '音频拼接', '多音轨混音', '从视频提取音频', '高级 custom FFmpeg'],
    ),
    LocalToolSkill(
      id: 'media_download', category: '图像与多媒体', title: '媒体下载',
      description: '解析受支持平台的视频/音频资源并管理结果文件。',
      toolNames: ['download_media', 'file_info', 'list_files', 'file_manage'],
      capabilities: ['视频资源解析并实际下载', '纯音频资源解析并实际下载', '自动文件命名', '媒体元信息', '列出/管理下载结果'],
    ),
    LocalToolSkill(
      id: 'web_fetch', category: '网络', title: '网页读取',
      description: '读取网页文本、HTML、链接，并可保存结果。',
      toolNames: ['web_fetch', 'write_file', 'file_info', 'list_files'],
      capabilities: ['提取正文', '获取 HTML', '提取链接', '保存抓取结果', '查看已保存文件'],
    ),
    LocalToolSkill(
      id: 'dynamic_web', category: '网络', title: '动态网页',
      description: '加载 JavaScript 页面并按 CSS 选择器提取内容。',
      toolNames: ['headless_browser', 'web_fetch', 'write_file', 'file_info'],
      capabilities: ['JavaScript 渲染', '等待页面稳定', 'CSS 选择器提取', '普通抓取回退', '保存提取结果'],
    ),
    LocalToolSkill(
      id: 'basic_calculation', category: '计算与数据', title: '基础计算与 Python',
      description: '直接执行受控 Python 进行通用计算和文本/数据处理。',
      toolNames: ['python_execute', 'read_file', 'write_file', 'file_info'],
      capabilities: ['算术/公式', '统计', '文本处理', 'JSON/CSV', '自定义 Python 逻辑', '读取输入文件', '写出结果文件'],
    ),
    LocalToolSkill(
      id: 'scientific_calculation', category: '计算与数据', title: '科学计算与 Python',
      description: '使用 NumPy、statistics 等完成数值和科学计算。',
      toolNames: ['python_execute', 'read_file', 'write_file', 'file_info'],
      capabilities: ['NumPy 数值计算', '统计分析', '数组/矩阵', '算法', '自定义 Python', '文件输入输出'],
    ),
    LocalToolSkill(
      id: 'data_analysis', category: '计算与数据', title: '数据分析',
      description: '使用 Pandas/Python 分析数据并读写文本和 Excel。',
      toolNames: ['python_execute', 'read_file', 'write_file', 'read_xlsx', 'create_xlsx', 'file_info', 'list_files'],
      capabilities: ['Pandas DataFrame', 'CSV/文本分析', 'Excel 读取', 'Excel 结果导出', '筛选/分组/聚合', '描述统计', '自定义 Python 数据处理'],
    ),
    LocalToolSkill(
      id: 'charts', category: '计算与数据', title: '图表绘制',
      description: '使用 Matplotlib 生成图表，并可继续处理输出图片。',
      toolNames: ['python_execute', 'write_file', 'image_compose', 'file_info', 'list_files'],
      capabilities: ['折线/柱状/散点/饼图等 Matplotlib 图表', '自定义 Python 绘图', '自动 PNG 输出', '图像尺寸/格式后处理'],
    ),
    LocalToolSkill(
      id: 'gmail', category: 'Google', title: 'Gmail',
      description: '在当前只读 OAuth 权限范围内搜索、列出和读取邮件。',
      toolNames: ['gmail'],
      capabilities: ['按 Gmail 查询语法搜索', '列出邮件', '读取邮件正文/头信息', '只读权限保护'],
    ),
    LocalToolSkill(
      id: 'google_calendar', category: 'Google', title: 'Google 日历',
      description: '查询、创建和删除 Google Calendar 日程。',
      toolNames: ['google_calendar'],
      capabilities: ['今日/本周/日期范围查询', '创建日程', '更新日程', '删除日程', '标题/时间/描述/地点'],
    ),
  ];

  static Set<String> get allIds => all.map((skill) => skill.id).toSet();
  static Set<String> get coveredToolNames => all.expand((skill) => skill.toolNames).toSet();

  static bool get hasCompleteCoverage {
    final covered = coveredToolNames;
    return covered.length == allCanonicalToolNames.length &&
        allCanonicalToolNames.every(covered.contains);
  }

  static List<String> get categories {
    final result = <String>[];
    for (final skill in all) {
      if (!result.contains(skill.category)) result.add(skill.category);
    }
    return result;
  }

  static List<LocalToolSkill> inCategory(String category) =>
      all.where((skill) => skill.category == category).toList(growable: false);
}

// RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
class LocalToolSkill {
  final String id;
  final String category;
  final String title;
  final String description;
  final List<String> toolNames;

  const LocalToolSkill({
    required this.id,
    required this.category,
    required this.title,
    required this.description,
    required this.toolNames,
  });
}

class LocalToolSkillCatalog {
  static const originalToolNames = <String>{
    'python_execute',
    'ffmpeg_process',
    'smart_crop',
    'ocr_image',
    'read_pdf',
    'create_pdf',
    'read_file',
    'write_file',
    'file_info',
    'create_zip',
    'convert_document',
    'create_docx',
    'read_docx',
    'read_pptx',
    'read_xlsx',
    'web_fetch',
    'headless_browser',
    'download_media',
    'modify_docx',
    'modify_pptx',
    'modify_xlsx',
    'google_calendar',
    'gmail',
  };

  static const all = <LocalToolSkill>[
    LocalToolSkill(
      id: 'text_files', category: '文件与文档', title: '文本文件',
      description: '读取、创建文本文件并查看文件信息。',
      toolNames: ['read_file', 'write_file', 'file_info'],
    ),
    LocalToolSkill(
      id: 'zip_archive', category: '文件与文档', title: 'ZIP 压缩与归档',
      description: '把一个或多个文件打包为 ZIP。',
      toolNames: ['create_zip', 'file_info'],
    ),
    LocalToolSkill(
      id: 'pdf_read', category: '文件与文档', title: 'PDF 阅读',
      description: '提取 PDF 文本并检查文件信息。',
      toolNames: ['read_pdf', 'file_info'],
    ),
    LocalToolSkill(
      id: 'pdf_create', category: '文件与文档', title: 'PDF 创建',
      description: '从文字或图片创建 PDF。',
      toolNames: ['create_pdf'],
    ),
    LocalToolSkill(
      id: 'document_convert', category: '文件与文档', title: '文档格式转换',
      description: '在 TXT、DOCX、PDF、HTML 之间进行文本型转换。',
      toolNames: ['convert_document'],
    ),
    LocalToolSkill(
      id: 'word', category: '文件与文档', title: 'Word 文档',
      description: '创建、读取和修改 DOCX 文档。',
      toolNames: ['create_docx', 'read_docx', 'modify_docx'],
    ),
    LocalToolSkill(
      id: 'powerpoint', category: '文件与文档', title: 'PowerPoint',
      description: '读取和修改 PPTX 演示文稿。',
      toolNames: ['read_pptx', 'modify_pptx'],
    ),
    LocalToolSkill(
      id: 'excel', category: '文件与文档', title: 'Excel',
      description: '读取和修改 XLSX 工作簿。',
      toolNames: ['read_xlsx', 'modify_xlsx'],
    ),
    LocalToolSkill(
      id: 'ocr', category: '图像与多媒体', title: 'OCR 文字识别',
      description: '从图片中识别并提取文字。',
      toolNames: ['ocr_image'],
    ),
    LocalToolSkill(
      id: 'image_processing', category: '图像与多媒体', title: '图片智能处理',
      description: '基于人脸检测执行智能裁剪。',
      toolNames: ['smart_crop'],
    ),
    LocalToolSkill(
      id: 'video_processing', category: '图像与多媒体', title: '视频处理',
      description: '裁剪、缩放、滤镜、抽帧、格式转换及视频音轨处理。',
      toolNames: ['ffmpeg_process'],
    ),
    LocalToolSkill(
      id: 'audio_processing', category: '图像与多媒体', title: '音频处理',
      description: '音频裁剪、音量/速度处理、提取与格式转换。',
      toolNames: ['ffmpeg_process'],
    ),
    LocalToolSkill(
      id: 'media_download', category: '图像与多媒体', title: '媒体下载',
      description: '从支持的平台解析并下载视频或音频。',
      toolNames: ['download_media'],
    ),
    LocalToolSkill(
      id: 'web_fetch', category: '网络', title: '网页读取',
      description: '读取普通网页的文本、HTML 或链接。',
      toolNames: ['web_fetch'],
    ),
    LocalToolSkill(
      id: 'dynamic_web', category: '网络', title: '动态网页',
      description: '加载需要 JavaScript 渲染的网页。',
      toolNames: ['headless_browser'],
    ),
    LocalToolSkill(
      id: 'basic_calculation', category: '计算与数据', title: '基础计算',
      description: '使用 Python 完成数学、统计、文本和结构化数据计算。',
      toolNames: ['python_execute'],
    ),
    LocalToolSkill(
      id: 'scientific_calculation', category: '计算与数据', title: '科学计算',
      description: '使用 NumPy 等模块执行数值和科学计算。',
      toolNames: ['python_execute'],
    ),
    LocalToolSkill(
      id: 'data_analysis', category: '计算与数据', title: '数据分析',
      description: '使用 Pandas 处理表格、CSV、统计与分组分析。',
      toolNames: ['python_execute'],
    ),
    LocalToolSkill(
      id: 'charts', category: '计算与数据', title: '图表绘制',
      description: '使用 Matplotlib 生成图表文件。',
      toolNames: ['python_execute'],
    ),
    LocalToolSkill(
      id: 'gmail', category: 'Google', title: 'Gmail',
      description: '列出和读取 Gmail 邮件；保持只读。',
      toolNames: ['gmail'],
    ),
    LocalToolSkill(
      id: 'google_calendar', category: 'Google', title: 'Google 日历',
      description: '查询、创建和删除 Google Calendar 日程。',
      toolNames: ['google_calendar'],
    ),
  ];

  static Set<String> get allIds => all.map((skill) => skill.id).toSet();

  static Set<String> get coveredToolNames =>
      all.expand((skill) => skill.toolNames).toSet();

  static bool get hasCompleteCoverage {
    final covered = coveredToolNames;
    return covered.length == originalToolNames.length &&
        originalToolNames.every(covered.contains);
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

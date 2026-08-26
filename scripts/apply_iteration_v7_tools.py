#!/usr/bin/env python3
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"v7 patch anchor missing: {label}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Python tool registry/schema
# ---------------------------------------------------------------------------
p = Path('python/navixmind/tools/__init__.py')
text = p.read_text()
text = replace_once(
    text,
    'from .code_executor import python_execute\n',
    'from .code_executor import python_execute\nfrom .extended_tools import (\n'
    '    list_files, file_manage, list_zip, extract_zip, pdf_manage,\n'
    '    create_pptx, create_xlsx, image_compose,\n'
    ')\n',
    'extended tool imports',
)

v7_schemas = r'''

# RASTACODER_V7_COMPLETE_SKILLS
# Restore post-Qwen3 upstream tools which were omitted by the old 23-tool
# baseline and add structured scene-complete primitives requested for v7.
TOOLS_SCHEMA.extend([
    {
        "name": "list_files",
        "description": "List/discover files and directories. Supports app output and common Android folders, optional recursive traversal and filename pattern filtering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "enum": ["output", "downloads", "documents", "pictures", "screenshots", "camera"], "default": "output"},
                "path": {"type": "string", "description": "Optional explicit accessible directory path"},
                "recursive": {"type": "boolean", "default": False},
                "pattern": {"type": "string", "description": "Optional glob such as *.txt"},
                "include_directories": {"type": "boolean", "default": True},
            },
            "required": [],
        },
    },
    {
        "name": "file_manage",
        "description": "Manage files/directories: list, mkdir, copy, move, rename, delete, touch, exists. Use structured paths; no shell commands are needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "mkdir", "copy", "move", "rename", "delete", "touch", "exists"]},
                "path": {"type": "string"},
                "source_path": {"type": "string"},
                "destination_path": {"type": "string"},
                "recursive": {"type": "boolean", "default": False},
                "overwrite": {"type": "boolean", "default": False},
            },
            "required": ["action"],
        },
    },
    {
        "name": "list_zip",
        "description": "List files and metadata inside a ZIP archive without extracting it.",
        "input_schema": {
            "type": "object",
            "properties": {"zip_path": {"type": "string"}},
            "required": ["zip_path"],
        },
    },
    {
        "name": "extract_zip",
        "description": "Safely extract a ZIP archive into a writable directory. Rejects path traversal entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zip_path": {"type": "string"},
                "output_dir": {"type": "string", "description": "Optional folder name/path; generated automatically when omitted"},
                "overwrite": {"type": "boolean", "default": False},
            },
            "required": ["zip_path"],
        },
    },
    {
        "name": "pdf_manage",
        "description": "Manage PDF pages: merge PDFs, split into individual pages, extract/reorder/delete pages, or rotate selected pages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["merge", "split", "extract_pages", "reorder", "delete_pages", "rotate"]},
                "input_path": {"type": "string"},
                "input_paths": {"type": "array", "items": {"type": "string"}},
                "output_path": {"type": "string"},
                "pages": {"description": "1-based pages, e.g. '1-3,5' or [3,1,2] for reorder"},
                "rotation": {"type": "integer", "default": 90},
            },
            "required": ["action"],
        },
    },
    {
        "name": "create_pptx",
        "description": "Create a PowerPoint PPTX from structured slides with titles, content/bullets and optional speaker notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string"},
                "title": {"type": "string"},
                "slides": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["output_path"],
        },
    },
    {
        "name": "create_xlsx",
        "description": "Create an Excel XLSX workbook from structured sheets and rows.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string"},
                "sheets": {"type": "array", "items": {"type": "object"}, "description": "[{name, rows:[[...], ...]}]"},
            },
            "required": ["output_path"],
        },
    },
    {
        "name": "image_compose",
        "description": "Full image manipulation: horizontal/vertical concat, overlay, resize/upscale/downscale, color adjustment, crop, grayscale, blur, rotate, flip and format conversion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_paths": {"type": "array", "items": {"type": "string"}},
                "output_path": {"type": "string"},
                "operation": {"type": "string", "enum": ["concat_horizontal", "concat_vertical", "overlay", "resize", "adjust", "crop", "grayscale", "blur", "rotate", "flip", "convert"]},
                "params": {"type": "object", "description": "resize {width,height}; crop {x,y,width,height}; adjust {brightness,contrast,saturation,sharpness,gamma}; rotate {degrees}; flip {direction}; convert {format,quality}."},
            },
            "required": ["input_paths", "output_path", "operation"],
        },
    },
])
'''
text = replace_once(
    text,
    '\n\n# Compact tool schemas for offline (on-device) models with small context windows.\n',
    v7_schemas + '\n\n# Compact tool schemas for offline (on-device) models with small context windows.\n',
    'v7 schema insertion',
)

v7_offline = r'''

# RASTACODER_V7_COMPLETE_SKILLS
# Every structured v7 utility is available to the local model when its Skill is
# enabled. Keep the schema gated by Skills rather than dumping all tools into
# every request.
_V7_LOCAL_TOOL_NAMES = {
    "list_files", "file_manage", "list_zip", "extract_zip", "pdf_manage",
    "create_pptx", "create_xlsx", "image_compose",
}
_existing_offline_names = {t["name"] for t in OFFLINE_TOOLS_SCHEMA}
OFFLINE_TOOLS_SCHEMA.extend(
    t for t in TOOLS_SCHEMA
    if t["name"] in _V7_LOCAL_TOOL_NAMES and t["name"] not in _existing_offline_names
)

# The native executor already supports raw/custom FFmpeg. V6 accidentally hid
# that escape hatch from the compact local schema. V7 also adds structured
# multi-input operations so common concat/mix tasks do not require raw syntax.
for _schema_list in (TOOLS_SCHEMA, OFFLINE_TOOLS_SCHEMA):
    for _tool in _schema_list:
        if _tool.get("name") != "ffmpeg_process":
            continue
        _props = _tool["input_schema"]["properties"]
        _props["input_paths"] = {
            "type": "array", "items": {"type": "string"},
            "description": "Multiple input media files for concat, mix_audio or merge_av"
        }
        _op = _props["operation"]
        _op["enum"] = [
            "trim", "crop", "resize", "filter", "custom", "extract_audio",
            "extract_frame", "convert", "concat", "mix_audio", "merge_av"
        ]
        _op["description"] = "Structured media operation; custom is the advanced raw FFmpeg escape hatch"
        _props["params"]["description"] = (
            "trim {start,end/duration}; crop {width,height,x,y}; resize {width,height}; "
            "filter {vf,af}; custom {args}; extract_audio {format,bitrate}; "
            "extract_frame {timestamp}; convert {codec,quality}; concat {media_type:audio|video}; "
            "mix_audio {duration}; merge_av uses first input as video and second as audio."
        )
        # input_path is operation-dependent now; executor performs the precise check.
        _tool["input_schema"]["required"] = ["output_path", "operation"]
'''
text = replace_once(
    text,
    '\n\n# Local inference and tool locality are independent. Expose these app-side\n',
    v7_offline + '\n\n# Local inference and tool locality are independent. Expose these app-side\n',
    'v7 offline schema insertion',
)

start = text.index('LOCAL_SKILLS = {')
end = text.index('\n\nALL_LOCAL_SKILL_IDS =', start)
new_skills = '''LOCAL_SKILLS = {
    "text_files": {"tools": ("read_file", "write_file", "file_info", "list_files", "file_manage")},
    "zip_archive": {"tools": ("create_zip", "list_zip", "extract_zip", "file_info", "list_files", "file_manage")},
    "pdf_read": {"tools": ("read_pdf", "pdf_manage", "file_info", "list_files")},
    "pdf_create": {"tools": ("create_pdf", "pdf_manage", "image_compose", "file_info", "list_files")},
    "document_convert": {"tools": ("convert_document", "read_file", "read_pdf", "read_docx", "file_info", "list_files")},
    "word": {"tools": ("create_docx", "read_docx", "modify_docx", "convert_document", "file_info", "list_files", "file_manage")},
    "powerpoint": {"tools": ("create_pptx", "read_pptx", "modify_pptx", "file_info", "list_files", "file_manage")},
    "excel": {"tools": ("create_xlsx", "read_xlsx", "modify_xlsx", "file_info", "list_files", "file_manage")},
    "ocr": {"tools": ("ocr_image", "image_compose", "file_info", "list_files")},
    "image_processing": {"tools": ("image_compose", "smart_crop", "file_info", "list_files", "file_manage")},
    "video_processing": {"tools": ("ffmpeg_process", "file_info", "list_files", "file_manage")},
    "audio_processing": {"tools": ("ffmpeg_process", "file_info", "list_files", "file_manage")},
    "media_download": {"tools": ("download_media", "file_info", "list_files", "file_manage")},
    "web_fetch": {"tools": ("web_fetch", "write_file", "file_info", "list_files")},
    "dynamic_web": {"tools": ("headless_browser", "web_fetch", "write_file", "file_info")},
    "basic_calculation": {"tools": ("python_execute", "read_file", "write_file", "file_info")},
    "scientific_calculation": {"tools": ("python_execute", "read_file", "write_file", "file_info")},
    "data_analysis": {"tools": ("python_execute", "read_file", "write_file", "read_xlsx", "create_xlsx", "file_info", "list_files")},
    "charts": {"tools": ("python_execute", "write_file", "image_compose", "file_info", "list_files")},
    "gmail": {"tools": ("gmail",)},
    "google_calendar": {"tools": ("google_calendar",)},
}'''
text = text[:start] + new_skills + text[end:]

start = text.index('LOCAL_TOOL_PROMPT_HINTS = {')
end = text.index('\n\n\ndef _offline_tool_names()', start)
new_hints = '''LOCAL_TOOL_PROMPT_HINTS = {
    "read_file": "read_file(file_path)",
    "write_file": "write_file(output_path, content)",
    "file_info": "file_info(file_path)",
    "list_files": "list_files(directory?, path?, recursive?, pattern?, include_directories?)",
    "file_manage": "file_manage(action, path?, source_path?, destination_path?, recursive?, overwrite?) ; action=list|mkdir|copy|move|rename|delete|touch|exists",
    "create_zip": "create_zip(output_path, file_paths, compression?)",
    "list_zip": "list_zip(zip_path)",
    "extract_zip": "extract_zip(zip_path, output_dir?, overwrite?)",
    "read_pdf": "read_pdf(pdf_path, pages?)",
    "create_pdf": "create_pdf(output_path, content?, title?, image_paths?)",
    "pdf_manage": "pdf_manage(action, input_path?, input_paths?, output_path?, pages?, rotation?) ; action=merge|split|extract_pages|reorder|delete_pages|rotate",
    "convert_document": "convert_document(input_path, output_format, output_path?) ; output_format=pdf|html|txt|docx",
    "create_docx": "create_docx(output_path, content, title?)",
    "read_docx": "read_docx(docx_path, extract?)",
    "modify_docx": "modify_docx(input_path, output_path, operations)",
    "create_pptx": "create_pptx(output_path, title?, slides?)",
    "read_pptx": "read_pptx(pptx_path, extract?)",
    "modify_pptx": "modify_pptx(input_path, output_path, operations)",
    "create_xlsx": "create_xlsx(output_path, sheets?)",
    "read_xlsx": "read_xlsx(xlsx_path, sheet?, range?, extract?)",
    "modify_xlsx": "modify_xlsx(input_path, output_path, operations)",
    "ocr_image": "ocr_image(image_path)",
    "image_compose": "image_compose(input_paths, output_path, operation, params?) ; operation=concat_horizontal|concat_vertical|overlay|resize|adjust|crop|grayscale|blur|rotate|flip|convert",
    "smart_crop": "smart_crop(input_path, output_path, aspect_ratio?)",
    "ffmpeg_process": "ffmpeg_process(input_path?, input_paths?, output_path, operation, params?) ; operation=trim|crop|resize|filter|custom|extract_audio|extract_frame|convert|concat|mix_audio|merge_av",
    "download_media": "download_media(url, format?)",
    "web_fetch": "web_fetch(url, extract_mode?)",
    "headless_browser": "headless_browser(url, wait_seconds?, extract_selector?)",
    "python_execute": "python_execute(code, file_paths?)",
    "gmail": "gmail(action, query?, message_id?) ; action=list|read",
    "google_calendar": "google_calendar(action, date_range?, event?, event_id?) ; action=list|create|delete",
}'''
text = text[:start] + new_hints + text[end:]

# Tool execution map.
anchor = '        "write_file": write_file,\n'
addition = (
    '        "write_file": write_file,\n'
    '        "list_files": list_files,\n'
    '        "file_manage": file_manage,\n'
    '        "list_zip": list_zip,\n'
    '        "extract_zip": extract_zip,\n'
    '        "pdf_manage": pdf_manage,\n'
    '        "create_pptx": create_pptx,\n'
    '        "create_xlsx": create_xlsx,\n'
    '        "image_compose": image_compose,\n'
)
text = replace_once(text, anchor, addition, 'v7 tool map')

# Resolve all multi-file schemas, including FFmpeg and PDF/image operations.
text = replace_once(
    text,
    "    array_path_keys = ['image_paths', 'file_paths']\n",
    "    array_path_keys = ['image_paths', 'file_paths', 'input_paths']\n",
    'multi-path resolution',
)

# Inject the app output directory into structured filesystem/PDF/archive tools.
text = replace_once(
    text,
    '    # Pass output_dir to python_execute for file writing and plot auto-save\n'
    '    if tool_name == "python_execute" and output_dir:\n'
    '        args["output_dir"] = output_dir\n',
    '    # Pass output_dir to Python tools which need a stable workspace root.\n'
    '    if tool_name == "python_execute" and output_dir:\n'
    '        args["output_dir"] = output_dir\n'
    '    if tool_name in {"list_files", "file_manage", "extract_zip", "pdf_manage"} and output_dir:\n'
    '        args["_output_dir"] = output_dir\n',
    'workspace context injection',
)

# Static cloud prompt: describe the newly available structured tools as well.
text = replace_once(
    text,
    '- **write_file** — Write text content to a file (saved to device, available for download/sharing)\n',
    '- **write_file** — Write text content to a file (saved to device, available for download/sharing)\n'
    '- **list_files / file_manage** — Discover, create folders, copy/move/rename/delete files and directories\n'
    '- **list_zip / extract_zip** — Inspect and extract ZIP archives\n'
    '- **pdf_manage** — Merge, split, extract/reorder/delete/rotate PDF pages\n'
    '- **image_compose** — Resize, convert, concatenate, overlay, crop, adjust, rotate/flip and filter images\n'
    '- **create_pptx / create_xlsx** — Create PowerPoint presentations and Excel workbooks\n',
    'cloud prompt extension',
)
p.write_text(text)


# ---------------------------------------------------------------------------
# Flutter Skill catalogue: 21 domains remain manual, but each domain exposes a
# complete scene-level capability set. The invariant is now 31 canonical tools,
# not the stale 23-tool checkpoint.
# ---------------------------------------------------------------------------
tool_skill = r'''// RASTACODER_V7_COMPLETE_SKILLS
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
      capabilities: ['视频资源解析', '纯音频资源解析', '媒体元信息', '列出/管理下载结果'],
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
      capabilities: ['今日/本周/日期范围查询', '创建日程', '删除日程', '标题/时间/描述/地点'],
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
'''
Path('lib/core/models/tool_skill.dart').write_text(tool_skill)

# Skill screen: report the truthful 31-tool canonical surface and announce
# user-facing capabilities, not just implementation function names.
p = Path('lib/features/settings/tool_skills_screen.dart')
ui = p.read_text()
ui = ui.replace(
    "label: '当前启用 ${_enabled.length} 个技能，共 ${LocalToolSkillCatalog.all.length} 个。原始工具覆盖 $covered 个，共 ${LocalToolSkillCatalog.originalToolNames.length} 个。',",
    "label: '当前启用 ${_enabled.length} 个技能，共 ${LocalToolSkillCatalog.all.length} 个。规范工具覆盖 $covered 个，共 ${LocalToolSkillCatalog.allCanonicalToolNames.length} 个。',",
)
ui = ui.replace(
    "'当前启用 ${_enabled.length}/${LocalToolSkillCatalog.all.length} 个技能；原始工具覆盖 $covered/${LocalToolSkillCatalog.originalToolNames.length}。'\n                    '${LocalToolSkillCatalog.hasCompleteCoverage ? ' 全部原始工具均已归类。' : ' 工具覆盖异常。'}',",
    "'当前启用 ${_enabled.length}/${LocalToolSkillCatalog.all.length} 个技能；规范工具覆盖 $covered/${LocalToolSkillCatalog.allCanonicalToolNames.length}。'\n                    '${LocalToolSkillCatalog.hasCompleteCoverage ? ' 当前完整工具面均已归类。' : ' 工具覆盖异常。'}',",
)
ui = ui.replace(
    "label: '${skill.title}，${_enabled.contains(skill.id) ? '已开启' : '已关闭'}。${skill.description}',",
    "label: '${skill.title}，${_enabled.contains(skill.id) ? '已开启' : '已关闭'}。${skill.description}。支持：${skill.capabilities.join('、')}',",
)
ui = ui.replace(
    "subtitle: Text('${skill.description}\\n底层工具：${skill.toolNames.join(', ')}'),",
    "subtitle: Text('${skill.description}\\n支持动作：${skill.capabilities.join('、')}\\n底层工具：${skill.toolNames.join(', ')}'),",
)
p.write_text(ui)

p = Path('lib/features/settings/settings_screen.dart')
settings = p.read_text()
settings = settings.replace(
    "subtitle: '管理新会话默认开启的 21 个技能；完整覆盖原有 23 个本地工具',",
    "subtitle: '管理 21 个手动技能；完整覆盖上游扩展与 V7 补全后的 31 个规范工具，并逐项显示场景动作',",
)
p.write_text(settings)

print('Applied RastaCoder v7 complete-skill tool/schema/catalog patch')

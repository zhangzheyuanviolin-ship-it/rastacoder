"""
Tools - Native tool implementations for the agent

This module provides tool definitions and execution logic.
"""

from typing import Any, Dict

from .web import web_fetch, headless_browser
from .documents import (
    read_pdf, create_pdf, create_docx, convert_document, create_zip, read_file, write_file,
    read_docx, modify_docx, read_pptx, modify_pptx, read_xlsx, modify_xlsx,
)
from .media import download_media
from .google_api import google_calendar, gmail
from .code_executor import python_execute

from ..bridge import ToolError, get_bridge
from .compat import normalize_tool_call

# RASTACODER_V4_TOOL_CONTRACT


# Tool schema for Claude
TOOLS_SCHEMA = [
    {
        "name": "web_fetch",
        "description": "Fetch a webpage and extract its text content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "extract_mode": {
                    "type": "string",
                    "enum": ["text", "html", "links"],
                    "description": "What to extract from the page"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "headless_browser",
        "description": "Load a JavaScript-heavy page in a headless browser and extract content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to load"},
                "wait_seconds": {
                    "type": "integer",
                    "default": 5,
                    "description": "Seconds to wait for JS to render"
                },
                "extract_selector": {
                    "type": "string",
                    "description": "CSS selector to extract, or empty for full page"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "read_pdf",
        "description": "Extract text content from a PDF file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Path to PDF file"},
                "pages": {
                    "type": "string",
                    "description": "Page range, e.g., '1-5' or 'all'"
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "create_pdf",
        "description": "Create a PDF document from text and/or images. Can embed images (JPG, PNG) directly into the PDF.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Text content for the PDF (optional if images provided)"},
                "title": {"type": "string", "description": "Document title"},
                "output_path": {"type": "string", "description": "Where to save the PDF"},
                "image_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image file paths to embed in the PDF"
                }
            },
            "required": ["output_path"]
        }
    },
    {
        "name": "convert_document",
        "description": "Text-oriented conversion between TXT, DOCX, PDF, and HTML. Complex layout may be simplified.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to .txt, .docx, .pdf, .html, or .htm input"},
                "output_format": {"type": "string", "enum": ["pdf", "html", "txt", "docx"], "description": "Target format"},
                "output_path": {"type": "string", "description": "Optional explicit output path"}
            },
            "required": ["input_path", "output_format"]
        }
    },
    {
        "name": "create_docx",
        "description": "Create a new DOCX Word document from text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Where to save the .docx file"},
                "content": {"type": "string", "description": "Document text"},
                "title": {"type": "string", "description": "Optional document title"}
            },
            "required": ["output_path", "content"]
        }
    },
    {
        "name": "read_docx",
        "description": "Extract text, tables, and metadata from a DOCX file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "docx_path": {"type": "string", "description": "Path to the DOCX file"},
                "extract": {
                    "type": "string",
                    "enum": ["text", "tables", "all"],
                    "default": "all",
                    "description": "What to extract"
                }
            },
            "required": ["docx_path"]
        }
    },
    {
        "name": "modify_docx",
        "description": "Modify an existing DOCX file. Can replace text, add paragraphs, update table cells, and save back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the source DOCX"},
                "output_path": {"type": "string", "description": "Where to save the modified DOCX"},
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["replace_text", "add_paragraph", "update_table_cell"]},
                            "params": {"type": "object"}
                        }
                    },
                    "description": "replace_text: {old, new}. add_paragraph: {text, style?}. update_table_cell: {table, row, col, text}."
                }
            },
            "required": ["input_path", "output_path", "operations"]
        }
    },
    {
        "name": "read_pptx",
        "description": "Extract text, slide content, speaker notes, and metadata from a PPTX file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pptx_path": {"type": "string", "description": "Path to the PPTX file"},
                "extract": {
                    "type": "string",
                    "enum": ["text", "slides", "notes", "all"],
                    "default": "all",
                    "description": "What to extract"
                }
            },
            "required": ["pptx_path"]
        }
    },
    {
        "name": "modify_pptx",
        "description": "Modify an existing PPTX file. Can replace text across slides, add slides, update shape text, set speaker notes, and save back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the source PPTX"},
                "output_path": {"type": "string", "description": "Where to save the modified PPTX"},
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["replace_text", "add_slide", "update_slide_text", "set_notes"]},
                            "params": {"type": "object"}
                        }
                    },
                    "description": "replace_text: {old, new}. add_slide: {layout_index?, title?, content?}. update_slide_text: {slide, shape_name, text}. set_notes: {slide, text}."
                }
            },
            "required": ["input_path", "output_path", "operations"]
        }
    },
    {
        "name": "read_xlsx",
        "description": "Extract cell data, sheet names, and formulas from an XLSX file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "xlsx_path": {"type": "string", "description": "Path to the XLSX file"},
                "sheet": {"type": "string", "description": "Sheet name or index. Omit for all sheets."},
                "range": {"type": "string", "description": "Cell range, e.g., 'A1:D10'. Omit for all data."},
                "extract": {
                    "type": "string",
                    "enum": ["values", "formulas", "all"],
                    "default": "values",
                    "description": "What to extract"
                }
            },
            "required": ["xlsx_path"]
        }
    },
    {
        "name": "modify_xlsx",
        "description": "Modify an existing XLSX file. Can update cells, set formulas, add rows/sheets, delete sheets, and save back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to the source XLSX"},
                "output_path": {"type": "string", "description": "Where to save the modified XLSX"},
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["set_cell", "set_formula", "add_row", "add_sheet", "delete_sheet"]},
                            "params": {"type": "object"}
                        }
                    },
                    "description": "set_cell: {sheet?, cell, value}. set_formula: {sheet?, cell, formula}. add_row: {sheet?, values: []}. add_sheet: {name}. delete_sheet: {name}."
                }
            },
            "required": ["input_path", "output_path", "operations"]
        }
    },
    {
        "name": "create_zip",
        "description": "Create a ZIP archive from one or more files. Supports deflated (compressed) and stored (no compression) modes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Where to save the ZIP file"},
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths to include in the archive"
                },
                "compression": {
                    "type": "string",
                    "enum": ["deflated", "stored"],
                    "default": "deflated",
                    "description": "Compression method: 'deflated' (smaller) or 'stored' (no compression, faster)"
                }
            },
            "required": ["output_path", "file_paths"]
        }
    },
    {
        "name": "download_media",
        "description": "Download video/audio from supported platforms (TikTok, Instagram, etc.). NOT YouTube.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL of the media"},
                "format": {
                    "type": "string",
                    "enum": ["video", "audio"],
                    "description": "Whether to download video or audio only"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "ffmpeg_process",
        "description": "Process video/audio with FFmpeg. Operations: trim, crop, resize, filter (brightness/contrast/etc), custom (raw FFmpeg args for complex ops), extract_audio, extract_frame, convert.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to input file"},
                "output_path": {"type": "string", "description": "Path for output file"},
                "operation": {
                    "type": "string",
                    "enum": ["trim", "crop", "resize", "filter", "custom", "extract_audio", "extract_frame", "convert"],
                    "description": "Operation to perform"
                },
                "params": {
                    "type": "object",
                    "description": "Operation params. trim: {start, end} or {start, duration}. crop: {width, height, x, y}. resize: {width, height}. filter: {vf} for video filters (e.g. 'eq=brightness=0.3'), {af} for audio filters. custom: {args} raw FFmpeg arguments between -i input and output (for complex multi-filter chains, e.g. \"-vf select='not(mod(floor(t)\\,2))',setpts=N/FRAME_RATE/TB -af aselect='not(mod(floor(t)\\,2))',asetpts=N/SR/TB -c:v libx264 -crf 23 -c:a aac\"). extract_audio: {format, bitrate}. extract_frame: {timestamp}. convert: {codec, quality (int 0-51)}."
                }
            },
            "required": ["input_path", "output_path", "operation"]
        }
    },
    {
        "name": "ocr_image",
        "description": "Extract text from an image using OCR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image file"}
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "smart_crop",
        "description": "Smart crop video/image to focus on faces. ONLY use for simple face-centered cropping. For TikTok/Reels adaptation with effects, transitions, or custom crop positions, use ffmpeg_process instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Path to input video or image"},
                "output_path": {"type": "string", "description": "Path for output file"},
                "aspect_ratio": {
                    "type": "string",
                    "default": "9:16",
                    "description": "Target aspect ratio (e.g., '9:16' for vertical, '16:9' for horizontal)"
                }
            },
            "required": ["input_path", "output_path"]
        }
    },
    {
        "name": "google_calendar",
        "description": "Query or create Google Calendar events. Requires user authorization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "create", "delete"],
                    "description": "Action to perform"
                },
                "date_range": {
                    "type": "string",
                    "description": "For list: 'today', 'this_week', or ISO date range"
                },
                "event": {
                    "type": "object",
                    "description": "For create: {title, start, end, description, location?}"
                },
                "event_id": {"type": "string", "description": "For delete: Calendar event ID"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "gmail",
        "description": "Read Gmail messages (read-only). Requires user authorization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "read"],
                    "description": "Action to perform"
                },
                "query": {
                    "type": "string",
                    "description": "For list: Gmail search query"
                },
                "message_id": {
                    "type": "string",
                    "description": "For read: message ID"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_info",
        "description": "Get file metadata (size, name, extension). Use this instead of trying os.path in python_execute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "read_file",
        "description": "Read text content from a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write text content to a file. The created file will be available for download/sharing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Filename or path for the output file"},
                "content": {"type": "string", "description": "Text content to write to the file"}
            },
            "required": ["output_path", "content"]
        }
    },
    {
        "name": "python_execute",
        "description": """Execute Python code in a secure sandbox. Use this for:
- Data processing and analysis (pandas DataFrames, CSV, groupby, etc.)
- Mathematical calculations and algorithms
- Statistical analysis (numpy, statistics)
- Charts and plots (matplotlib — figures are auto-saved as PNG and returned)
- Text manipulation and parsing
- JSON/CSV data processing
- Any computation that requires custom logic

Available modules: math, numpy, pandas, matplotlib, json, re, datetime, collections, itertools, statistics, csv, base64, hashlib.
FORBIDDEN: subprocess, os, sys, shutil, socket, http, urllib, pathlib, glob, signal, ctypes, requests, multiprocessing, threading.
To run FFmpeg/FFprobe, use the ffmpeg_process tool instead. To access files, use dedicated tools (read_pdf, ocr_image, etc.).

For plots, use matplotlib — figures are auto-saved as PNG files and returned. An OUTPUT_DIR variable is available for saving files explicitly (e.g., df.to_csv(OUTPUT_DIR + '/data.csv')).

The code runs with a 30-second timeout. Print statements and the last expression's value are captured and returned.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Can be multi-line. Use print() for output."
                },
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths the code is allowed to read (must be files provided by user)"
                }
            },
            "required": ["code"]
        }
    }
]


# Compact tool schemas for offline (on-device) models with small context windows.
# Includes all tools that work offline. Descriptions kept minimal to conserve tokens.
OFFLINE_TOOLS_SCHEMA = [
    {
        "name": "python_execute",
        "description": "Run Python code. Available: math, numpy, pandas, matplotlib, json, re, datetime, collections, itertools, statistics, csv, base64, hashlib. Use print() for output. FORBIDDEN: os, sys, subprocess.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to run"},
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files the code can read"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "ffmpeg_process",
        "description": "Process video/audio with FFmpeg. Operations: trim, crop, resize, filter, extract_audio, extract_frame, convert. Use this for ALL video/audio processing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Input file path"},
                "output_path": {"type": "string", "description": "Output file path"},
                "operation": {
                    "type": "string",
                    "enum": ["trim", "crop", "resize", "filter", "extract_audio", "extract_frame", "convert"],
                    "description": "Operation to perform"
                },
                "params": {
                    "type": "object",
                    "description": "trim: {start, end/duration}. crop: {width, height, x, y}. resize: {width, height}. filter: {vf, af}. extract_audio: {format, bitrate}. extract_frame: {timestamp}. convert: {codec, quality}."
                }
            },
            "required": ["input_path", "output_path", "operation"]
        }
    },
    {
        "name": "smart_crop",
        "description": "Smart crop video/image to focus on faces. For simple face-centered cropping only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Input file path"},
                "output_path": {"type": "string", "description": "Output file path"},
                "aspect_ratio": {"type": "string", "default": "9:16", "description": "Target aspect ratio"}
            },
            "required": ["input_path", "output_path"]
        }
    },
    {
        "name": "ocr_image",
        "description": "Extract text from an image using OCR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Path to image"}
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "read_pdf",
        "description": "Extract text from a PDF file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Path to PDF"},
                "pages": {"type": "string", "description": "Page range, e.g. '1-5' or 'all'"}
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "create_pdf",
        "description": "Create a PDF from text and/or images.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Where to save PDF"},
                "content": {"type": "string", "description": "Text content"},
                "title": {"type": "string", "description": "Document title"},
                "image_paths": {"type": "array", "items": {"type": "string"}, "description": "Images to embed"}
            },
            "required": ["output_path"]
        }
    },
    {
        "name": "create_zip",
        "description": "Create ZIP archive from files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Where to save ZIP"},
                "file_paths": {"type": "array", "items": {"type": "string"}, "description": "Files to include"},
                "compression": {"type": "string", "enum": ["deflated", "stored"], "default": "deflated"}
            },
            "required": ["output_path", "file_paths"]
        }
    },
    {
        "name": "convert_document",
        "description": "Text-oriented conversion among TXT/DOCX/PDF/HTML.",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "Input file path"},
                "output_format": {"type": "string", "enum": ["pdf", "html", "txt", "docx"], "description": "Target format"},
                "output_path": {"type": "string", "description": "Optional output path"}
            },
            "required": ["input_path", "output_format"]
        }
    },
    {
        "name": "create_docx",
        "description": "Create DOCX Word document from text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string"},
                "content": {"type": "string"},
                "title": {"type": "string"}
            },
            "required": ["output_path", "content"]
        }
    },
    {
        "name": "read_docx",
        "description": "Extract text and tables from a DOCX file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "docx_path": {"type": "string", "description": "Path to DOCX"},
                "extract": {"type": "string", "enum": ["text", "tables", "all"], "default": "all"}
            },
            "required": ["docx_path"]
        }
    },
    {
        "name": "read_pptx",
        "description": "Extract text and slide content from a PPTX file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pptx_path": {"type": "string", "description": "Path to PPTX"},
                "extract": {"type": "string", "enum": ["text", "slides", "notes", "all"], "default": "all"}
            },
            "required": ["pptx_path"]
        }
    },
    {
        "name": "read_xlsx",
        "description": "Extract data from an XLSX spreadsheet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "xlsx_path": {"type": "string", "description": "Path to XLSX"},
                "sheet": {"type": "string", "description": "Sheet name or index"},
                "range": {"type": "string", "description": "Cell range, e.g. 'A1:D10'"}
            },
            "required": ["xlsx_path"]
        }
    },
    {
        "name": "read_file",
        "description": "Read text from a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "File to read"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write text to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Output filename"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["output_path", "content"]
        }
    },
    {
        "name": "file_info",
        "description": "Get file size, name, extension.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "File to inspect"}
            },
            "required": ["file_path"]
        }
    },
]


# Local inference and tool locality are independent. Expose these app-side
# capabilities to on-device models too; each tool still enforces its own
# connectivity/auth requirements.
_LOCAL_EXTRA_TOOL_NAMES = {
    "web_fetch", "headless_browser", "download_media",
    "modify_docx", "modify_pptx", "modify_xlsx",
    "google_calendar", "gmail",
}
_existing_offline_names = {t["name"] for t in OFFLINE_TOOLS_SCHEMA}
OFFLINE_TOOLS_SCHEMA.extend(
    t for t in TOOLS_SCHEMA
    if t["name"] in _LOCAL_EXTRA_TOOL_NAMES and t["name"] not in _existing_offline_names
)


# RASTACODER_V6_TOOL_RELIABILITY
# Skill IDs are UI-only. They are deliberately never shown to the model.
# The model sees canonical callable function names only.
LOCAL_SKILLS = {
    "text_files": {"tools": ("read_file", "write_file", "file_info")},
    "zip_archive": {"tools": ("create_zip", "file_info")},
    "pdf_read": {"tools": ("read_pdf", "file_info")},
    "pdf_create": {"tools": ("create_pdf",)},
    "document_convert": {"tools": ("convert_document",)},
    "word": {"tools": ("create_docx", "read_docx", "modify_docx")},
    "powerpoint": {"tools": ("read_pptx", "modify_pptx")},
    "excel": {"tools": ("read_xlsx", "modify_xlsx")},
    "ocr": {"tools": ("ocr_image",)},
    "image_processing": {"tools": ("smart_crop",)},
    "video_processing": {"tools": ("ffmpeg_process",)},
    "audio_processing": {"tools": ("ffmpeg_process",)},
    "media_download": {"tools": ("download_media",)},
    "web_fetch": {"tools": ("web_fetch",)},
    "dynamic_web": {"tools": ("headless_browser",)},
    "basic_calculation": {"tools": ("python_execute",)},
    "scientific_calculation": {"tools": ("python_execute",)},
    "data_analysis": {"tools": ("python_execute",)},
    "charts": {"tools": ("python_execute",)},
    "gmail": {"tools": ("gmail",)},
    "google_calendar": {"tools": ("google_calendar",)},
}

ALL_LOCAL_SKILL_IDS = tuple(LOCAL_SKILLS.keys())

LOCAL_TOOL_PROMPT_HINTS = {
    "read_file": "read_file(file_path)",
    "write_file": "write_file(output_path, content)",
    "file_info": "file_info(file_path)",
    "create_zip": "create_zip(output_path, file_paths, compression?)",
    "read_pdf": "read_pdf(pdf_path, pages?)",
    "create_pdf": "create_pdf(output_path, content?, title?, image_paths?)",
    "convert_document": "convert_document(input_path, output_format, output_path?) ; output_format=pdf|html|txt|docx",
    "create_docx": "create_docx(output_path, content, title?)",
    "read_docx": "read_docx(docx_path, extract?)",
    "modify_docx": "modify_docx(input_path, output_path, operations)",
    "read_pptx": "read_pptx(pptx_path, extract?)",
    "modify_pptx": "modify_pptx(input_path, output_path, operations)",
    "read_xlsx": "read_xlsx(xlsx_path, sheet?, range?, extract?)",
    "modify_xlsx": "modify_xlsx(input_path, output_path, operations)",
    "ocr_image": "ocr_image(image_path)",
    "smart_crop": "smart_crop(input_path, output_path, aspect_ratio?)",
    "ffmpeg_process": "ffmpeg_process(input_path, output_path, operation, params?) ; operations=trim|crop|resize|filter|extract_audio|extract_frame|convert ; for MP3/WAV/M4A/AAC/FLAC/OGG audio output use operation=extract_audio and params.format",
    "download_media": "download_media(url, format?)",
    "web_fetch": "web_fetch(url, extract_mode?)",
    "headless_browser": "headless_browser(url, wait_seconds?, extract_selector?)",
    "python_execute": "python_execute(code, file_paths?)",
    "gmail": "gmail(action, query?, message_id?) ; action=list|read",
    "google_calendar": "google_calendar(action, date_range?, event?, event_id?) ; action=list|create|delete",
}


def _offline_tool_names():
    return {tool["name"] for tool in OFFLINE_TOOLS_SCHEMA}


def get_enabled_tool_names(skill_ids=None):
    if skill_ids is None:
        skill_ids = ALL_LOCAL_SKILL_IDS
    enabled = set()
    for skill_id in skill_ids:
        skill = LOCAL_SKILLS.get(str(skill_id))
        if skill:
            enabled.update(skill["tools"])
    return enabled


def get_offline_tools_for_skills(skill_ids=None):
    enabled = get_enabled_tool_names(skill_ids)
    return [tool for tool in OFFLINE_TOOLS_SCHEMA if tool["name"] in enabled]


def build_offline_skill_prompt(skill_ids=None):
    ids = ALL_LOCAL_SKILL_IDS if skill_ids is None else tuple(str(x) for x in skill_ids)
    selected = [skill_id for skill_id in ids if skill_id in LOCAL_SKILLS]
    base = (
        "You are RastaCoder, an AI assistant on Android. Tool availability is manually selected by the user. "
        "UI Skill/category labels are not callable functions and are intentionally omitted from this prompt."
    )
    if not selected:
        return base + " No tools are enabled. Answer directly and never emit a tool call."

    enabled_tools = get_enabled_tool_names(selected)
    ordered_tools = [t["name"] for t in OFFLINE_TOOLS_SCHEMA if t["name"] in enabled_tools]
    lines = [
        base,
        "When a tool is needed, output ONLY this XML wrapper with valid JSON inside:",
        "<tool_call>",
        '{"name":"CANONICAL_FUNCTION_NAME","arguments":{"exact_parameter_name":"value"}}',
        "</tool_call>",
        "CALLABLE FUNCTIONS (these exact names only):",
    ]
    for tool_name in ordered_tools:
        lines.append(f"- {LOCAL_TOOL_PROMPT_HINTS[tool_name]}")
    lines.extend([
        "STRICT TOOL-CALL RULES:",
        "- The name field MUST be one canonical function name listed above. Never call a Skill/category label.",
        "- arguments MUST use the exact parameter names shown in that function signature.",
        "- Never invent generic argument keys such as param, request, instruction, or command.",
        "- Use attached file basenames exactly as shown in the user message; the app resolves them to real paths.",
        "- Choose a sensible output filename yourself. Do not ask the user for an output path when a filename can be chosen safely.",
        "- Do not place prose before or after a tool call. After the tool result, give the concise final answer.",
        "- Use only the callable functions listed above.",
    ])
    return "\n".join(lines)


# Import-time invariant: the 21-skill catalogue must cover exactly every local
# tool exposed before classification. This intentionally fails fast in CI if a
# future tool is added without assigning it to at least one skill.
_skill_covered_tools = get_enabled_tool_names(ALL_LOCAL_SKILL_IDS)
_offline_tools = _offline_tool_names()
if _skill_covered_tools != _offline_tools:
    missing = sorted(_offline_tools - _skill_covered_tools)
    extra = sorted(_skill_covered_tools - _offline_tools)
    raise RuntimeError(f"Local skill coverage mismatch; missing={missing}, extra={extra}")



def _safe_diag_value(value: Any) -> Any:
    """Redact secrets and bound large diagnostic payloads."""
    secret_words = {"api_key", "access_token", "google_access_token", "authorization", "token", "password"}
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_s = str(key)
            if key_s.lower() in secret_words or key_s == "_context":
                out[key_s] = "[REDACTED]"
            else:
                out[key_s] = _safe_diag_value(item)
        return out
    if isinstance(value, list):
        return [_safe_diag_value(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + "...[truncated]"
    return value


def _record_tool_diag(context: Dict[str, Any], stage: str, **fields: Any) -> None:
    if not isinstance(context, dict):
        return
    events = context.setdefault('_diagnostics', [])
    if not isinstance(events, list):
        return
    event = {"stage": stage}
    event.update({k: _safe_diag_value(v) for k, v in fields.items()})
    events.append(event)


def execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    context: Dict[str, Any]
) -> Any:
    """
    Execute a tool by name.

    Args:
        tool_name: Name of the tool to execute
        args: Tool arguments
        context: Execution context (tokens, etc.)

    Returns:
        Tool result

    Raises:
        ToolError: If tool execution fails
    """
    original_tool_name = tool_name
    tool_name, args, compatibility_notes = normalize_tool_call(tool_name, args, context=context)
    bridge = get_bridge()
    if compatibility_notes:
        bridge.log(
            "Tool compatibility: " + "; ".join(compatibility_notes),
            level="warn",
        )

    tool_map = {
        "web_fetch": web_fetch,
        "headless_browser": headless_browser,
        "read_pdf": read_pdf,
        "create_pdf": create_pdf,
        "create_docx": create_docx,
        "convert_document": convert_document,
        "read_docx": read_docx,
        "modify_docx": modify_docx,
        "read_pptx": read_pptx,
        "modify_pptx": modify_pptx,
        "read_xlsx": read_xlsx,
        "modify_xlsx": modify_xlsx,
        "create_zip": create_zip,
        "download_media": download_media,
        "google_calendar": google_calendar,
        "gmail": gmail,
        "ffmpeg_process": _ffmpeg_process,
        "ocr_image": _ocr_image,
        "smart_crop": _smart_crop,
        "python_execute": python_execute,
        "file_info": _file_info,
        "read_file": read_file,
        "write_file": write_file,
    }

    if tool_name not in tool_map:
        raise ToolError(
            f"[MODEL_TOOL_NAME_ERROR] Unknown tool '{original_tool_name}'. "
            f"Normalized name: '{tool_name}'."
        )

    # Manual Skill boundary comes before schema validation. A hallucinated
    # disabled tool must never be repaired into an executable call.
    allowed_tools = context.get('_allowed_tools')
    if allowed_tools is not None and tool_name not in set(allowed_tools):
        _record_tool_diag(context, "disabled", tool=tool_name, original_tool=original_tool_name)
        raise ToolError(
            f"[MODEL_TOOL_DISABLED] Tool '{tool_name}' is not enabled for this conversation."
        )

    _record_tool_diag(
        context, "normalized", tool=tool_name, original_tool=original_tool_name,
        args=_safe_diag_value(args), repairs=compatibility_notes,
    )

    # Validate required parameters and top-level enum values only after the
    # compatibility layer has synthesized deterministic safe defaults.
    schema_entry = next((t for t in TOOLS_SCHEMA if t.get("name") == tool_name), None)
    if schema_entry:
        input_schema = schema_entry.get("input_schema", {})
        missing = [
            key for key in input_schema.get("required", [])
            if key not in args or args.get(key) is None or args.get(key) == ""
        ]
        if missing:
            _record_tool_diag(context, "schema_error", tool=tool_name, missing=missing, args=_safe_diag_value(args))
            raise ToolError(
                f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name} missing required "
                f"parameter(s): {', '.join(missing)}. Received: {sorted(args.keys())}. "
                "Retry the same enabled tool with corrected arguments; choose a sensible output filename yourself when only output_path is missing."
            )
        for key, spec in input_schema.get("properties", {}).items():
            if key in args and isinstance(spec, dict) and spec.get("enum"):
                if args[key] not in spec["enum"]:
                    _record_tool_diag(context, "enum_error", tool=tool_name, key=key, value=args[key])
                    raise ToolError(
                        f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name}.{key} received "
                        f"{args[key]!r}; allowed values: {spec['enum']}. Retry with one allowed value."
                    )

    tool_func = tool_map[tool_name]

    # Resolve file paths: if a tool arg is a basename that matches an attached file,
    # replace it with the full path so native tools can find the file
    file_map = context.get('_file_map', {})
    if file_map:
        _resolve_file_paths(args, file_map)

    # Resolve relative output paths to writable directory
    output_dir = context.get('output_dir')
    if output_dir:
        _resolve_output_paths(args, output_dir)

    _record_tool_diag(context, "paths_resolved", tool=tool_name, args=_safe_diag_value(args))

    # Add context to args for tools that need it
    if tool_name in ["google_calendar", "gmail"]:
        args["_context"] = context

    # Pass output_dir to python_execute for file writing and plot auto-save
    if tool_name == "python_execute" and output_dir:
        args["output_dir"] = output_dir

    # Pass timeout for native tools
    if tool_name in ["ocr_image", "ffmpeg_process", "smart_crop"]:
        args["_timeout_ms"] = context.get("tool_timeout_ms", 30000)

    # Strip internal keys that Claude may echo back from context
    args.pop('_timeout_ms', None) if tool_name not in ["ocr_image", "ffmpeg_process", "smart_crop"] else None

    try:
        import inspect
        inspect.signature(tool_func).bind(**args)
    except TypeError as e:
        raise ToolError(f"[MODEL_TOOL_ARGUMENT_ERROR] {tool_name}: {str(e)}")

    return tool_func(**args)


def _resolve_file_paths(args: Dict[str, Any], file_map: Dict[str, str]) -> None:
    """Resolve basename references to full file paths using the attached files map."""
    import os
    path_keys = ['image_path', 'input_path', 'pdf_path', 'file_path', 'path', 'docx_path', 'pptx_path', 'xlsx_path']
    for key in path_keys:
        if key in args:
            value = args[key]
            if isinstance(value, str):
                # Direct match (value is already a basename in the map)
                if value in file_map:
                    args[key] = file_map[value]
                # Try matching basename of a full path Claude may have guessed
                elif os.path.basename(value) in file_map:
                    args[key] = file_map[os.path.basename(value)]

    # Also resolve arrays of paths (e.g. image_paths for create_pdf, file_paths for create_zip)
    array_path_keys = ['image_paths', 'file_paths']
    for key in array_path_keys:
        if key in args and isinstance(args[key], list):
            resolved = []
            for p in args[key]:
                if isinstance(p, str):
                    if p in file_map:
                        resolved.append(file_map[p])
                    elif os.path.basename(p) in file_map:
                        resolved.append(file_map[os.path.basename(p)])
                    else:
                        resolved.append(p)
                else:
                    resolved.append(p)
            args[key] = resolved


def _resolve_output_paths(args: Dict[str, Any], output_dir: str) -> None:
    """Resolve relative output paths to a writable directory."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    output_keys = ['output_path']
    for key in output_keys:
        if key in args:
            value = args[key]
            if isinstance(value, str) and not os.path.isabs(value):
                args[key] = os.path.join(output_dir, value)


def _file_info(file_path: str, **kwargs) -> dict:
    """Get file metadata (size, name, extension)."""
    import os
    if not os.path.exists(file_path):
        raise ToolError(f"File not found: {file_path}")
    size_bytes = os.path.getsize(file_path)
    return {
        "name": os.path.basename(file_path),
        "path": file_path,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "extension": os.path.splitext(file_path)[1].lstrip('.'),
    }


def _ffmpeg_process(**kwargs) -> dict:
    """FFmpeg processing - delegates to native Flutter tool."""
    from ..bridge import get_bridge
    bridge = get_bridge()

    timeout_ms = kwargs.pop('_timeout_ms', 30000)
    # FFmpeg gets 10x the base timeout (video processing is slow)
    return bridge.call_native("ffmpeg", kwargs, timeout_ms=timeout_ms * 10)


def _ocr_image(**kwargs) -> dict:
    """OCR - delegates to native ML Kit tool."""
    from ..bridge import get_bridge
    bridge = get_bridge()

    timeout_ms = kwargs.pop('_timeout_ms', 30000)
    return bridge.call_native("ocr", kwargs, timeout_ms=timeout_ms)


def _smart_crop(**kwargs) -> dict:
    """Smart crop with face detection - delegates to native tool."""
    from ..bridge import get_bridge
    bridge = get_bridge()

    timeout_ms = kwargs.pop('_timeout_ms', 30000)
    # Smart crop gets 10x the base timeout (video processing is slow)
    return bridge.call_native("smart_crop", kwargs, timeout_ms=timeout_ms * 10)

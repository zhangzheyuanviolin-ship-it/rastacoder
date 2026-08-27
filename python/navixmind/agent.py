"""
Agent - ReAct loop implementation with Claude integration

This module implements the main agent logic, handling user queries,
tool execution, and response generation using a proper ReAct pattern.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from .bridge import get_bridge, ToolError
from .session import get_session, apply_delta
from .crash_logger import CrashLogger
from .tools import (
    execute_tool, TOOLS_SCHEMA, OFFLINE_TOOLS_SCHEMA,
    ALL_LOCAL_SKILL_IDS, build_offline_skill_prompt,
    get_enabled_tool_names, get_offline_tools_for_skills,
)
from .tools.compat import normalize_tool_call, normalize_tool_name
from .tools.path_contract import logicalize_path

# RASTACODER_V4_TOOL_CONTRACT


# Constants (defaults, overridden by settings via context)
DEFAULT_MAX_ITERATIONS = 50
DEFAULT_MAX_TOOL_CALLS = 50
DEFAULT_MAX_TOKENS = 16384
MAX_CONTEXT_TOKENS = 150000
DEFAULT_MODEL = "claude-opus-4-20250514"
SONNET_MODEL = "claude-sonnet-4-20250514"
FALLBACK_MODEL = "claude-haiku-4-5-20251001"

# Cost threshold for switching to cheaper model (percentage of daily limit)
COST_THRESHOLD_FOR_HAIKU = 80

# Simple query patterns that can use Haiku
SIMPLE_QUERY_PATTERNS = [
    "what time",
    "what day",
    "what date",
    "convert",
    "format",
    "translate to",
    "is this",
    "yes or no",
    "true or false",
    "classify",
    "categorize",
    "extract",
    "list the",
    "count the",
    "how many",
    "summarize briefly",
]

# Complex query patterns that need Sonnet
COMPLEX_QUERY_PATTERNS = [
    "analyze",
    "explain in detail",
    "compare and contrast",
    "write code",
    "debug",
    "implement",
    "design",
    "create a plan",
    "step by step",
    "research",
    "investigate",
]

# Global API key storage (set via Flutter)
_api_key: Optional[str] = None

# Global Google access token (set via Flutter or per-query context)
_access_token: Optional[str] = None


def set_api_key(key: str) -> None:
    """Set the Claude API key globally."""
    global _api_key
    _api_key = key
    CrashLogger.log_info("API key set")


def get_api_key() -> Optional[str]:
    """Get the Claude API key (from global or environment)."""
    return _api_key or os.environ.get('CLAUDE_API_KEY')


def set_access_token(token: str) -> None:
    """Set the Google access token globally."""
    global _access_token
    _access_token = token
    CrashLogger.log_info("Google access token set")


# System prompt
SYSTEM_PROMPT = """You are NavixMind, an AI assistant running on an Android device. You have access to
various tools through the NavixMind OS environment.

AVAILABLE TOOLS:
- **python_execute** — Run Python code in a secure sandbox (math, numpy, pandas, matplotlib, json, re, datetime, collections, itertools, functools, statistics, csv, base64, hashlib). Use print() for output. FORBIDDEN: subprocess, os, sys, shutil, socket, http, urllib, pathlib, glob, signal, ctypes, multiprocessing, threading.
- **web_fetch** — Fetch a webpage and extract text, HTML, or links
- **headless_browser** — Load JavaScript-heavy pages in a headless browser
- **read_pdf** — Extract text from PDF files (supports page ranges)
- **create_pdf** — Create PDF from text and/or images
- **create_zip** — Create ZIP archives from one or more files (supports deflated/stored compression)
- **convert_document** — Text-oriented conversion among TXT, DOCX, PDF, and HTML; complex layout may be simplified
- **create_docx** — Create a new Word DOCX document from text
- **read_docx** — Extract text, tables, and metadata from DOCX files
- **modify_docx** — Modify existing DOCX files (replace text, add paragraphs, update table cells)
- **read_pptx** — Extract text, slide content, speaker notes from PPTX files
- **modify_pptx** — Modify existing PPTX files (replace text, add slides, update shapes, set notes)
- **read_xlsx** — Extract cell data, sheet names, and formulas from XLSX files
- **modify_xlsx** — Modify existing XLSX files (set cells, formulas, add rows/sheets, delete sheets)
- **ffmpeg_process** — Process video/audio: trim, crop, resize, filter, extract audio/frame, convert, concatenate, mix audio, merge A/V, or use advanced custom FFmpeg. Returns media_duration_seconds (actual media length) and processing_time_ms (execution time) — do NOT confuse them. NEVER use % patterns (like %03d) in output filenames — the tool expects a single output file. To split media into segments, use multiple trim calls with start/duration.
- **smart_crop** — Smart crop video/image to focus on faces (for simple face-centered cropping only)
- **ocr_image** — Extract text from images using OCR
- **download_media** — Download video/audio from supported platforms (NOT YouTube)
- **google_calendar** — Query or manage Google Calendar events (list, create, update, delete)
- **gmail** — Read Gmail messages (list, read). Read-only access — sending is not available.
- **file_info** — Get file metadata (size, name, extension)
- **read_file** — Read text content from a file (any text-based format)
- **write_file** — Write text content to a file (saved to device, available for download/sharing)
- **list_files** — List/discover files and directories, including recursive/pattern searches
- **file_manage** — Create directories; copy, move, rename, delete, touch or test files/directories
- **list_zip / extract_zip** — Inspect and safely extract ZIP archives
- **pdf_manage** — Merge, split, extract/reorder/delete/rotate PDF pages
- **image_compose** — Resize/convert/concat/overlay/crop/adjust/rotate/flip/filter images
- **create_pptx / create_xlsx** — Create PowerPoint presentations and Excel workbooks

GOOGLE SERVICES (google_calendar, gmail):
- These tools require the user to connect their Google account in Settings first.
- If a Google tool returns "Google account not connected", tell the user: "Please connect your Google account in Settings to use this feature."
- Do NOT retry Google tools after a "not connected" error — it won't help until the user connects.

FILE HANDLING:
- Users attach files to their messages. Use file basenames (e.g., "photo.jpg") when calling tools — paths are resolved automatically.
- Output files (create_pdf, create_zip, ffmpeg_process, write_file, etc.) are saved to the device. Use descriptive filenames.
- **ALWAYS include the output file path in your response** when you create or modify a file. The user needs the path to share/download the result. Example: "Here's your compressed video: `/path/to/output.mp4`"
- To check file properties, use the file_info tool. Do NOT import os in python_execute.

FFMPEG PATTERNS (use these exact patterns — do NOT improvise):
- **Keep every Nth second**: operation="filter", vf="select='not(mod(floor(t),N))',setpts=N/FRAME_RATE/TB", af="aselect='not(mod(floor(t),N))',asetpts=N/SR/TB" (e.g. N=2 keeps seconds 0,2,4...)
- **Remove every Nth second**: operation="filter", vf="select='mod(floor(t),N)',setpts=N/FRAME_RATE/TB", af="aselect='mod(floor(t),N)',asetpts=N/SR/TB"
- **Keep time range**: operation="trim" with start/end or start/duration — simpler and more reliable than select
- **Black & white**: operation="filter", vf="hue=s=0" (do NOT use format=gray — it breaks Android playback)
- **Speed up/slow down**: operation="filter", vf="setpts=0.5*PTS" (2x speed), af="atempo=2.0"
- **A/V sync rule**: ALWAYS provide matching af when using vf with select/aselect. Use setpts=N/FRAME_RATE/TB for video and asetpts=N/SR/TB for audio.
- **NEVER use mod(n,...) for time-based editing** — n is frame number (varies with FPS), use t (time in seconds) instead.
- Prefer operation="trim" for simple cuts over complex select expressions.
- **NEVER use operation="custom"** for video filtering. Use operation="filter" with vf/af — it handles A/V sync, codec selection, and Android compatibility automatically. operation="custom" is ONLY for rare edge cases that no other operation supports.
- Commas inside filter expressions are escaped automatically — write them normally.
- When combining effects (e.g. select + black & white), chain them in a single vf string: vf="select='...',setpts=...,hue=s=0"

PYTHON EXECUTION:
- Use python_execute for calculations, data processing, algorithms, text manipulation.
- Use pandas for tabular data analysis (DataFrames, groupby, describe, CSV read/write).
- Use matplotlib for charts/graphs. Plots are auto-saved as PNG and returned to the user.
- An OUTPUT_DIR variable is available in python_execute for saving output files (CSV, plots, etc.).
- Do NOT use python_execute to call ffmpeg/ffprobe — use the ffmpeg_process tool instead.
- Do NOT access files via os/pathlib — use dedicated tools (read_file, read_pdf, ocr_image, file_info, etc.).
- python_execute cannot access the network — use web_fetch for that.
- python_execute can only read files explicitly listed in its file_paths parameter.

PROBLEM-SOLVING — NEVER GIVE UP ON FIRST ATTEMPT:
- If a tool cannot do something in one call, BREAK IT DOWN into multiple steps. Never say "I can't" without trying an alternative.
- For complex file operations (e.g., "improve all slide titles", "reformat every table", "update all headings"):
  1. FIRST read the file to understand its structure (read_pptx, read_docx, read_xlsx, read_pdf).
  2. THEN iterate: process each element (slide, paragraph, row, page) one at a time using modify tools or python_execute.
  3. Each iteration can use YOUR intelligence to generate improved content (new titles, better descriptions, reformatted text).
- For Office files, use the dedicated create/read/modify/convert tools. python_execute does not expose python-docx, python-pptx, or openpyxl inside its restricted sandbox.
- If one approach fails, TRY ANOTHER. Exhaust all options before telling the user something is impossible.
- This applies to ALL tasks, not just documents: web fetching, media processing, data analysis — always adapt and retry.

ERROR HANDLING:
- If a tool fails, try an alternative approach FIRST. Only explain the error if all approaches fail.
- If python_execute fails due to a forbidden module, use the correct dedicated tool.
- If a file is not found, ask the user to re-attach it.

STYLE:
- Be concise; this is a mobile interface.
- Use markdown for formatting when helpful.
- For code or data, use monospace formatting.

CRITICAL RULE:
- Each user message is a NEW request. You MUST call the appropriate tools to fulfill it.
- NEVER assume previous results satisfy the current request. If the user asks to process, convert, or create a file, you MUST call the tool — do NOT just describe the result or say "done".
- The conversation history shows what happened before. Your job is to execute the NEW request NOW using tools.
"""

# User-friendly error messages
ERROR_MESSAGES = {
    "network_offline": "No internet connection. Check your network and try again.",
    "api_rate_limit": "Too many requests. Please wait {seconds} seconds.",
    "api_quota_exceeded": "Daily API limit reached. Resets at midnight.",
    "auth_expired": "Session expired. Tap to sign in again.",
    "storage_full": "Device storage full ({used}/{total}). Free up space to continue.",
    "ffmpeg_invalid_input": "Cannot process this video format. Try a different file.",
    "llm_overloaded": "AI service is busy. Retrying automatically...",
    "tool_timeout": "Operation timed out after {seconds}s. The file may be too large.",
    "python_crash": "Internal error occurred. The app will recover automatically.",
    "file_too_large": "File is too large ({size}MB). Maximum allowed: {max}MB.",
}


class ClaudeClient:
    """Client for Claude API with retry logic."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str = SYSTEM_PROMPT,
        tools: Optional[List[dict]] = None,
        max_tokens: int = 4096,
        retry_count: int = 3
    ) -> dict:
        """
        Create a message with Claude, with retry logic for transient errors.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Tool definitions
            max_tokens: Maximum tokens in response
            retry_count: Number of retries for transient errors

        Returns:
            API response dict

        Raises:
            APIError: On non-recoverable API errors
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }

        if tools:
            body["tools"] = tools

        last_error = None
        for attempt in range(retry_count):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=body,
                    timeout=120
                )

                if response.status_code == 200:
                    return response.json()

                error_body = response.json()
                error_message = error_body.get('error', {}).get('message', 'Unknown API error')

                # Handle rate limiting with retry
                if response.status_code == 429:
                    retry_after = int(response.headers.get('retry-after', 5))
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(retry_after)
                        continue
                    raise APIError(f"Rate limited: {error_message}", 429)

                # Handle server errors with retry
                if response.status_code in (500, 502, 503):
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise APIError(f"Server error: {error_message}", response.status_code)

                # Non-recoverable errors
                raise APIError(error_message, response.status_code)

            except requests.Timeout:
                last_error = APIError("Request timed out", 408)
                if attempt < retry_count - 1:
                    continue
                raise last_error

            except requests.RequestException as e:
                last_error = APIError(f"Network error: {str(e)}", 0)
                if attempt < retry_count - 1:
                    import time
                    time.sleep(1)
                    continue
                raise last_error

        raise last_error or APIError("Unknown error", 0)


# Max tokens per model size for offline inference.
# Context windows are now 32K for all models.
# Max output tokens are conservative to keep generation fast on mobile.
OFFLINE_MAX_TOKENS = {
    'qwen2.5-coder-0.5b': 512,
    'qwen2.5-coder-1.5b': 1024,
    'qwen2.5-coder-3b': 1024,
    'ministral-3-3b': 2048,
    'qwen3-4b': 2048,
}

# RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
# Per-request local prompt is built from manually enabled skills.
OFFLINE_SYSTEM_PROMPT = build_offline_skill_prompt(ALL_LOCAL_SKILL_IDS)


# RASTACODER_V14_ORDERED_JSONISH_PARSER
def _ordered_literal_eval(text: str) -> Any:
    """Literal-eval JSON-ish model output while preserving brace-item source order."""
    import ast

    def walk(node):
        if isinstance(node, ast.Dict):
            return {walk(k): walk(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.List):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Tuple):
            return [walk(v) for v in node.elts]
        if isinstance(node, ast.Set):
            # Qwen-class small models sometimes use {a,b,c} where the schema
            # requires [a,b,c]. Preserve lexical order instead of creating a
            # Python set whose iteration order would scramble spreadsheet rows.
            return [walk(v) for v in node.elts]
        return ast.literal_eval(node)

    return walk(ast.parse(text, mode='eval').body)


def _parse_mapping(text: str) -> Optional[dict]:
    """Parse JSON-like tool call objects without executing model text."""
    import re

    value = text.strip()
    candidates = [value, re.sub(r',\s*([}\]])', r'\1', value)]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    try:
        parsed = _ordered_literal_eval(value)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError, TypeError):
        pass
    return None


def _missing_json_value_keys(text: str) -> List[str]:
    """Return quoted object keys emitted without a ': value' payload."""
    import re
    keys: List[str] = []
    pattern = re.compile(r'(?P<prefix>[,{]\s*)"(?P<key>(?:\\.|[^"\\])*)"\s*(?=,|})')
    for match in pattern.finditer(str(text or '')):
        key = match.group('key').strip()
        if key and key not in keys:
            keys.append(key)
    return keys


def _coerce_tool_args(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        parsed = _parse_mapping(value)
        if isinstance(parsed, dict):
            return parsed
        value = value.strip()
        return {"param": value} if value else {}
    return {}


def _extract_json_objects(text: str) -> List[str]:
    """Extract balanced JSON/dict-looking objects, including truncated calls."""
    results = []
    i = 0
    while i < len(text):
        if text[i] != '{':
            i += 1
            continue
        depth = 0
        start = i
        in_string = False
        quote = None
        escape = False
        while i < len(text):
            c = text[i]
            if escape:
                escape = False
            elif c == '\\' and in_string:
                escape = True
            elif c in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote = c
                elif c == quote:
                    in_string = False
                    quote = None
            elif not in_string:
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        results.append(text[start:i + 1])
                        i += 1
                        break
            i += 1
        if depth > 0:
            # Small models occasionally omit only trailing braces. Repair JSON
            # candidates conservatively; invalid objects are rejected later.
            results.append(text[start:i] + '}' * depth)
    return results


def _build_tool_use(name: Any, arguments: Any, source: str, index: int) -> Optional[dict]:
    # Normalize with arguments BEFORE checking the canonical-name set. Preserve
    # both sides of that repair for the copyable diagnostic log.
    raw_args = _coerce_tool_args(arguments)
    canonical, args, parser_repairs = normalize_tool_call(name, raw_args)
    known = {t['name'] for t in TOOLS_SCHEMA}
    if canonical not in known:
        return None
    return {
        "type": "tool_use",
        "id": f"call_{abs(hash(source)) % 10**8:08d}_{index}",
        "name": canonical,
        "input": args,
        "_raw_name": str(name or ""),
        "_raw_input": raw_args,
        "_raw_source": str(source)[:1500],
        "_parser_repairs": list(parser_repairs),
    }


def _try_parse_tool_json(json_str: str, index: int) -> Optional[dict]:
    """Parse common JSON/dict function-call variants into a tool_use block."""
    # A quoted key with no colon/value means the model omitted semantic content.
    # Reject it into the bounded format-repair path; never silently execute null.
    if _missing_json_value_keys(json_str):
        return None
    call_data = _parse_mapping(json_str)
    if not call_data:
        return None

    # OpenAI-style nested function / function_call objects.
    nested = call_data.get('function') or call_data.get('function_call')
    if isinstance(nested, dict):
        return _build_tool_use(
            nested.get('name') or nested.get('tool') or nested.get('tool_name'),
            nested.get('arguments', nested.get('args', nested.get('parameters', nested.get('input', {})))),
            json_str,
            index,
        )

    name = call_data.get('name') or call_data.get('tool') or call_data.get('tool_name')
    arg_key = next((k for k in ('arguments', 'args', 'parameters', 'input') if k in call_data), None)
    if arg_key:
        arguments = call_data.get(arg_key)
    else:
        # Some models emit {"name":"tool","input_path":"x",...}.
        arguments = {
            k: v for k, v in call_data.items()
            if k not in {'name', 'tool', 'tool_name', 'type', 'id'}
        }
    return _build_tool_use(name, arguments, json_str, index)


def _try_parse_function_syntax(text: str, index: int) -> Optional[dict]:
    """Safely parse tool_name(key=value, ...) syntax using AST literals only."""
    import ast
    import re

    known = {t['name'] for t in TOOLS_SCHEMA}
    for match in re.finditer(r'([A-Za-z_][A-Za-z0-9_\-]*)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)', text, re.DOTALL):
        raw = match.group(0)
        try:
            node = ast.parse(raw, mode='eval').body
        except SyntaxError:
            continue
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.args:
            continue
        raw_name = node.func.id
        args = {}
        valid = True
        for kw in node.keywords:
            if kw.arg is None:
                valid = False
                break
            try:
                args[kw.arg] = ast.literal_eval(kw.value)
            except (ValueError, TypeError):
                valid = False
                break
        if valid:
            return _build_tool_use(raw_name, args, raw, index)
    return None


def _sanitize_reasoning(text: str) -> str:
    """Keep human-readable reasoning while excluding tool-call payloads."""
    import re
    value = str(text or '').strip()
    if not value:
        return ''
    value = re.sub(
        r'<(?:tool_call|function_call|tool_result|tool_use)>[\s\S]*?</(?:tool_call|function_call|tool_result|tool_use)>',
        '', value, flags=re.IGNORECASE,
    )
    value = re.sub(r'</?(?:tool_call|function_call|tool_result|tool_use)[^>]*>', '', value, flags=re.IGNORECASE)
    for obj in list(_extract_json_objects(value)):
        try:
            if _try_parse_tool_json(obj, 0) is not None:
                value = value.replace(obj, '')
        except Exception:
            pass
    known = {str(t.get('name', '')) for t in TOOLS_SCHEMA}
    kept = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if not line:
            if kept and kept[-1] != '':
                kept.append('')
            continue
        if lower.startswith(('tool:', 'result:', 'executing ', 'code:', 'file:', '[tool result]', '[tool error]')):
            continue
        if any(lower.startswith(name.lower() + '(') for name in known if name):
            continue
        kept.append(raw_line.rstrip())
    while kept and not kept[-1].strip():
        kept.pop()
    return '\n'.join(kept).strip()


def _thinking_for_ui(parts: List[str], mode: str) -> str:
    if str(mode) == 'disabled':
        return ''
    return _sanitize_reasoning('\n\n'.join(str(x) for x in parts if str(x).strip()))


def _extract_reasoning_blocks(content_blocks: List[Dict[str, Any]]) -> str:
    import re
    parts = []
    for block in content_blocks or []:
        if not isinstance(block, dict) or block.get('type') != 'text':
            continue
        text = str(block.get('text', ''))
        for match in re.finditer(r'<think>([\s\S]*?)</think>', text, flags=re.IGNORECASE):
            value = match.group(1).strip()
            if value:
                parts.append(value)
        # Defensive open-tag recovery when generation ends before </think>.
        open_match = re.search(r'<think>([\s\S]*)$', text, flags=re.IGNORECASE)
        if open_match:
            value = open_match.group(1).strip()
            if value:
                parts.append(value)
    return _sanitize_reasoning('\n\n'.join(parts))


def _strip_reasoning_from_blocks(content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import re
    cleaned = []
    for block in content_blocks or []:
        if not isinstance(block, dict) or block.get('type') != 'text':
            cleaned.append(block)
            continue
        text = str(block.get('text', ''))
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<think>[\s\S]*$', '', text, flags=re.IGNORECASE)
        if text.strip():
            copy = dict(block)
            copy['text'] = text.strip()
            cleaned.append(copy)
    return cleaned


# RASTACODER_V10_CONTEXT_SAFE_TOOL_RESULTS
_SEARCH_RESULT_TOOLS = {
    'anysearch_search', 'anysearch_extract', 'anysearch_get_sub_domains',
    'exa_search', 'langsearch_search', 'tavily_search',
}


def _tool_result_char_budget(context: Dict[str, Any], max_output_tokens: int = 2048) -> int:
    """Bound tool payloads before they are re-prefilled into a local model."""
    if not isinstance(context, dict) or 'offline_model_info' not in context:
        return 10000
    try:
        ctx = max(2048, min(int(context.get('local_context_tokens', 32768)), 32768))
    except (TypeError, ValueError):
        ctx = 32768
    try:
        out = max(256, min(int(max_output_tokens), 8192))
    except (TypeError, ValueError):
        out = 2048
    available_tokens = max(900, ctx - out - 2400)
    return max(1200, min(int(available_tokens * 1.25), 12000))


def _trim_model_text(value: Any, limit: int) -> Tuple[str, bool]:
    value = str(value or '').strip()
    if len(value) <= limit:
        return value, False
    if limit < 300:
        return value[:limit], True
    head = max(180, int(limit * 0.78))
    tail = max(80, limit - head - 55)
    return value[:head] + '\n...[context-safe truncation]...\n' + value[-tail:], True


def _search_result_payload_for_model(tool_name: str, result: Any, max_chars: int) -> str:
    if not isinstance(result, dict):
        return _trim_model_text(result, max_chars)[0]
    provider = str(result.get('provider') or tool_name.replace('_search', ''))
    query = str(result.get('query') or '').strip()
    answer = str(result.get('answer') or '').strip()
    rows = result.get('results')
    out = [f'provider: {provider}']
    if query:
        out.append(f'query: {query}')
    if answer:
        answer_text, _ = _trim_model_text(answer, min(1400, max(350, max_chars // 4)))
        out += ['provider_answer:', answer_text]
    if isinstance(rows, list) and rows:
        out.append(f'result_count: {len(rows)}')
        remaining = max(600, max_chars - sum(len(x) for x in out) - 120)
        per = max(320, remaining // max(1, len(rows)))
        for index, item in enumerate(rows, 1):
            if not isinstance(item, dict):
                snippet, _ = _trim_model_text(item, per)
                out += [f'[{index}]', snippet]
                continue
            title = item.get('title') or item.get('name') or item.get('id') or f'Result {index}'
            url = item.get('url') or item.get('link') or item.get('id') or ''
            published = item.get('publishedDate') or item.get('published_date') or item.get('datePublished') or item.get('date') or ''
            summary = item.get('summary') or item.get('snippet') or item.get('description')
            if not summary:
                highlights = item.get('highlights')
                if isinstance(highlights, list):
                    summary = '\n'.join(str(x) for x in highlights if str(x).strip())
            if not summary:
                summary = item.get('text') or item.get('content') or item.get('raw_content') or ''
            summary_text, _ = _trim_model_text(summary, max(180, per - 180))
            out.append(f'[{index}] {title}')
            if url:
                out.append(f'URL: {url}')
            if published:
                out.append(f'published: {published}')
            if summary_text:
                out += ['summary:', summary_text]
    elif result.get('content'):
        payload, _ = _trim_model_text(result.get('content'), max(300, max_chars - 220))
        out += ['content:', payload]
    else:
        raw, _ = _trim_model_text(_json_boundary_dumps(result, ensure_ascii=False), max_chars)
        out.append(raw)
    final, truncated = _trim_model_text('\n'.join(out), max_chars)
    if truncated:
        final += '\ncontext_safety_note: Search output was truncated before local-model prefill.'
    return final


# RASTACODER_V12_LOGICAL_LIST_RESULTS
def _list_files_payload_for_model(result: Any, max_chars: int) -> str:
    """Expose logical workspace paths to the model, never the physical app root."""
    if not isinstance(result, dict):
        return _trim_model_text(result, max_chars)[0]
    root = str(result.get('workspace_root') or '')
    requested = str(result.get('requested_path') or '.').strip() or '.'
    lines = [
        f'workspace_path: {requested}',
        f'count: {int(result.get("count") or 0)}',
        f'recursive: {bool(result.get("recursive"))}',
    ]
    pattern = result.get('pattern')
    if pattern:
        lines.append(f'pattern: {pattern}')
    entries = result.get('entries') if isinstance(result.get('entries'), list) else []
    lines.append('entries:')
    for item in entries:
        if not isinstance(item, dict):
            continue
        logical = logicalize_path(str(item.get('path') or item.get('name') or ''), root) if root else str(item.get('name') or '')
        kind = str(item.get('type') or 'file')
        if kind == 'directory':
            lines.append(f'- directory: {logical}')
        else:
            lines.append(f'- file: {logical} ({int(item.get("size_bytes") or 0)} bytes)')
    if result.get('truncated'):
        lines.append('truncated: true')
    payload, truncated = _trim_model_text('\n'.join(lines), max_chars)
    if truncated:
        payload += '\ncontext_safety_note: File listing was truncated before local-model prefill.'
    return payload


def _prepare_tool_result_for_model(tool_name: str, result: Any, context: Dict[str, Any], max_output_tokens: int) -> str:
    max_chars = _tool_result_char_budget(context, max_output_tokens)
    if tool_name in _SEARCH_RESULT_TOOLS:
        payload = _search_result_payload_for_model(tool_name, result, max_chars)
    elif tool_name == 'list_files':
        payload = _list_files_payload_for_model(result, max_chars)
    elif isinstance(result, dict):
        large_key = next((k for k in ('content', 'text', 'result', 'output', 'summary') if str(result.get(k) or '').strip()), None)
        if large_key:
            meta = {k: v for k, v in result.items() if k != large_key and isinstance(v, (str, int, float, bool, type(None)))}
            meta_text = _json_boundary_dumps(meta, ensure_ascii=False)
            body_limit = max(300, max_chars - len(meta_text) - 120)
            body, truncated = _trim_model_text(result.get(large_key), body_limit)
            payload = f'metadata: {meta_text}\n{large_key}:\n{body}'
            if truncated:
                payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
        else:
            payload, truncated = _trim_model_text(_json_boundary_dumps(result, ensure_ascii=False), max_chars)
            if truncated:
                payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
    else:
        payload, truncated = _trim_model_text(result, max_chars)
        if truncated:
            payload += '\ncontext_safety_note: Tool output was truncated before local-model prefill.'
    return (
        f'TOOL_RESULT\ntool: {tool_name}\nstatus: succeeded\npayload:\n{payload}\n\n'
        'NEXT_ACTION: Use this result to continue the original user request. If it is sufficient, answer the user directly in the user\'s language and stop. '
        'Do not repeat raw JSON or the tool result. Call another enabled tool only when genuinely necessary.'
    )


# RASTACODER_V13_DOCUMENT_INGESTION
_DOCUMENT_READ_TOOLS = {"read_file", "read_pdf", "read_docx", "read_pptx", "read_xlsx"}


def _document_primary_text(result: Any) -> str:
    if not isinstance(result, dict):
        return str(result or "")
    for key in ("content", "text"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value
    for key in ("sheets", "data", "slides", "tables", "notes"):
        value = result.get(key)
        if value not in (None, "", [], {}):
            try:
                return _json_boundary_dumps(value, ensure_ascii=False)
            except Exception:
                return str(value)
    return ""


def _split_complete_document_text(text: str, chunk_chars: int = 7000) -> List[str]:
    value = str(text or "")
    size = max(1200, int(chunk_chars))
    return [value[i:i + size] for i in range(0, len(value), size)] or [""]


def _document_result_for_local_model(
    client: Any,
    user_query: str,
    tool_name: str,
    result: Any,
    context: Dict[str, Any],
    max_output_tokens: int,
) -> str:
    # Map-reduce large document text with the same downloaded local model.
    source_text = _document_primary_text(result)
    budget = _tool_result_char_budget(context, max_output_tokens)
    if not source_text or len(source_text) <= budget:
        return _prepare_tool_result_for_model(
            tool_name, result, context, max_output_tokens
        )

    chunks = _split_complete_document_text(source_text)
    helper = LocalLLMClient(
        model_id=str(getattr(client, "model_id", getattr(client, "model", ""))),
        temperature=0.2,
        top_p=0.9,
        thinking_mode="disabled",
    )
    note_cap = max(420, min(1200, (budget - 900) // max(1, len(chunks))))
    notes: List[str] = []
    failures = 0
    source_query = str(user_query or "").strip()[:2400]
    helper_system = (
        "You are an internal document-ingestion helper. Read the supplied chunk "
        "and return compact evidence notes for the original user request. Preserve "
        "relevant names, numbers, dates, claims, qualifications, structure and uncertainty. "
        "Do not call tools. Do not output JSON or XML. Do not answer the user directly."
    )

    for index, chunk in enumerate(chunks, 1):
        prompt = (
            f"ORIGINAL USER REQUEST:\n{source_query}\n\n"
            f"DOCUMENT CHUNK {index}/{len(chunks)}:\n{chunk}\n\n"
            f"Return evidence notes for this chunk only, at most {note_cap} characters."
        )
        note = ""
        try:
            response = helper.create_message(
                messages=[{"role": "user", "content": prompt}],
                system=helper_system,
                tools=None,
                max_tokens=max(256, min(640, int(max_output_tokens))),
                retry_count=1,
            )
            blocks = _strip_reasoning_from_blocks(response.get("content", []))
            note = _extract_text_content(blocks).strip()
        except Exception as exc:
            failures += 1
            context.setdefault("_diagnostics", []).append({
                "stage": "document_ingestion_chunk_error",
                "tool": tool_name,
                "chunk": index,
                "chunks": len(chunks),
                "error": str(exc)[:1200],
            })

        if not note:
            head = max(180, note_cap // 2)
            tail = max(120, note_cap - head - 40)
            note = chunk[:head]
            if len(chunk) > head:
                note += "\n...[chunk fallback]...\n" + chunk[-tail:]
        note, _ = _trim_model_text(note, note_cap)
        notes.append(f"[chunk {index}/{len(chunks)}]\n{note}")

    metadata = {}
    if isinstance(result, dict):
        for key, value in result.items():
            if (
                key not in {"content", "text", "slides", "tables", "notes", "sheets", "data"}
                and isinstance(value, (str, int, float, bool, type(None)))
            ):
                metadata[key] = value

    digest = "\n\n".join(notes)
    payload = (
        "DOCUMENT_INGESTION\n"
        f"tool: {tool_name}\n"
        f"source_chars: {len(source_text)}\n"
        f"chunks_processed: {len(chunks)}\n"
        f"chunk_failures: {failures}\n"
        "coverage: complete executor-returned text was partitioned across all chunks\n"
        f"metadata: {_json_boundary_dumps(metadata, ensure_ascii=False)}\n"
        "evidence_digest:\n"
        f"{digest}"
    )
    payload, _ = _trim_model_text(payload, budget)
    context.setdefault("_diagnostics", []).append({
        "stage": "document_ingestion_complete",
        "tool": tool_name,
        "source_chars": len(source_text),
        "chunks": len(chunks),
        "chunk_failures": failures,
        "digest_chars": len(payload),
    })
    return (
        f"TOOL_RESULT\ntool: {tool_name}\nstatus: succeeded\npayload:\n{payload}\n\n"
        "NEXT_ACTION: Answer the original user request from the evidence digest. "
        "The digest covers every source chunk. Do not request the same document again "
        "unless the user explicitly asks for a different extraction."
    )


def _tool_error_for_model(tool_name: str, error: Any) -> str:
    msg = str(error or '').strip()
    low = msg.lower()
    if 'api key' in low and ('未配置' in msg or 'not configured' in low):
        recovery = 'NON_RETRYABLE: Do not call this provider again. Tell the user to configure its API Key in Tool Management.'
    elif 'http 401' in low or 'http 403' in low or 'unauthorized' in low or 'forbidden' in low:
        recovery = 'NON_RETRYABLE: Credentials or permission are invalid. Do not loop; report the configuration problem.'
    elif 'http 429' in low or 'rate limit' in low:
        recovery = 'Do not retry the same provider repeatedly. If another enabled search provider is available, use it once; otherwise report the rate limit.'
    elif tool_name == 'list_files' and ('directory not found' in low or 'workspace' in low or 'path' in low):
        recovery = (
            "RECOVERABLE: If the user asked for the workspace root, retry once with list_files(path='.', recursive as needed). "
            "For an unknown nested path, first list path='.' and choose an existing logical path. Do not ask the user to re-attach a workspace directory."
        )
    elif '[model_tool_argument_error]' in low or '[model_tool_name_error]' in low:
        recovery = 'RECOVERABLE: Retry once with one enabled canonical tool name and the exact documented argument keys.'
    elif 'timeout' in low or 'request failed' in low or 'network' in low:
        recovery = 'RECOVERABLE_ONCE: Retry once or use one different enabled provider. Do not loop on the same failure.'
    else:
        recovery = 'Do not repeat the identical failed call. Correct the cause if clear; otherwise explain the failure to the user.'
    return f'TOOL_FAILURE\ntool: {tool_name}\nerror: {msg[:1800]}\nrecovery: {recovery}'


def _merge_continuation_text(parts: List[str], current: str) -> str:
    pieces = [str(x).strip() for x in parts if str(x).strip()]
    current = str(current or '').strip()
    if current:
        if not pieces or current != pieces[-1]:
            pieces.append(current)
    return '\n'.join(pieces).strip()


class LocalLLMClient:
    """Client for on-device LLM inference via native bridge.

    Same interface as ClaudeClient but calls bridge.call_native('llm_generate')
    instead of the Claude API. The Kotlin layer handles MLC Engine and converts
    the response to Claude-compatible format.
    """

    def __init__(
        self, model_id: str, temperature: float = 0.7, top_p: float = 0.95,
        thinking_mode: str = 'model_default'
    ):
        self.model_id = model_id
        self.model = model_id  # For usage tracking compatibility
        self.temperature = max(0.0, min(float(temperature), 2.0))
        self.top_p = max(0.01, min(float(top_p), 1.0))
        self.thinking_mode = thinking_mode if thinking_mode in {'model_default', 'enabled', 'disabled'} else 'model_default'

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str = OFFLINE_SYSTEM_PROMPT,
        tools: Optional[List[dict]] = None,
        max_tokens: int = 2048,
        retry_count: int = 1,
        stream_to_ui: bool = False
    ) -> dict:
        """
        Run inference via the native bridge (MLC LLM engine).

        Converts Claude-format tools to OpenAI format, calls the native bridge,
        and returns the Claude-compatible response from Kotlin.
        """
        bridge = get_bridge()

        # Convert messages: ensure all content is string (OpenAI format)
        openai_messages = self._convert_messages(messages, system)
        # Thinking mode is controlled only by the user's saved setting.
        # Never infer it from skills or task type. Qwen3 understands these switches.
        if 'qwen3' in self.model_id.lower() and self.thinking_mode != 'model_default':
            directive = '/think' if self.thinking_mode == 'enabled' else '/no_think'
            for msg in reversed(openai_messages):
                if msg.get('role') == 'user':
                    msg['content'] = f"{msg.get('content', '')}\n{directive}"
                    break

        # Convert tools from Claude format to OpenAI function calling format
        openai_tools = None
        if tools:
            openai_tools = self._convert_tools_to_openai(tools)

        # Manual local output limit is honored; retain a hard safety ceiling.
        max_tokens = max(1, min(int(max_tokens), 8192))

        # Build args for native call
        args = {
            'messages_json': _json_boundary_dumps(openai_messages),
            'max_tokens': max_tokens,
            'model_id': self.model_id,
            'temperature': self.temperature,
            'top_p': self.top_p,
            # RASTACODER_V14_STREAM_TO_UI_FLAG
            'stream_to_ui': bool(stream_to_ui),
        }
        if openai_tools:
            args['tools_json'] = _json_boundary_dumps(openai_tools)

        # Call native with longer timeout for local inference (model loading can take 30-60s)
        try:
            result = bridge.call_native('llm_generate', args, timeout_ms=300000)
        except TimeoutError:
            raise APIError("Local model inference timed out after 300s", 408)
        except ToolError as e:
            raise APIError(f"Local inference error: {e}", 500)

        response_json = result.get('response', '{}')

        try:
            response = json.loads(response_json)
        except json.JSONDecodeError:
            # Garbled output fallback — treat as text response
            CrashLogger.log_error("local_llm_parse", Exception(f"Failed to parse: {response_json[:200]}"))
            response = {
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": response_json}],
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }

        # Preserve local reasoning separately before tool-call normalization. It
        # is kept out of model history but returned to Flutter for the user's
        # expandable Thinking panel.
        response['_reasoning'] = _extract_reasoning_blocks(response.get('content', []))

        # Validate tool calls — small models may produce invalid JSON for tool inputs
        content = response.get('content', [])
        sanitized_content = []
        for block in content:
            if block.get('type') == 'tool_use':
                raw_name = block.get('name')
                raw_input = _coerce_tool_args(block.get('input', {}))
                name, tool_input, parser_repairs = normalize_tool_call(raw_name, raw_input)
                block = dict(block)
                block['_raw_name'] = str(raw_name or '')
                block['_raw_input'] = raw_input
                block['_raw_source'] = _json_boundary_dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500]
                block['_parser_repairs'] = list(parser_repairs)
                block['name'] = name
                block['input'] = tool_input
            sanitized_content.append(block)
        response['content'] = sanitized_content

        # Parse <tool_call> tags from text content (Hermes function calling format).
        # Small models may produce tool calls as text instead of structured format,
        # and MLC engine may return them as text if its parser doesn't catch them.
        response = self._parse_tool_calls_from_text(response)

        return response

    @staticmethod
    def _parse_tool_calls_from_text(response: dict) -> dict:
        """Recover common tool-call variants emitted as text by small models."""
        import re

        if response.get('stop_reason') == 'tool_use':
            # Structured calls still need name/argument normalization.
            normalized = []
            for block in response.get('content', []):
                if block.get('type') == 'tool_use':
                    raw_name = block.get('_raw_name', block.get('name'))
                    raw_input = block.get('_raw_input', _coerce_tool_args(block.get('input', {})))
                    name, args, parser_repairs = normalize_tool_call(block.get('name'), block.get('input', {}))
                    block = dict(block)
                    block.setdefault('_raw_name', str(raw_name or ''))
                    block.setdefault('_raw_input', raw_input)
                    block.setdefault('_raw_source', _json_boundary_dumps({'name': raw_name, 'arguments': raw_input}, ensure_ascii=False)[:1500])
                    existing_repairs = block.get('_parser_repairs') if isinstance(block.get('_parser_repairs'), list) else []
                    block['_parser_repairs'] = list(existing_repairs) + [r for r in parser_repairs if r not in existing_repairs]
                    block['name'] = name
                    block['input'] = args
                normalized.append(block)
            response['content'] = normalized
            return response

        new_content = []
        found = False
        for block in response.get('content', []):
            if block.get('type') != 'text':
                new_content.append(block)
                continue

            original = block.get('text', '')
            text = re.sub(r'<think>[\s\S]*?</think>', '', original, flags=re.IGNORECASE).strip()
            text = re.sub(r'```(?:json|javascript|python)?\s*', '', text, flags=re.IGNORECASE)
            text = text.replace('```', '').strip()
            tool_blocks = []
            remaining = text

            # Hermes and common function-call XML-ish tags.
            tag_pattern = r'<(?:tool_call|function_call|function)>\s*([\s\S]*?)\s*</(?:tool_call|function_call|function)>'
            tag_matches = re.findall(tag_pattern, text, flags=re.IGNORECASE)
            for i, tagged in enumerate(tag_matches):
                parsed_any = False
                for j, obj in enumerate(_extract_json_objects(tagged)):
                    parsed = _try_parse_tool_json(obj, i * 10 + j)
                    if parsed:
                        tool_blocks.append(parsed)
                        parsed_any = True
                if not parsed_any:
                    parsed = _try_parse_tool_json(tagged.strip(), i)
                    if parsed:
                        tool_blocks.append(parsed)
                    else:
                        fn = _try_parse_function_syntax(tagged, i)
                        if fn:
                            tool_blocks.append(fn)
            if tag_matches:
                remaining = re.sub(tag_pattern, '', remaining, flags=re.IGNORECASE).strip()

            # Raw JSON/dict objects.
            if not tool_blocks:
                objects = _extract_json_objects(text)
                for i, obj in enumerate(objects):
                    parsed = _try_parse_tool_json(obj, i)
                    if parsed:
                        tool_blocks.append(parsed)
                        remaining = remaining.replace(obj, '', 1).strip()

            # Last-resort safe function syntax: tool_name(key="value").
            if not tool_blocks:
                fn = _try_parse_function_syntax(text, 0)
                if fn:
                    tool_blocks.append(fn)
                    # Preserve prose only when it is not just the function call.
                    name = fn['name']
                    remaining = re.sub(rf'\b{re.escape(name)}\s*\([\s\S]*?\)', '', remaining, count=1).strip()

            if tool_blocks:
                found = True
                remaining = re.sub(
                    r'</?(?:tool_call|function_call|function)\b[^>]*>',
                    '', remaining, flags=re.IGNORECASE,
                ).strip()
                if remaining:
                    new_content.append({"type": "text", "text": remaining})
                new_content.extend(tool_blocks)
            elif tag_matches or re.search(r'<(?:tool_call|function_call|function)\b', text, flags=re.IGNORECASE):
                # Recognizable tool-call wrapper, invalid payload/name. Never
                # leak it into final prose; let the ReAct loop request a retry.
                response['_tool_parse_error'] = tagged[:1500] if tag_matches else original[:1500]
                remaining = re.sub(
                    r'</?(?:tool_call|function_call|function)\b[^>]*>',
                    '', remaining, flags=re.IGNORECASE,
                ).strip()
                new_content.append({"type": "text", "text": remaining}) if remaining else None
            else:
                new_content.append(block)

        if found:
            response['content'] = new_content
            response['stop_reason'] = 'tool_use'
        elif response.get('_tool_parse_error'):
            response['content'] = new_content
            response['stop_reason'] = 'tool_parse_error'
        return response

    def _convert_messages(self, messages: List[Dict[str, Any]], system: str) -> List[Dict[str, Any]]:
        """Convert Claude-format messages to OpenAI chat format.

        MLC engine does NOT support 'tool' role or 'tool_calls' in assistant messages.
        Instead we flatten:
        - Assistant tool_use blocks → plain text showing the tool call as <tool_call> JSON
        - User tool_result blocks → user message with "[Tool Result] ..." text
        """
        openai_msgs = []

        # System message first
        openai_msgs.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            if isinstance(content, str):
                openai_msgs.append({"role": role, "content": content})
            elif isinstance(content, list):
                if role == 'assistant':
                    # Flatten tool_use blocks into plain text (MLC doesn't support tool_calls)
                    text_parts = []
                    for block in content:
                        if block.get('type') == 'text':
                            text = block.get('text', '')
                            if text:
                                text_parts.append(text)
                        elif block.get('type') == 'tool_use':
                            call_json = json.dumps({
                                "name": block.get('name', ''),
                                "arguments": block.get('input', {})
                            })
                            text_parts.append(f"<tool_call>\n{call_json}\n</tool_call>")
                    combined = '\n'.join(text_parts)
                    if combined:
                        openai_msgs.append({"role": "assistant", "content": combined})
                elif role == 'user':
                    # Flatten tool_result blocks into user messages
                    text_parts = []
                    for block in content:
                        if block.get('type') == 'tool_result':
                            tool_id = block.get('tool_use_id', '')
                            result_content = block.get('content', '')
                            is_error = block.get('is_error', False)
                            prefix = "[Tool Error]" if is_error else "[Tool Result]"
                            text_parts.append(f"{prefix} (id={tool_id}): {result_content}")
                        elif isinstance(block, str):
                            text_parts.append(block)
                        elif block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                    combined = '\n'.join(text_parts)
                    if combined:
                        openai_msgs.append({"role": "user", "content": combined})
                else:
                    # Fallback: join text parts
                    text = '\n'.join(
                        b.get('text', str(b)) if isinstance(b, dict) else str(b)
                        for b in content
                    )
                    openai_msgs.append({"role": role, "content": text})

        return openai_msgs

    @staticmethod
    def _convert_tools_to_openai(claude_tools: List[dict]) -> List[dict]:
        """Convert Claude tool definitions to OpenAI function calling format.

        Claude format:
        {"name": "foo", "description": "...", "input_schema": {"type": "object", "properties": {...}}}

        OpenAI format:
        {"type": "function", "function": {"name": "foo", "description": "...", "parameters": {...}}}
        """
        openai_tools = []
        for tool in claude_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}})
                }
            })
        return openai_tools


# RASTACODER_V11_OPENAI_COMPATIBLE_CLIENT
class OpenAICompatibleClient:
    """Adapter for /v1/chat/completions providers with native tool_calls."""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = str(base_url or '').strip().rstrip('/')
        self.api_key = str(api_key or '').strip()
        self.model = str(model or '').strip()
        if not self.base_url or not self.model:
            raise APIError('OpenAI-compatible Base URL and Model ID are required', 400)

    def _endpoint(self) -> str:
        lower = self.base_url.lower()
        if lower.endswith('/chat/completions'):
            return self.base_url
        if lower.endswith('/v1'):
            return self.base_url + '/chat/completions'
        return self.base_url + '/v1/chat/completions'

    @staticmethod
    def _convert_messages(messages: List[Dict[str, Any]], system: str) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = [{"role": "system", "content": system}]
        for msg in messages:
            role = str(msg.get('role', 'user'))
            content = msg.get('content', '')
            if isinstance(content, str):
                converted.append({"role": role, "content": content})
                continue
            if not isinstance(content, list):
                converted.append({"role": role, "content": str(content)})
                continue
            if role == 'assistant':
                text_parts = []
                calls = []
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get('type') == 'text' and block.get('text'):
                        text_parts.append(str(block.get('text')))
                    elif block.get('type') == 'tool_use':
                        calls.append({
                            'id': str(block.get('id') or f"call_{len(calls)}"),
                            'type': 'function',
                            'function': {
                                'name': str(block.get('name') or ''),
                                'arguments': json.dumps(block.get('input') or {}, ensure_ascii=False),
                            },
                        })
                item: Dict[str, Any] = {'role': 'assistant', 'content': '\n'.join(text_parts) or None}
                if calls:
                    item['tool_calls'] = calls
                converted.append(item)
            elif role == 'user':
                ordinary = []
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_result':
                        converted.append({
                            'role': 'tool',
                            'tool_call_id': str(block.get('tool_use_id') or ''),
                            'content': str(block.get('content') or ''),
                        })
                    elif isinstance(block, dict) and block.get('type') == 'text':
                        ordinary.append(str(block.get('text') or ''))
                    elif isinstance(block, str):
                        ordinary.append(block)
                if any(x for x in ordinary):
                    converted.append({'role': 'user', 'content': '\n'.join(x for x in ordinary if x)})
            else:
                converted.append({'role': role, 'content': str(content)})
        return converted

    def create_message(
        self, messages: List[Dict[str, Any]], system: str = SYSTEM_PROMPT,
        tools: Optional[List[dict]] = None, max_tokens: int = 4096, retry_count: int = 2
    ) -> dict:
        headers = {'content-type': 'application/json'}
        if self.api_key:
            headers['authorization'] = f'Bearer {self.api_key}'
        body: Dict[str, Any] = {
            'model': self.model,
            'messages': self._convert_messages(messages, system),
            'max_tokens': int(max_tokens),
        }
        if tools:
            body['tools'] = LocalLLMClient._convert_tools_to_openai(tools)
            body['tool_choice'] = 'auto'

        last_error: Optional[APIError] = None
        for attempt in range(max(1, retry_count)):
            try:
                response = requests.post(self._endpoint(), headers=headers, json=body, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get('choices') if isinstance(data, dict) else None
                    if not isinstance(choices, list) or not choices:
                        raise APIError('OpenAI-compatible response has no choices', 502)
                    choice = choices[0] if isinstance(choices[0], dict) else {}
                    message = choice.get('message') if isinstance(choice.get('message'), dict) else {}
                    blocks: List[Dict[str, Any]] = []
                    text = message.get('content')
                    if isinstance(text, str) and text.strip():
                        blocks.append({'type': 'text', 'text': text})
                    raw_calls = message.get('tool_calls')
                    if not isinstance(raw_calls, list):
                        raw_calls = []
                    legacy = message.get('function_call')
                    if isinstance(legacy, dict):
                        raw_calls = list(raw_calls) + [{'id': 'legacy_function_call', 'function': legacy}]
                    for index, call in enumerate(raw_calls):
                        if not isinstance(call, dict):
                            continue
                        fn = call.get('function') if isinstance(call.get('function'), dict) else call
                        raw_name = fn.get('name')
                        raw_args = _coerce_tool_args(fn.get('arguments', fn.get('args', {})))
                        canonical, canonical_args, repairs = normalize_tool_call(raw_name, raw_args)
                        blocks.append({
                            'type': 'tool_use',
                            'id': str(call.get('id') or f'call_{index}'),
                            'name': canonical,
                            'input': canonical_args,
                            '_raw_name': str(raw_name or ''),
                            '_raw_input': raw_args,
                            '_raw_source': json.dumps(call, ensure_ascii=False)[:1500],
                            '_parser_repairs': repairs,
                        })
                    finish = str(choice.get('finish_reason') or '').lower()
                    if any(b.get('type') == 'tool_use' for b in blocks) or finish in {'tool_calls', 'function_call'}:
                        stop_reason = 'tool_use'
                    elif finish in {'length', 'max_tokens'}:
                        stop_reason = 'max_tokens'
                    else:
                        stop_reason = 'end_turn'
                    usage_raw = data.get('usage') if isinstance(data.get('usage'), dict) else {}
                    return {
                        'stop_reason': stop_reason,
                        'content': blocks,
                        'usage': {
                            'input_tokens': int(usage_raw.get('prompt_tokens') or usage_raw.get('input_tokens') or 0),
                            'output_tokens': int(usage_raw.get('completion_tokens') or usage_raw.get('output_tokens') or 0),
                        },
                    }

                try:
                    error_data = response.json()
                except Exception:
                    error_data = {}
                error_obj = error_data.get('error') if isinstance(error_data, dict) else None
                if isinstance(error_obj, dict):
                    message = str(error_obj.get('message') or error_obj)
                else:
                    message = str(error_data or getattr(response, 'text', '') or 'Unknown API error')
                last_error = APIError(message[:2000], int(response.status_code))
                if response.status_code in {408, 429, 500, 502, 503, 504} and attempt < retry_count - 1:
                    import time
                    time.sleep(1 if response.status_code == 429 else 2 ** attempt)
                    continue
                raise last_error
            except requests.Timeout:
                last_error = APIError('OpenAI-compatible request timed out', 408)
                if attempt < retry_count - 1:
                    continue
                raise last_error
            except requests.RequestException as exc:
                last_error = APIError(f'OpenAI-compatible network error: {exc}', 0)
                if attempt < retry_count - 1:
                    continue
                raise last_error
        raise last_error or APIError('Unknown OpenAI-compatible API error', 0)


class APIError(Exception):
    """Error from Claude API."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def handle_request(request_json: str) -> str:
    """
    Main entry point for handling requests from Flutter.

    Args:
        request_json: JSON-RPC request string

    Returns:
        JSON-RPC response string
    """
    try:
        request = json.loads(request_json)
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        if method == 'process_query':
            result = process_query(
                user_query=params.get('user_query', ''),
                files=params.get('files', []),
                context=params.get('context', {})
            )
            return _json_boundary_dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }, ensure_ascii=False)

        elif method == 'apply_delta':
            apply_delta(params)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"success": True}
            })

        elif method == 'set_api_key':
            set_api_key(params.get('api_key', ''))
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"success": True}
            })

        elif method == 'set_access_token':
            set_access_token(params.get('access_token', ''))
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"success": True}
            })

        elif method == 'self_improve':
            result = self_improve(
                conversation=params.get('conversation', []),
                current_prompt=params.get('current_prompt', ''),
                api_key=params.get('api_key', ''),
            )
            return _json_boundary_dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }, ensure_ascii=False)

        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })

    except json.JSONDecodeError as e:
        CrashLogger.log_error("handle_request", e)
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        })
    except Exception as e:
        CrashLogger.log_error("handle_request", e)
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })



# RASTACODER_V14_JSON_BOUNDARY
def _json_boundary_safe(value: Any) -> Any:
    """Recursively convert arbitrary executor/model values to deterministic JSON-safe data."""
    if isinstance(value, dict):
        return {str(k): _json_boundary_safe(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return [_json_boundary_safe(v) for v in sorted(value, key=lambda x: repr(x))]
    if isinstance(value, (list, tuple)):
        return [_json_boundary_safe(v) for v in value]
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        if hasattr(value, 'item'):
            return _json_boundary_safe(value.item())
    except Exception:
        pass
    return str(value)


def _json_boundary_dumps(value: Any, **kwargs: Any) -> str:
    return json.dumps(_json_boundary_safe(value), **kwargs)


def _diag_safe(value: Any) -> Any:
    secret_words = {'api_key', 'access_token', 'google_access_token', 'authorization', 'token', 'password'}
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            key_s = str(key)
            result[key_s] = '[REDACTED]' if key_s.lower() in secret_words or key_s == '_context' else _diag_safe(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_diag_safe(v) for v in list(value)[:50]]
    if isinstance(value, (set, frozenset)):
        return [_diag_safe(v) for v in sorted(value, key=lambda x: repr(x))[:50]]
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + '...[truncated]'
    return value


def _format_diagnostics(context: Dict[str, Any]) -> str:
    events = context.get('_diagnostics', []) if isinstance(context, dict) else []
    safe = _diag_safe(events)
    try:
        return _json_boundary_dumps(safe, ensure_ascii=False, indent=2)
    except Exception:
        return str(safe)

def process_query(
    user_query: str,
    files: List[str] = None,
    context: Dict[str, Any] = None
) -> dict:
    """
    Process a user query through the ReAct agent loop.

    This implements the full ReAct pattern:
    1. Send query to Claude with tools available
    2. If Claude uses a tool, execute it and send result back
    3. Repeat until Claude responds with end_turn or max iterations reached

    Args:
        user_query: The user's query text
        files: List of file paths attached to the query
        context: Additional context (tokens, device info, etc.)

    Returns:
        Result dict with 'content' key containing the response
    """
    bridge = get_bridge()
    session = get_session()
    context = context or {}
    context['_diagnostics'] = []
    context['_current_files'] = list(files or [])
    reasoning_parts: List[str] = []
    parse_retry_count = 0

    # Get API key (from global storage or environment)
    api_key = get_api_key()

    # Check if offline model is selected (doesn't need API key)
    preferred = context.get('preferred_model', '')
    is_offline_model = 'offline_model_info' in context if context else False
    is_openai_compatible = preferred == 'openai-compatible'
    openai_config = context.get('openai_compatible') if isinstance(context.get('openai_compatible'), dict) else {}

    if is_openai_compatible:
        if not str(openai_config.get('base_url') or '').strip() or not str(openai_config.get('model') or '').strip():
            return {
                "content": "OpenAI 兼容接口尚未配置完整。请在设置中填写 Base URL 和 Model ID。",
                "error": True
            }
    elif not api_key and not is_offline_model:
        return {
            "content": "API key not configured. Please enter your Claude API key to get started, or select an offline model.",
            "error": True
        }

    # Inject stored Google access token as fallback if not in per-query context
    if _access_token and 'google_access_token' not in context:
        context['google_access_token'] = _access_token

    # Add attachment info to context for model selection
    if files:
        context['has_attachments'] = True

    # Use custom system prompt from context, or fall back to default
    system_prompt = context.get('system_prompt', SYSTEM_PROMPT)

    # Select appropriate model based on query and context
    selected_model, model_reason = _select_model(user_query, context)
    bridge.log(model_reason, level="info")

    # Determine if this is an offline model
    is_offline = 'offline_model_info' in context if context else False

    if is_offline:
        # RASTACODER_V5_SKILLS_PARAMS_BENCH_STREAM
        requested_skills = context.get('enabled_skills')
        if not isinstance(requested_skills, list):
            requested_skills = list(ALL_LOCAL_SKILL_IDS)
        enabled_skills = [str(x) for x in requested_skills if str(x) in ALL_LOCAL_SKILL_IDS]
        enabled_tools = get_enabled_tool_names(enabled_skills)
        context['_allowed_tools'] = sorted(enabled_tools)
        system_prompt = build_offline_skill_prompt(enabled_skills)
        local_temperature = max(0.0, min(float(context.get('local_temperature', 0.7)), 2.0))
        local_top_p = max(0.01, min(float(context.get('local_top_p', 0.95)), 1.0))
        local_thinking_mode = str(context.get('local_thinking_mode', 'model_default'))
        client = LocalLLMClient(
            model_id=selected_model, temperature=local_temperature,
            top_p=local_top_p, thinking_mode=local_thinking_mode
        )
        bridge.log(
            f"Using on-device inference; skills={len(enabled_skills)}/{len(ALL_LOCAL_SKILL_IDS)}, tools={len(enabled_tools)}/{len(get_enabled_tool_names(ALL_LOCAL_SKILL_IDS))}",
            level="info"
        )
        context['_diagnostics'].append({
            'stage': 'query_config',
            'enabled_skills': list(enabled_skills),
            'allowed_tools': sorted(enabled_tools),
            'thinking_mode': local_thinking_mode,
            'temperature': local_temperature,
            'top_p': local_top_p,
            'current_files': [os.path.basename(p) for p in (files or [])],
        })
    else:
        if system_prompt != SYSTEM_PROMPT:
            bridge.log("Using custom system prompt", level="info")
        if is_openai_compatible:
            client = OpenAICompatibleClient(
                base_url=str(openai_config.get('base_url') or ''),
                api_key=str(openai_config.get('api_key') or ''),
                model=str(openai_config.get('model') or selected_model),
            )
            bridge.log(f"Using OpenAI-compatible cloud model: {client.model}", level="info")
        else:
            client = ClaudeClient(api_key, model=selected_model)

    # Build initial messages from session context. Local context budget is
    # a user-entered exact token count; cloud keeps the existing global ceiling.
    if is_offline:
        configured_context = max(512, min(int(context.get('local_context_tokens', 32768)), 32768))
        configured_output = max(1, min(int(context.get('local_max_output_tokens', 2048)), 8192))
        context_budget = min(configured_context, max(512, 38912 - configured_output))
    else:
        context_budget = MAX_CONTEXT_TOKENS
    messages = session.get_context_for_llm(context_budget)
    bridge.log(f"Context: {len(messages)} previous messages, {len(session.messages)} in session", level="info")

    # Add current user message with any attachments
    user_content = user_query
    # Persist file map across queries so subsequent queries can reference earlier uploads
    if not hasattr(session, '_file_map'):
        session._file_map = {}
    if files:
        file_list = ", ".join(os.path.basename(f) for f in files)
        user_content += f"\n\n[Attached files: {file_list}]"
        # Merge new uploads into persistent file map
        for f in files:
            session._file_map[os.path.basename(f)] = f
    # Always provide the full file map to tools
    context['_file_map'] = dict(session._file_map)

    messages.append({"role": "user", "content": user_content})

    # Add to session for context tracking (use enriched content so file names persist)
    session.add_message("user", user_content)

    # ReAct loop — limits configurable from Settings
    max_iterations = max(1, int(context.get('max_iterations', DEFAULT_MAX_ITERATIONS)))
    max_tool_calls = int(context.get('max_tool_calls', DEFAULT_MAX_TOOL_CALLS))
    unlimited_tool_calls = max_tool_calls <= 0
    max_tokens = context.get('max_tokens', DEFAULT_MAX_TOKENS)

    # On-device output length follows the dedicated manual setting.
    if is_offline:
        max_tokens = max(1, min(int(context.get('local_max_output_tokens', 2048)), 8192))
        tools_schema = get_offline_tools_for_skills(enabled_skills)
    else:
        tools_schema = TOOLS_SCHEMA
    iteration = 0
    tool_call_count = 0
    final_response = None
    created_files = []  # Track output files for session context
    offline_max_token_continuations = 0
    partial_final_chunks: List[str] = []
    force_no_tools_once = False
    successful_tool_turns = 0
    empty_final_recovery_used = False

    while unlimited_tool_calls or iteration < max_iterations:
        iteration += 1
        if unlimited_tool_calls:
            bridge.log(f"Thinking... (step {iteration}, unlimited tool mode)")
        else:
            bridge.log(f"Thinking... (step {iteration}/{max_iterations})", progress=iteration / max_iterations * 0.5)

        try:
            if is_offline:
                bridge.log("Running on device...", level="info")
            else:
                bridge.log("Calling Claude API...", level="info")
            # V10 semantic invariant retained: tools=None if (is_offline and force_no_tools_once) else tools_schema
            # V14 makes the local/cloud split explicit so the local call can carry stream_to_ui.
            if is_offline:
                response = client.create_message(
                    messages=messages,
                    system=system_prompt,
                    tools=None if force_no_tools_once else tools_schema,
                    max_tokens=max_tokens,
                    stream_to_ui=True,
                )
            else:
                response = client.create_message(
                    messages=messages,
                    system=system_prompt,
                    tools=tools_schema,
                    max_tokens=max_tokens,
                )
            if is_offline:
                bridge.log("Got response from model", level="info")
            else:
                bridge.log("Got response from Claude", level="info")
        except APIError as e:
            bridge.log(f"API error: {e}", level="error")
            error_msg = _get_user_friendly_error(e)
            session.add_message("assistant", error_msg)
            result = {"content": error_msg, "error": True}
            if is_offline:
                context['_diagnostics'].append({'stage': 'model_error', 'error': str(e)[:2000]})
                result['thinking'] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result
        except Exception as e:
            CrashLogger.log_error("process_query", e)
            bridge.log(f"Exception: {str(e)}", level="error")
            error_msg = f"An unexpected error occurred: {e}"
            session.add_message("assistant", error_msg)
            result = {"content": error_msg, "error": True}
            if is_offline:
                context['_diagnostics'].append({'stage': 'unexpected_error', 'error': str(e)[:2000]})
                result['thinking'] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result

        # Get stop reason and content
        stop_reason = response.get('stop_reason')
        content_blocks = response.get('content', [])
        if is_offline:
            reasoning = _sanitize_reasoning(str(response.get('_reasoning') or ''))
            if reasoning and local_thinking_mode != 'disabled':
                reasoning_parts.append(reasoning)
            context['_diagnostics'].append({
                'stage': 'model_response',
                'stop_reason': stop_reason,
                'reasoning_chars': len(reasoning),
                'content_types': [b.get('type') for b in content_blocks if isinstance(b, dict)],
                'tool_parse_error': bool(response.get('_tool_parse_error')),
            })

        # Log stop reason for visibility
        bridge.log(f"Stop reason: {stop_reason}", level="info")

        # Track usage for cost management
        usage = response.get('usage', {})
        if usage:
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            bridge.log(f"Tokens: {input_tokens} in, {output_tokens} out", level="info")
            _record_usage(
                model=client.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                context=context
            )

        # Log any text content (Claude's thinking before tool use)
        thinking_text = _extract_text_content(content_blocks)
        if thinking_text and stop_reason == 'tool_use':
            # Show a preview of Claude's thinking
            preview = thinking_text[:100] + "..." if len(thinking_text) > 100 else thinking_text
            bridge.log(f"Thinking: {preview}", level="info")

        # Local small-model recovery: a literal <tool_call> wrapper was
        # detected but its payload could not be parsed. Ask the same model to
        # repair the call instead of leaking XML into the final answer.
        if is_offline and stop_reason == 'tool_parse_error':
            parse_retry_count += 1
            raw_bad = str(response.get('_tool_parse_error') or '')[:1000]
            context['_diagnostics'].append({
                'stage': 'tool_parse_retry', 'attempt': parse_retry_count,
                'raw_preview': raw_bad,
            })
            if parse_retry_count <= 2:
                messages.append({
                    'role': 'user',
                    'content': (
                        '[Tool call format error] The previous tool call was not executable. '
                        + (
                            'The previous JSON contained argument key(s) with no value: '
                            + ', '.join(_missing_json_value_keys(raw_bad))
                            + '. Every included key must have a colon and a real JSON value. '
                            'Omit optional keys you do not need. For content/text/body, provide the complete requested text. '
                            if _missing_json_value_keys(raw_bad) else ''
                        )
                        + 'Retry now using ONLY one enabled canonical function name and the exact argument keys '
                        'shown in the system prompt. Do not use Skill/category names or generic keys such as param. '
                        'Do not answer with prose.'
                    )
                })
                continue
            final_response = '工具调用格式连续无法解析。请复制本轮“工具调用诊断”供排查。'
            result = {'content': final_response, 'error': True}
            result['thinking'] = '\n\n'.join(reasoning_parts)
            result['thinking_mode'] = local_thinking_mode
            result['diagnostics'] = _format_diagnostics(context)
            return result

        # Case 1: Agent finished (end_turn)
        if stop_reason == 'end_turn':
            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks
            final_response = _merge_continuation_text(partial_final_chunks, _extract_text_content(visible_blocks))
            if is_offline and not final_response.strip() and successful_tool_turns > 0 and not empty_final_recovery_used:
                empty_final_recovery_used = True
                force_no_tools_once = True
                context['_diagnostics'].append({
                    'stage': 'empty_final_recovery',
                    'successful_tool_turns': successful_tool_turns,
                    'created_files': [os.path.basename(p) for p in created_files],
                })
                messages.append({
                    'role': 'user',
                    'content': (
                        'The requested tool operation already succeeded. Produce the final user-facing answer now. '
                        'Do not call tools. Mention created file paths when applicable. Do not return an empty answer.'
                    ),
                })
                continue
            bridge.log("Preparing response...", progress=0.95)
            # Store response in session. File paths are tracked in session._file_map
            # so follow-up queries can reference them. Do NOT append file list to the
            # assistant text — it confuses the model into thinking work is already done.
            session.add_message("assistant", final_response)
            bridge.log("Done!", progress=1.0)
            result = {"content": final_response}
            if created_files:
                result["created_files"] = created_files
            if is_offline:
                result["thinking"] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
                result["thinking_mode"] = local_thinking_mode
                result["diagnostics"] = _format_diagnostics(context)
            return result

        # Case 2: Agent wants to use tools
        if stop_reason == 'tool_use':
            # Process all tool calls in this response
            tool_results = []

            # Count tools in this response
            tools_in_response = sum(1 for b in content_blocks if b.get('type') == 'tool_use')
            bridge.log(f"Executing {tools_in_response} tool(s)...", level="info")

            for block in content_blocks:
                if block.get('type') == 'tool_use':
                    tool_name = block.get('name')
                    tool_input = block.get('input', {})
                    tool_id = block.get('id')
                    raw_tool_name = block.get('_raw_name', tool_name)
                    raw_tool_input = block.get('_raw_input', tool_input)
                    parser_repairs = block.get('_parser_repairs') if isinstance(block.get('_parser_repairs'), list) else []
                    raw_source = block.get('_raw_source')
                    tool_name, tool_input, compat_notes = normalize_tool_call(tool_name, tool_input, context=context)
                    tool_input = _json_boundary_safe(tool_input)
                    if is_offline:
                        repairs = list(parser_repairs) + [r for r in compat_notes if r not in parser_repairs]
                        context['_diagnostics'].append({
                            'stage': 'tool_call',
                            'raw_name': str(raw_tool_name),
                            'raw_args': _diag_safe(raw_tool_input),
                            'raw_source': _diag_safe(raw_source),
                            'canonical_name': tool_name,
                            'canonical_args': _diag_safe(tool_input),
                            'repairs': repairs,
                        })
                    if compat_notes:
                        bridge.log(
                            "Tool compatibility: " + "; ".join(compat_notes),
                            level="warn",
                        )

                    tool_call_count += 1
                    if not unlimited_tool_calls and tool_call_count > max_tool_calls:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "is_error": True,
                            "content": "Maximum tool calls reached for this query."
                        })
                        continue

                    # Log tool name and input summary
                    input_summary = _summarize_tool_input(tool_name, tool_input)
                    bridge.log(
                        f"Tool: {tool_name} - {input_summary}",
                        progress=None if unlimited_tool_calls else 0.5 + (iteration / max_iterations * 0.3),
                    )

                    try:
                        # Log code for python_execute before running
                        if tool_name == 'python_execute':
                            code = tool_input.get('code', '')
                            if code:
                                bridge.log(f"Code:\n```python\n{code}\n```", level="info")

                        result = execute_tool(tool_name, tool_input, context)
                        # Truncate large results
                        result_str = _json_boundary_dumps(result, ensure_ascii=False) if isinstance(result, (dict, list, tuple, set, frozenset)) else str(result)

                        # Log created files as clickable links and add to file map
                        if isinstance(result, dict):
                            if result.get('output_path'):
                                output_path = result['output_path']
                                bridge.log(f"File: {output_path}", level="info")
                                created_files.append(output_path)
                                session._file_map[os.path.basename(output_path)] = output_path
                            # Also track multi-file results (e.g. FFmpeg split)
                            if result.get('output_paths'):
                                for p in result['output_paths']:
                                    bridge.log(f"File: {p}", level="info")
                                    created_files.append(p)
                                    session._file_map[os.path.basename(p)] = p

                        # Log result summary
                        result_summary = _summarize_tool_result(tool_name, result_str)
                        bridge.log(f"Result: {result_summary}", level="info")

                        if is_offline and tool_name in _DOCUMENT_READ_TOOLS:
                            model_result = _document_result_for_local_model(
                                client, user_query, tool_name, result, context, max_tokens
                            )
                        else:
                            model_result = (
                                _prepare_tool_result_for_model(tool_name, result, context, max_tokens)
                                if (is_offline or is_openai_compatible) else result_str
                            )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": model_result
                        })
                        successful_tool_turns += 1
                    except ToolError as e:
                        bridge.log(f"Tool error: {e}", level="warn")
                        if is_offline:
                            context['_diagnostics'].append({
                                'stage': 'tool_error', 'tool': tool_name, 'error': str(e)[:2000]
                            })
                        error_content = _tool_error_for_model(tool_name, e) if (is_offline or is_openai_compatible) else str(e)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "is_error": True,
                            "content": error_content
                        })
                    except Exception as e:
                        CrashLogger.log_error(f"tool_{tool_name}", e)
                        bridge.log(f"Tool exception: {str(e)}", level="error")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "is_error": True,
                            "content": f"Tool error: {str(e)}"
                        })

            # Add assistant message (with tool_use blocks) and tool results to conversation
            messages.append({"role": "assistant", "content": content_blocks})
            messages.append({"role": "user", "content": tool_results})

            # Continue the loop to get next response
            continue

        # Case 3: Max tokens reached. Cloud keeps legacy continuation behavior.
        # Local models get at most one tool-free continuation, preventing the 50-step max_tokens loop.
        if stop_reason == 'max_tokens':
            visible_blocks = _strip_reasoning_from_blocks(content_blocks) if is_offline else content_blocks
            partial = _extract_text_content(visible_blocks).strip()
            if not is_offline:
                bridge.log("Response hit token limit, continuing...", level="info")
                messages.append({"role": "assistant", "content": content_blocks})
                messages.append({"role": "user", "content": "Continue from where you left off."})
                continue
            if partial:
                partial_final_chunks.append(partial)
            context['_diagnostics'].append({
                'stage': 'offline_max_tokens',
                'continuation': offline_max_token_continuations,
                'partial_chars': len(partial),
                'tool_calls': tool_call_count,
            })
            if offline_max_token_continuations >= 1:
                final_response = _merge_continuation_text(partial_final_chunks[:-1], partial_final_chunks[-1] if partial_final_chunks else '')
                if not final_response:
                    final_response = '本地模型连续达到单次输出上限，且没有产生可用正文。请调高“最大输出 Token”后重试。'
                session.add_message("assistant", final_response)
                result = {"content": final_response}
                if created_files:
                    result["created_files"] = created_files
                result["thinking"] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
                result["thinking_mode"] = local_thinking_mode
                result["diagnostics"] = _format_diagnostics(context)
                return result
            offline_max_token_continuations += 1
            force_no_tools_once = True
            messages.append({"role": "assistant", "content": content_blocks})
            messages.append({
                "role": "user",
                "content": (
                    '[FINAL_ANSWER_CONTINUATION] Continue only the unfinished final answer. '
                    'Do not call any tool, do not repeat earlier text, do not output raw JSON or hidden reasoning, and finish within this response.'
                ),
            })
            continue

        # Case 4: Unexpected stop reason
        bridge.log(f"Unexpected stop reason: {stop_reason}", level="warn")
        partial = _extract_text_content(content_blocks)
        if partial:
            session.add_message("assistant", partial)
            result = {"content": partial}
            if is_offline:
                result['thinking'] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
                result['thinking_mode'] = local_thinking_mode
                result['diagnostics'] = _format_diagnostics(context)
            return result
        break

    # Reached max iterations
    summary = _summarize_progress(messages, tool_call_count)
    max_iter_msg = f"I've reached my step limit after {iteration} iterations and {tool_call_count} tool calls. {summary}"
    session.add_message("assistant", max_iter_msg)
    result = {"content": max_iter_msg}
    if is_offline:
        context['_diagnostics'].append({'stage': 'max_iterations', 'iterations': iteration, 'tool_calls': tool_call_count})
        result['thinking'] = _thinking_for_ui(reasoning_parts, local_thinking_mode)
        result['thinking_mode'] = local_thinking_mode
        result['diagnostics'] = _format_diagnostics(context)
    return result


def _extract_text_content(content_blocks: List[dict]) -> str:
    """Extract all text content from response blocks."""
    text_parts = []
    for block in content_blocks:
        if block.get('type') == 'text':
            text_parts.append(block.get('text', ''))
    return '\n'.join(text_parts)


def _summarize_progress(messages: List[dict], tool_call_count: int) -> str:
    """Summarize what the agent has accomplished."""
    tool_names = set()

    for msg in messages:
        content = msg.get('content', [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    tool_names.add(block.get('name', 'unknown'))

    if tool_names:
        return f"I used these tools: {', '.join(sorted(tool_names))}. Here's what I found so far..."
    return "I was analyzing your request but couldn't complete it."


def _get_user_friendly_error(error: APIError) -> str:
    """Convert API error to user-friendly message."""
    if error.status_code == 429:
        return ERROR_MESSAGES["api_rate_limit"].format(seconds=60)
    if error.status_code == 401:
        return "Invalid API key. Please check your configuration in Settings."
    if error.status_code in (500, 502, 503):
        return ERROR_MESSAGES["llm_overloaded"]
    if error.status_code == 408:
        return ERROR_MESSAGES["tool_timeout"].format(seconds=120)
    return f"Sorry, I encountered an error: {error}"


def _record_usage(model: str, input_tokens: int, output_tokens: int, context: dict) -> None:
    """Record API usage for cost tracking."""
    try:
        bridge = get_bridge()
        bridge._send({
            "jsonrpc": "2.0",
            "method": "record_usage",
            "params": {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        })
    except Exception as e:
        CrashLogger.log_error("record_usage", e)


def _select_model(query: str, context: Dict[str, Any]) -> Tuple[str, str]:
    """
    Select the appropriate model based on query complexity and cost budget.

    Returns:
        Tuple of (model_name, reason)

    Selection criteria:
    1. If cost budget is >= 80% used -> use Haiku to conserve budget
    2. If query is simple (classification, format conversion, etc.) -> use Haiku
    3. If query is complex (analysis, coding, research) -> use Sonnet
    4. Default -> use Sonnet for best quality
    """
    query_lower = query.lower().strip()

    # Check 0: Offline model requested
    requested_model = context.get('preferred_model', '')
    if context.get('offline_model_info'):
        return requested_model, f"Using offline model: {requested_model}"

    # V11 custom OpenAI-compatible provider keeps the exact user-entered model ID.
    if requested_model == 'openai-compatible':
        cfg = context.get('openai_compatible') if isinstance(context.get('openai_compatible'), dict) else {}
        model = str(cfg.get('model') or 'openai-compatible').strip()
        return model, f"Using OpenAI-compatible model: {model}"

    # Check 1: Cost budget threshold
    cost_percent_used = context.get('cost_percent_used', 0) or 0
    if cost_percent_used >= COST_THRESHOLD_FOR_HAIKU:
        return FALLBACK_MODEL, f"Using faster model (budget at {cost_percent_used:.1f}%)"

    # Check 2: Explicit model request in context
    if requested_model == 'haiku':
        return FALLBACK_MODEL, "Using faster model (user preference)"
    if requested_model == 'sonnet':
        return SONNET_MODEL, "Using Sonnet model (user preference)"
    if requested_model == 'opus':
        return DEFAULT_MODEL, "Using Opus model (user preference)"

    # Check 3: Complex query patterns -> always use Sonnet
    for pattern in COMPLEX_QUERY_PATTERNS:
        if pattern in query_lower:
            return DEFAULT_MODEL, "Using advanced model for complex task"

    # Check 4: Simple query patterns -> can use Haiku
    for pattern in SIMPLE_QUERY_PATTERNS:
        if pattern in query_lower:
            return FALLBACK_MODEL, "Using faster model for simple task"

    # Check 5: Very short queries are often simple
    word_count = len(query.split())
    if word_count <= 5 and '?' in query:
        return FALLBACK_MODEL, "Using faster model for quick question"

    # Check 6: Queries with attachments typically need more analysis
    if context.get('has_attachments', False):
        return DEFAULT_MODEL, "Using advanced model for file analysis"

    # Default: Use Sonnet for best quality
    return DEFAULT_MODEL, "Using advanced model"


def _summarize_tool_input(tool_name: str, tool_input: dict) -> str:
    """Create a short summary of tool input for logging."""
    try:
        if tool_name == 'python_execute':
            code = tool_input.get('code', '')
            lines = code.strip().split('\n')
            if len(lines) > 1:
                return f"{len(lines)} lines of code"
            elif code:
                return code[:50] + "..." if len(code) > 50 else code
            return "empty code"

        if tool_name == 'web_fetch':
            url = tool_input.get('url', '')
            return url[:60] + "..." if len(url) > 60 else url

        if tool_name in ('read_file', 'ocr_image'):
            path = tool_input.get('image_path', tool_input.get('path', tool_input.get('file_path', '')))
            import os
            return os.path.basename(path) if path else "unknown file"

        if tool_name == 'create_pdf':
            title = tool_input.get('title', 'untitled')
            images = tool_input.get('image_paths', [])
            if images:
                return f"Creating '{title}' with {len(images)} image(s)"
            return f"Creating '{title}'"

        if tool_name == 'convert_document':
            import os
            source = tool_input.get('input_path', '')
            fmt = tool_input.get('output_format', '?')
            return f"{os.path.basename(source) if source else '?'} -> {fmt}"

        if tool_name == 'create_docx':
            import os
            output = tool_input.get('output_path', '')
            return f"create {os.path.basename(output) if output else 'DOCX'}"

        if tool_name in ('google_calendar', 'gmail'):
            action = tool_input.get('action', '?')
            return f"action={action}"

        if tool_name == 'ffmpeg_process':
            op = tool_input.get('operation', '?')
            params = tool_input.get('params', {})
            params_str = json.dumps(params) if params else ''
            if len(params_str) > 100:
                params_str = params_str[:100] + '...'
            return f"{op}: {params_str}" if params_str else op

        # Generic fallback: include short scalar values so model formatting
        # mistakes are diagnosable without dumping large user content.
        parts = []
        for key, value in list(tool_input.items())[:4]:
            if isinstance(value, (str, int, float, bool)):
                shown = str(value)
                if len(shown) > 60:
                    shown = shown[:57] + '...'
                parts.append(f"{key}={shown}")
            else:
                parts.append(key)
        return "params: " + ", ".join(parts) if parts else "no params"
    except Exception:
        return "..."


def _summarize_tool_result(tool_name: str, result_str: str) -> str:
    """Create a short summary of tool result for logging."""
    try:
        length = len(result_str)
        if length > 500:
            return f"got {length} chars"
        elif length > 100:
            return result_str[:80] + "..."
        else:
            return result_str[:100]
    except Exception:
        return "..."


def self_improve(
    conversation: List[Dict[str, str]],
    current_prompt: str,
    api_key: str,
) -> dict:
    """
    Analyze a conversation and generate an improved system prompt.

    Uses extended thinking to deeply analyze what went well and what could
    be improved, then produces a refined system prompt.

    Args:
        conversation: List of {role, content} dicts from the chat
        current_prompt: The current system prompt text
        api_key: Claude API key

    Returns:
        Dict with 'improved_prompt' on success, or 'error'/'message' on failure
    """
    bridge = get_bridge()

    if not api_key:
        return {"error": True, "message": "API key not configured"}

    if not conversation:
        return {"error": True, "message": "No conversation to analyze"}

    bridge.log("Analyzing conversation for self-improvement...", level="info")

    # Format conversation as readable text
    conv_text = ""
    for msg in conversation:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        conv_text += f"[{role}]: {content}\n\n"

    # Build tool names list for context
    tool_names = [t["name"] for t in TOOLS_SCHEMA]
    tool_list_str = ", ".join(tool_names)

    # Build the meta-prompt
    meta_prompt = f"""You are analyzing a conversation between a user and an AI assistant called NavixMind.
Your task is to improve the system prompt that guides the assistant's behavior.

CURRENT SYSTEM PROMPT:
---
{current_prompt}
---

AVAILABLE TOOLS (the assistant has these tools via the API — the system prompt should reference them by name):
{tool_list_str}

CONVERSATION:
---
{conv_text}
---

Analyze the conversation carefully:
1. What did the assistant do well?
2. Where did the assistant fail, get confused, or could have been better?
3. What specific tools did the assistant misuse, fail to use, or use incorrectly?
4. What patterns, preferences, or needs does the user have?
5. What instructions could help the assistant handle similar situations better next time?

Now write an IMPROVED system prompt that:
- Keeps all working parts of the current prompt (especially the AVAILABLE TOOLS section)
- Adds specific instructions to fix the exact failures you observed in the conversation
- References tools BY NAME (e.g. "use google_calendar for calendar queries", not just "access calendar")
- Adds error-handling guidance for any errors that occurred (e.g. "if Google not connected, tell user to connect in Settings")
- Incorporates user preferences and patterns you noticed
- Stays concise — this runs on a mobile device
- Does NOT remove any tool names or capability descriptions from the current prompt

Output ONLY the improved system prompt text, nothing else. No preamble, no explanation."""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    body = {
        "model": DEFAULT_MODEL,
        "max_tokens": 16000,
        "thinking": {
            "type": "enabled",
            "budget_tokens": 10000,
        },
        "temperature": 1,
        "messages": [
            {"role": "user", "content": meta_prompt},
        ],
    }

    try:
        bridge.log("Calling Claude with extended thinking...", level="info")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=180,
        )

        if response.status_code != 200:
            error_body = response.json()
            error_msg = error_body.get("error", {}).get("message", "Unknown API error")
            bridge.log(f"Self-improve API error: {error_msg}", level="error")
            return {"error": True, "message": f"API error: {error_msg}"}

        result = response.json()

        # Record usage
        usage = result.get("usage", {})
        if usage:
            _record_usage(
                model=DEFAULT_MODEL,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                context={},
            )

        # Extract only text blocks (skip thinking blocks)
        content_blocks = result.get("content", [])
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))

        improved_prompt = "\n".join(text_parts).strip()

        if not improved_prompt:
            bridge.log("Self-improve returned empty response", level="warn")
            return {"error": True, "message": "No improved prompt generated"}

        bridge.log("System prompt improved successfully", level="info")
        return {"improved_prompt": improved_prompt}

    except requests.Timeout:
        bridge.log("Self-improve timed out", level="error")
        return {"error": True, "message": "Request timed out (180s). Try with a shorter conversation."}
    except requests.RequestException as e:
        bridge.log(f"Self-improve network error: {e}", level="error")
        return {"error": True, "message": f"Network error: {str(e)}"}
    except Exception as e:
        CrashLogger.log_error("self_improve", e)
        bridge.log(f"Self-improve exception: {e}", level="error")
        return {"error": True, "message": f"Unexpected error: {str(e)}"}

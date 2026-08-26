#!/usr/bin/env python3
from pathlib import Path

# The core v7 tool script was intentionally written as a deterministic source
# patch. Its cloud-prompt paragraph belongs in agent.py rather than tools/
# __init__.py, so strip that one paragraph before executing the rest.
source_path = Path('scripts/apply_iteration_v7_tools.py')
source = source_path.read_text()
start_marker = '# Static cloud prompt: describe the newly available structured tools as well.\n'
end_marker = 'p.write_text(text)\n\n\n# ---------------------------------------------------------------------------\n# Flutter Skill catalogue'
start = source.find(start_marker)
end = source.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('v7 tool runner could not isolate cloud-prompt paragraph')
source = source[:start] + 'p.write_text(text)\n\n\n# ---------------------------------------------------------------------------\n# Flutter Skill catalogue' + source[end + len(end_marker):]
exec(compile(source, str(source_path), 'exec'), {'__name__': '__main__'})

# Patch the actual static cloud SYSTEM_PROMPT. Local models use the dynamic
# Skill prompt from tools/__init__.py, so this affects cloud parity only.
p = Path('python/navixmind/agent.py')
text = p.read_text()
anchor = '- **write_file** — Write text content to a file (saved to device, available for download/sharing)\n'
addition = anchor + (
    '- **list_files** — List/discover files and directories, including recursive/pattern searches\n'
    '- **file_manage** — Create directories; copy, move, rename, delete, touch or test files/directories\n'
    '- **list_zip / extract_zip** — Inspect and safely extract ZIP archives\n'
    '- **pdf_manage** — Merge, split, extract/reorder/delete/rotate PDF pages\n'
    '- **image_compose** — Resize/convert/concat/overlay/crop/adjust/rotate/flip/filter images\n'
    '- **create_pptx / create_xlsx** — Create PowerPoint presentations and Excel workbooks\n'
)
if anchor not in text:
    raise SystemExit('v7 cloud prompt anchor missing in agent.py')
text = text.replace(anchor, addition, 1)
text = text.replace(
    '- **ffmpeg_process** — Process video/audio: trim, crop, resize, filter, extract audio/frame, convert.',
    '- **ffmpeg_process** — Process video/audio: trim, crop, resize, filter, extract audio/frame, convert, concatenate, mix audio, merge A/V, or use advanced custom FFmpeg.',
    1,
)
text = text.replace(
    '- **google_calendar** — Query or create Google Calendar events (list, create, delete)',
    '- **google_calendar** — Query or manage Google Calendar events (list, create, update, delete)',
    1,
)
p.write_text(text)
print('Applied v7 tools and cloud prompt in correct source files')

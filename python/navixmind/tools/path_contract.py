"""Canonical model-facing path contract for RastaCoder.

The model works in a logical namespace. Physical Android/app paths are execution
implementation details. Small models may emit virtual absolute paths such as
/, /workspace, /notes.txt or /folder/result.pdf; those are repaired before a
tool touches the Android filesystem.
"""
from __future__ import annotations

import os
from typing import Optional

from ..bridge import ToolError


ANDROID_LOGICAL_ROOTS = {
    'downloads': '/storage/emulated/0/Download',
    'documents': '/storage/emulated/0/Documents',
    'pictures': '/storage/emulated/0/Pictures',
    'screenshots': '/storage/emulated/0/Pictures/Screenshots',
    'camera': '/storage/emulated/0/DCIM/Camera',
}

# V17 local-tool recovery invariant:
# A model-facing bare slash means "the root of my workspace", never Android's
# filesystem root. The same logical rule extends to invented leading-slash
# children such as /notes.txt: if they are not already-real trusted files or
# documented Android public roots, they live under the app workspace.
WORKSPACE_ALIASES = {
    '', '.', './', '/', 'workspace', 'workspace/', 'output', 'output/',
    '/workspace', '/workspace/', '/output', '/output/',
}


def _safe_join(base: str, remainder: str, label: str) -> str:
    base = os.path.normpath(base)
    remainder = str(remainder or '').replace('\\', '/').strip()
    while remainder.startswith('./'):
        remainder = remainder[2:]
    if not remainder:
        return base
    if remainder == '..' or remainder.startswith('../'):
        raise ToolError(f'Path escapes {label}: {remainder}')
    target = os.path.normpath(os.path.join(base, remainder))
    try:
        if os.path.commonpath([base, target]) != base:
            raise ToolError(f'Path escapes {label}: {remainder}')
    except ValueError as exc:
        raise ToolError(f'Invalid path for {label}: {remainder}') from exc
    return target


def _inside(base: str, target: str) -> bool:
    base = os.path.normpath(str(base))
    target = os.path.normpath(str(target))
    try:
        return os.path.commonpath([base, target]) == base
    except ValueError:
        return False


def _strip_virtual_workspace_prefix(raw: str) -> Optional[str]:
    value = raw.replace('\\', '/').strip()
    lower = value.lower()
    if lower in WORKSPACE_ALIASES:
        return ''
    for prefix in ('workspace/', 'output/', '/workspace/', '/output/'):
        if lower.startswith(prefix):
            return value[len(prefix):]
    return None


def resolve_model_path(value: str, workspace_root: str, allow_android_roots: bool = True) -> str:
    """Resolve one model-facing path into an execution path.

    Rules are intentionally biased toward the local model's logical namespace:
    * '.', '/', workspace and output aliases resolve to the app workspace.
    * downloads/documents/pictures/screenshots/camera resolve to documented
      Android public roots when input access is allowed.
    * real files which already exist are preserved. This retains the V12
      attachment contract after the agent has mapped a basename to its actual
      temporary/app path.
    * absolute paths under the workspace or documented Android roots remain
      real execution paths on later tool turns.
    * every other leading-slash path is interpreted as workspace-relative.
      Thus /foo.txt and /folder/foo.txt can never fall through to Android '/'.

    The executor still enforces tool-level access and Android permissions; this
    function only prevents a small model's virtual-root notation from becoming
    an accidental operating-system root request.
    """
    root = os.path.normpath(str(workspace_root))
    raw = str(value or '').strip().replace('\\', '/')

    virtual_remainder = _strip_virtual_workspace_prefix(raw)
    if virtual_remainder is not None:
        return _safe_join(root, virtual_remainder, 'workspace root')

    probe = raw.lstrip('/')
    first, sep, remainder = probe.partition('/')
    first_key = first.lower()
    if allow_android_roots and first_key in ANDROID_LOGICAL_ROOTS:
        return _safe_join(
            ANDROID_LOGICAL_ROOTS[first_key],
            remainder if sep else '',
            f'{first_key} root',
        )

    if os.path.isabs(raw):
        normalized = os.path.normpath(raw)
        if _inside(root, normalized):
            return normalized
        if allow_android_roots and any(_inside(base, normalized) for base in ANDROID_LOGICAL_ROOTS.values()):
            return normalized
        # V12 compatibility: basename->attachment mapping happens before this
        # resolver. Preserve an already-real file so attached inputs outside the
        # workspace continue to work. Do not preserve arbitrary absolute
        # directories such as /data or /system merely because they exist.
        if os.path.isfile(normalized):
            return normalized
        return _safe_join(root, normalized.lstrip('/'), 'workspace root')

    while raw.startswith('./'):
        raw = raw[2:]
    return _safe_join(root, raw, 'workspace root')


def resolve_output_path(value: str, workspace_root: str) -> str:
    """Resolve generated outputs through the virtual workspace contract."""
    return resolve_model_path(value, workspace_root, allow_android_roots=False)


def resolve_list_path(value: Optional[str], workspace_root: str, legacy_directory: str = 'output') -> str:
    """Resolve list_files target, retaining legacy directory compatibility."""
    raw = str(value or '').strip().replace('\\', '/')
    directory_key = str(legacy_directory or 'output').strip().lower()
    if not raw:
        if directory_key in {'output', 'workspace', ''}:
            return os.path.normpath(workspace_root)
        if directory_key in ANDROID_LOGICAL_ROOTS:
            return os.path.normpath(ANDROID_LOGICAL_ROOTS[directory_key])
        raw = directory_key

    # Bare '/' is deliberately interpreted as the logical workspace root.
    if raw == '/':
        return os.path.normpath(workspace_root)

    # Legacy directory=<android-root> plus relative path keeps that root.
    if directory_key in ANDROID_LOGICAL_ROOTS and not os.path.isabs(raw):
        probe = raw.lstrip('./')
        first = probe.partition('/')[0].lower()
        if first not in ANDROID_LOGICAL_ROOTS and _strip_virtual_workspace_prefix(raw) is None:
            return _safe_join(ANDROID_LOGICAL_ROOTS[directory_key], probe, f'{directory_key} root')

    return resolve_model_path(raw, workspace_root, allow_android_roots=True)


def logicalize_path(value: str, workspace_root: str) -> str:
    """Convert a physical execution path back to the model-facing logical namespace."""
    raw = os.path.normpath(str(value or ''))
    root = os.path.normpath(str(workspace_root))
    try:
        if os.path.commonpath([root, raw]) == root:
            rel = os.path.relpath(raw, root).replace('\\', '/')
            return '.' if rel == '.' else rel
    except ValueError:
        pass
    for logical, physical in ANDROID_LOGICAL_ROOTS.items():
        base = os.path.normpath(physical)
        try:
            if os.path.commonpath([base, raw]) == base:
                rel = os.path.relpath(raw, base).replace('\\', '/')
                return logical if rel == '.' else f'{logical}/{rel}'
        except ValueError:
            continue
    return os.path.basename(raw) or '.'

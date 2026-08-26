"""Canonical model-facing path contract for RastaCoder.

The model works in a logical namespace. Physical Android/app paths are execution
implementation details. Small models may still emit common virtual absolute
aliases such as /workspace; those aliases are repaired deterministically.
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

WORKSPACE_ALIASES = {
    '', '.', './', 'workspace', 'workspace/', 'output', 'output/',
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
    """Resolve one model-facing path while preserving trusted real absolute paths.

    Virtual workspace aliases are interpreted before the generic absolute-path
    branch. This is the key invariant missing in V11.
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
        # Only treat a leading-slash absolute path as a logical alias when the
        # first segment is one of our documented model-facing Android roots.
        if not raw.startswith('/') or raw.lower() == '/' + probe.lower():
            return _safe_join(ANDROID_LOGICAL_ROOTS[first_key], remainder if sep else '', f'{first_key} root')

    # Attached files and already-resolved real Android/app paths reach here as
    # genuine absolute paths and must remain usable.
    if os.path.isabs(raw):
        return os.path.normpath(raw)

    while raw.startswith('./'):
        raw = raw[2:]
    return _safe_join(root, raw, 'workspace root')


def resolve_output_path(value: str, workspace_root: str) -> str:
    """Resolve generated output paths. Virtual /workspace and /output are safe aliases."""
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
    # Do not teach the model arbitrary physical filesystem roots from list
    # results. A basename remains actionable only when an attachment/file map
    # supplied it; arbitrary external traversal is intentionally not promoted.
    return os.path.basename(raw) or '.'

"""Canonical model-facing path contract for RastaCoder.

The model works in a logical namespace. Physical Android/app paths are execution
implementation details. Small models may emit virtual absolute aliases such as
/ or /workspace; those aliases are repaired deterministically before any tool
touches the Android filesystem.
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
# A model-facing bare slash means "the root of my workspace", never the Android
# process/filesystem root. Small local models commonly express a logical root as
# "/" even when the schema example says ".". Treating it as a real absolute
# path causes Android EACCES and can break every path-taking local tool.
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

    Virtual workspace aliases are interpreted before the generic absolute-path
    branch. In particular, V17 locks bare "/" to the app workspace root so an
    on-device model cannot accidentally request Android's filesystem root when
    it merely means "my workspace root".

    Genuine absolute paths are still preserved for trusted attachment paths and
    already-resolved internal execution paths; the agent/file-map layer is what
    supplies those values. Documented Android roots remain available through
    their logical aliases (downloads/, documents/, pictures/, etc.).
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
    # genuine absolute paths and must remain usable. Bare '/' never reaches this
    # branch because it is a workspace alias above.
    if os.path.isabs(raw):
        return os.path.normpath(raw)

    while raw.startswith('./'):
        raw = raw[2:]
    return _safe_join(root, raw, 'workspace root')


def resolve_output_path(value: str, workspace_root: str) -> str:
    """Resolve generated output paths. /, /workspace and /output are workspace aliases."""
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
    # Keep this explicit guard in addition to WORKSPACE_ALIASES so a future
    # alias refactor cannot silently reintroduce the V16 EACCES regression.
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
    # Do not teach the model arbitrary physical filesystem roots from list
    # results. A basename remains actionable only when an attachment/file map
    # supplied it; arbitrary external traversal is intentionally not promoted.
    return os.path.basename(raw) or '.'

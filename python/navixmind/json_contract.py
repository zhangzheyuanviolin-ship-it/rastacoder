"""Canonical JSON-safe boundary for model/tool/diagnostic transport.

Tool implementations are free to use ordinary Python values internally. Anything
that crosses the model, Flutter bridge, diagnostic, session or JSON-RPC boundary
must pass through this module first. This prevents one tool returning a set,
tuple, datetime, Path, bytes or third-party scalar from crashing the whole turn.
"""
from __future__ import annotations

import base64
import json
import math
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


def to_json_safe(value: Any, *, _seen: set[int] | None = None) -> Any:
    """Recursively convert arbitrary values into strict JSON-compatible values.

    The conversion is deterministic for sets/frozensets so diagnostics and model
    context remain stable across runs. Cycles are represented as a short marker
    instead of recursing forever.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return str(value)
    if isinstance(value, Decimal):
        if value.is_finite():
            return float(value)
        return str(value)
    if isinstance(value, Enum):
        return to_json_safe(value.value, _seen=_seen)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return "base64:" + base64.b64encode(value).decode("ascii")

    if _seen is None:
        _seen = set()
    ident = id(value)
    if ident in _seen:
        return "[cyclic-reference]"

    if isinstance(value, dict):
        _seen.add(ident)
        try:
            return {
                str(key): to_json_safe(item, _seen=_seen)
                for key, item in value.items()
            }
        finally:
            _seen.discard(ident)

    if isinstance(value, (list, tuple)):
        _seen.add(ident)
        try:
            return [to_json_safe(item, _seen=_seen) for item in value]
        finally:
            _seen.discard(ident)

    if isinstance(value, (set, frozenset)):
        _seen.add(ident)
        try:
            items = [to_json_safe(item, _seen=_seen) for item in value]
        finally:
            _seen.discard(ident)
        # Sets have already lost source ordering. Make the unavoidable recovery
        # deterministic instead of relying on hash iteration order.
        return sorted(
            items,
            key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, default=str),
        )

    # Common numpy/pandas/third-party scalar contract without importing them.
    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            unboxed = item_method()
            if unboxed is not value:
                return to_json_safe(unboxed, _seen=_seen)
        except Exception:
            pass

    iso_method = getattr(value, "isoformat", None)
    if callable(iso_method):
        try:
            return str(iso_method())
        except Exception:
            pass

    return str(value)


def json_dumps_safe(value: Any, **kwargs: Any) -> str:
    """Strict JSON dump after canonical recursive conversion."""
    options = {"ensure_ascii": False, "allow_nan": False}
    options.update(kwargs)
    return json.dumps(to_json_safe(value), **options)


def assert_json_safe(value: Any) -> None:
    """Raise if a value cannot round-trip through the strict boundary."""
    encoded = json_dumps_safe(value)
    json.loads(encoded)

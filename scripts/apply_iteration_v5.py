#!/usr/bin/env python3
"""Apply the reviewed RastaCoder v5 patch.

The implementation payload is split only to keep GitHub connector writes small
and verifiable. The decompressed source is SHA-256 checked before execution.
"""
from __future__ import annotations

import base64
import hashlib
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_SHA256 = "9591cf7c753815c6991f26355eb881c8e512b202b481b002919223d2c1b072a5"
PARTS = [ROOT / "scripts" / f"v5_payload_{index:02d}.b64" for index in range(7)]

encoded = "".join(part.read_text(encoding="utf-8").strip() for part in PARTS)
source = zlib.decompress(base64.b64decode(encoded)).decode("utf-8")
digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
if digest != EXPECTED_SOURCE_SHA256:
    raise SystemExit(
        f"RastaCoder v5 patch integrity failure: expected {EXPECTED_SOURCE_SHA256}, got {digest}"
    )

code = compile(source, "<rastacoder-v5-reviewed-patch>", "exec")
exec(code, {"__name__": "__main__", "__file__": str(Path(__file__).resolve())})

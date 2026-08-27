#!/usr/bin/env python3
"""Prepare the verified curl-cffi Android ARM64 wheel for Chaquopy.

curl-cffi 0.16.2 publishes a real CPython 3.13 Android ARM64 wheel, but its
package metadata requires cffi>=2.0.0. V15's no-APK ABI probe proved the same
0.16.2 wrapper imports and performs HTTPS Chrome impersonation correctly with
cffi/_cffi_backend 1.17.1. Chaquopy currently publishes cffi 1.17.1 for this
Android/Python target, so this script changes only that dependency metadata.
All executable/package payload bytes remain identical to the official wheel.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR_DIR = ROOT / "android" / "app" / "vendor"
WHEEL_NAME = "curl_cffi-0.16.2-cp313-cp313-android_24_arm64_v8a.whl"
OUTPUT_WHEEL = VENDOR_DIR / WHEEL_NAME
SOURCE_URL = (
    "https://github.com/lexiforest/curl_cffi/releases/download/v0.16.2/"
    + WHEEL_NAME
)
SOURCE_SHA256 = "58598186eccd24d2b2e126f945d8a5bdca0066a2789052023d3d8370ebadca30"
OLD_REQUIREMENT_RE = re.compile(r"^Requires-Dist:\s*cffi\s*>=\s*2(?:\.0(?:\.0)?)?\s*$", re.I)
NEW_REQUIREMENT = "Requires-Dist: cffi>=1.17.1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_hash(data: bytes) -> str:
    raw = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def download_official() -> bytes:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "RastaCoder-V15-wheel-preparer"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    actual = digest(data)
    if actual != SOURCE_SHA256:
        raise SystemExit(f"Official curl-cffi wheel SHA-256 mismatch: {actual}")
    return data


def prepare() -> Path:
    source_bytes = download_official()
    with tempfile.TemporaryDirectory(prefix="v15-curl-cffi-") as td:
        source_path = Path(td) / WHEEL_NAME
        source_path.write_bytes(source_bytes)

        with zipfile.ZipFile(source_path, "r") as zin:
            infos = zin.infolist()
            payloads = {info.filename: zin.read(info.filename) for info in infos}

        metadata_names = [name for name in payloads if name.endswith(".dist-info/METADATA")]
        record_names = [name for name in payloads if name.endswith(".dist-info/RECORD")]
        if len(metadata_names) != 1 or len(record_names) != 1:
            raise SystemExit("Unexpected curl-cffi wheel dist-info layout")
        metadata_name = metadata_names[0]
        record_name = record_names[0]

        metadata = payloads[metadata_name].decode("utf-8")
        lines = metadata.splitlines()
        replaced = 0
        new_lines = []
        for line in lines:
            if OLD_REQUIREMENT_RE.match(line.strip()):
                new_lines.append(NEW_REQUIREMENT)
                replaced += 1
            else:
                new_lines.append(line)
        if replaced != 1:
            raise SystemExit(f"Expected exactly one cffi>=2 metadata requirement, found {replaced}")
        new_metadata = ("\n".join(new_lines) + "\n").encode("utf-8")
        payloads[metadata_name] = new_metadata

        # Rebuild RECORD according to the wheel spec after the one metadata edit.
        record_buffer = io.StringIO(newline="")
        writer = csv.writer(record_buffer, lineterminator="\n")
        for info in infos:
            name = info.filename
            if name == record_name:
                continue
            data = payloads[name]
            writer.writerow([name, record_hash(data), str(len(data))])
        writer.writerow([record_name, "", ""])
        payloads[record_name] = record_buffer.getvalue().encode("utf-8")

        VENDOR_DIR.mkdir(parents=True, exist_ok=True)
        tmp_out = Path(td) / ("patched-" + WHEEL_NAME)
        with zipfile.ZipFile(tmp_out, "w") as zout:
            for info in infos:
                cloned = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                cloned.compress_type = info.compress_type
                cloned.comment = info.comment
                cloned.extra = info.extra
                cloned.create_system = info.create_system
                cloned.create_version = info.create_version
                cloned.extract_version = info.extract_version
                cloned.flag_bits = info.flag_bits
                cloned.internal_attr = info.internal_attr
                cloned.external_attr = info.external_attr
                cloned.volume = info.volume
                zout.writestr(cloned, payloads[info.filename])

        # Prove every original payload member except METADATA/RECORD is byte-identical.
        with zipfile.ZipFile(source_path, "r") as original, zipfile.ZipFile(tmp_out, "r") as patched:
            if original.namelist() != patched.namelist():
                raise SystemExit("Patched wheel changed the member layout")
            for name in original.namelist():
                if name in {metadata_name, record_name}:
                    continue
                if original.read(name) != patched.read(name):
                    raise SystemExit(f"Patched wheel changed payload bytes: {name}")
            patched_metadata = patched.read(metadata_name).decode("utf-8")
            if NEW_REQUIREMENT not in patched_metadata or "cffi>=2" in patched_metadata.lower().replace(" ", ""):
                raise SystemExit("Patched wheel metadata verification failed")

        shutil.copyfile(tmp_out, OUTPUT_WHEEL)

    print(f"Prepared {OUTPUT_WHEEL.relative_to(ROOT)}")
    print(f"Official source SHA-256: {SOURCE_SHA256}")
    print(f"Prepared wheel SHA-256: {digest(OUTPUT_WHEEL.read_bytes())}")
    return OUTPUT_WHEEL


if __name__ == "__main__":
    prepare()

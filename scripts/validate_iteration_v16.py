#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def source(path):
    return (ROOT / path).read_text(encoding='utf-8')


from navixmind.tools import TOOLS_SCHEMA
from navixmind.tools.code_executor import execute_python
from navixmind.tools.documents import read_xlsx
from navixmind.tools.extended_tools import create_xlsx

names = [tool.get('name') for tool in TOOLS_SCHEMA]
require(len(set(names)) == 37, f'Expected 37 canonical local functions, got {len(set(names))}')

# 1) SafePathFacade: common read-only probes work inside OUTPUT_DIR, while an
# arbitrary Android/host path remains opaque to model-generated Python.
with tempfile.TemporaryDirectory() as td:
    code = '''
from os import path
p = path.join(OUTPUT_DIR, "probe.txt")
with open(p, "w") as f:
    f.write("v16-probe")
print(path.exists("."))
print(path.isdir("."))
print(path.exists("probe.txt"))
print(path.isfile("probe.txt"))
print(path.getsize("probe.txt"))
print(path.getmtime("probe.txt") > 0)
'''
    result = execute_python(code, output_dir=td)
    require(result['success'] is True, f'Safe os.path probes failed: {result}')
    lines = [line.strip() for line in result['output'].splitlines() if line.strip()]
    require(lines[-6:] == ['True', 'True', 'True', 'True', '9', 'True'], f'Unexpected probe output: {lines}')

    blocked = execute_python('import os.path as path\nprint(path.exists("/etc/passwd"))', output_dir=td)
    require(blocked['success'] is False, 'Arbitrary filesystem probe unexpectedly succeeded')
    require('Filesystem probing' in (blocked.get('error') or ''), f'Unexpected blocked-probe error: {blocked}')

# 2) create_xlsx/read_xlsx exact roundtrip for the cloud regression matrix.
expected = [
    ['Model', 'Year', 'Vendor'],
    ['GPT-4', 2023, 'OpenAI'],
    ['Claude', 2024, 'Anthropic'],
]
with tempfile.TemporaryDirectory() as td:
    root = Path(td)

    canonical = root / 'canonical.xlsx'
    created = create_xlsx(str(canonical), sheets=[{'name': 'Models', 'rows': expected}])
    require(created.get('verified') is True, f'create_xlsx did not self-verify: {created}')
    result = read_xlsx(str(canonical), sheet='Models', range='A1:C3', extract='values')
    rows = result['sheets']['Models']['rows']
    require(rows == expected, f'Canonical create/read XLSX mismatch: {rows!r}')

    compat = root / 'compat.xlsx'
    created = create_xlsx(
        str(compat),
        sheets=[{'sheet_name': 'Models', 'data': [{'item': row} for row in expected]}],
    )
    require(created.get('verified') is True, f'Compatibility create_xlsx did not verify: {created}')
    result = read_xlsx(str(compat), sheet='Models', range='A1:C3', extract='values')
    rows = result['sheets']['Models']['rows']
    require(rows == expected, f'sheet_name/data/item compatibility mismatch: {rows!r}')

    records = root / 'records.xlsx'
    record_input = [
        {'Model': 'GPT-4', 'Year': 2023, 'Vendor': 'OpenAI'},
        {'Model': 'Claude', 'Year': 2024, 'Vendor': 'Anthropic'},
    ]
    create_xlsx(str(records), sheets=[{'name': 'Records', 'rows': record_input}])
    result = read_xlsx(str(records), sheet='Records', range='A1:C3', extract='values')
    require(result['sheets']['Records']['rows'] == expected, 'Object-record XLSX normalization failed')

# 3) curl-cffi native loader: source patch handles OSError/dlopen cleanly, and
# the native preparer packages every wheel-private hashed DT_NEEDED member.
media = source('python/navixmind/tools/media.py')
require('except (ImportError, OSError) as exc:' in media, 'download_media does not catch native dlopen failures')
require('Browser impersonation native runtime is incomplete' in media, 'download_media native-runtime error contract missing')

native_prep = source('scripts/prepare_curl_cffi_native_companion_v16.py')
require('PRIVATE_NEEDED_RE' in native_prep, 'Generic wheel-private DT_NEEDED detection missing')
require("re.findall(PRIVATE_NEEDED_RE, wrapper)" in native_prep, 'Native companion discovery is not driven by wrapper dependencies')
require('JNI_DIR / needed_name' in native_prep, 'Native companion is not copied under its exact DT_NEEDED filename')
require("payload.startswith(b'\\x7fELF')" in native_prep, 'Native companion ELF verification missing')

# 4) Current fixed MLC runtime is intentionally limited to the five model
# libraries proven by the binary probe. Do not silently add download entries
# which have no compiled model library in libtvm4j_runtime_packed.so.
expected_ids = {
    'qwen3_q4f16_0_744427a6c2d881a41e79d0bfb2a540dc',
    'qwen2_q4f16_0_ce81ef8767dfb3f843c79deb0b3f66fc',
    'qwen2_q4f16_0_1be22ffdc6429c5019af9af8dae22086',
    'qwen2_q4f16_0_ecc0cde57625a5817018e8d547361bb3',
    'ministral3_q4f16_0_68e08feb72d08c3826f6a0b3623b81fc',
}
registry = source('lib/core/models/model_registry.dart')
registry_ids = set(re.findall(r"mlcModelLib:\s*'([^']+)'", registry))
require(registry_ids == expected_ids, f'Unverified or missing model registry entries: {registry_ids}')

asset_cfg = json.loads(source('android/mlc4j/src/main/assets/mlc-app-config.json'))
asset_ids = {item['model_lib'] for item in asset_cfg['model_list']}
require(asset_ids == expected_ids, f'MLC asset config diverged from proven runtime IDs: {asset_ids}')

package_cfg = json.loads(source('mlc-package-config.json'))
package_ids = {item['model_lib'] for item in package_cfg['model_list']}
require(package_ids == expected_ids, f'MLC package config diverged from proven runtime IDs: {package_ids}')

channel = source('android/app/src/main/kotlin/ai/navixmind/services/MLCInferenceChannel.kt')
require('chatModule.reload(modelPath, modelLib)' in channel, 'Android runtime no longer reloads by explicit model_lib')

print('V16 validation passed: safe os.path probes, exact XLSX roundtrips, curl-cffi native loader hardening, and verified MLC model-set gates are green.')

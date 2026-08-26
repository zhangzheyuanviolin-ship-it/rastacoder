#!/usr/bin/env python3
from pathlib import Path
p = Path('python/navixmind/tools/documents.py')
text = p.read_text()
old = '''            elif action == "delete_sheet":
                name = params.get("name")
                if name in wb.sheetnames:
                    del wb[name]
                    applied += 1
'''
new = '''            elif action == "delete_sheet":
                name = params.get("name")
                if name in wb.sheetnames and len(wb.sheetnames) > 1:
                    del wb[name]
                    applied += 1
'''
if old not in text:
    raise SystemExit('v7 preoffice anchor missing')
p.write_text(text.replace(old, new, 1))
print('Normalized XLSX delete_sheet anchor for v7 office expansion')

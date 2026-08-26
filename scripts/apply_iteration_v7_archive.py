#!/usr/bin/env python3
from pathlib import Path

p = Path('python/navixmind/tools/documents.py')
text = p.read_text()
old = '''        # Verify all files exist before creating the archive
        for fpath in file_paths:
            if not os.path.isfile(fpath):
                raise ToolError(f"File not found: {fpath}")

        # Track basenames to handle duplicates
        seen_names = {}
        zip_compression = compression_map[compression]

        with zipfile.ZipFile(output_path, 'w', compression=zip_compression) as zf:
            for fpath in file_paths:
                basename = os.path.basename(fpath)

                # Handle duplicate basenames by appending a counter
                if basename in seen_names:
                    seen_names[basename] += 1
                    name, ext = os.path.splitext(basename)
                    arcname = f"{name}_{seen_names[basename]}{ext}"
                else:
                    seen_names[basename] = 0
                    arcname = basename

                zf.write(fpath, arcname)
'''
new = '''        # Verify all inputs exist. V7 accepts both files and directories.
        for fpath in file_paths:
            if not os.path.exists(fpath):
                raise ToolError(f"File or directory not found: {fpath}")

        # Track top-level basenames to handle collisions.
        seen_names = {}
        zip_compression = compression_map[compression]

        with zipfile.ZipFile(output_path, 'w', compression=zip_compression) as zf:
            for fpath in file_paths:
                basename = os.path.basename(os.path.normpath(fpath)) or 'item'
                if basename in seen_names:
                    seen_names[basename] += 1
                    root_name = f"{basename}_{seen_names[basename]}"
                else:
                    seen_names[basename] = 0
                    root_name = basename

                if os.path.isdir(fpath):
                    wrote_any = False
                    for root, dirs, files in os.walk(fpath):
                        rel_root = os.path.relpath(root, fpath)
                        archive_root = root_name if rel_root == '.' else os.path.join(root_name, rel_root)
                        if not files and not dirs:
                            zf.writestr(archive_root.rstrip('/') + '/', b'')
                        for filename in files:
                            source = os.path.join(root, filename)
                            arcname = os.path.join(archive_root, filename)
                            zf.write(source, arcname)
                            wrote_any = True
                    if not wrote_any:
                        zf.writestr(root_name.rstrip('/') + '/', b'')
                else:
                    name, ext = os.path.splitext(root_name)
                    if seen_names[basename] > 0:
                        arcname = f"{name}{ext}"
                    else:
                        arcname = root_name
                    zf.write(fpath, arcname)
'''
if old not in text:
    raise SystemExit('v7 archive create_zip anchor missing')
p.write_text(text.replace(old, new, 1))

p = Path('python/navixmind/tools/__init__.py')
text = p.read_text()
text = text.replace(
    '"description": "List of file paths to include in the archive"',
    '"description": "List of file or directory paths to include recursively in the archive"',
    1,
)
p.write_text(text)
print('Applied v7 ZIP file+directory creation support')

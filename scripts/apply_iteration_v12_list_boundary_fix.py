from pathlib import Path


path = Path('python/navixmind/tools/__init__.py')
text = path.read_text(encoding='utf-8')
marker = '# RASTACODER_V12_PRESERVE_LIST_LOGICAL_PATH'
if marker not in text:
    old = '''    # Resolve every model-facing relative file path against the same workspace root.\n    output_dir = context.get('output_dir')\n    if output_dir:\n        _resolve_workspace_input_paths(args, output_dir)\n        _resolve_output_paths(args, output_dir)\n'''
    new = '''    # Resolve every model-facing relative file path against the same workspace root.\n    output_dir = context.get('output_dir')\n    if output_dir:\n        # RASTACODER_V12_PRESERVE_LIST_LOGICAL_PATH\n        # list_files owns its logical-path -> physical-path translation via\n        # resolve_list_path(_output_dir). Keeping its path logical here is\n        # essential: requested_path is later returned to the model and must\n        # remain '.', 'folder/sub', 'downloads/...', etc., never the private\n        # Android/app filesystem root. All other tools keep the universal\n        # input resolver because their implementations consume physical paths.\n        if tool_name != 'list_files':\n            _resolve_workspace_input_paths(args, output_dir)\n        _resolve_output_paths(args, output_dir)\n'''
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Expected one execute_tool workspace resolver anchor, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

print('Applied RastaCoder v12 list_files logical-boundary fix.')

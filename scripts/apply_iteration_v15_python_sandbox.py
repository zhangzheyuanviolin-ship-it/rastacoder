from pathlib import Path

ROOT = Path('.')


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def replace_once(path, old, new):
    text = read(path)
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'V15 anchor not found in {path}: {old[:120]!r}')
    write(path, text.replace(old, new, 1))


path = 'python/navixmind/tools/code_executor.py'

safe_facades = r'''class _SafePathFacade:
    """Pure path-string operations only; no filesystem probing or process APIs."""
    join = staticmethod(_os.path.join)
    basename = staticmethod(_os.path.basename)
    dirname = staticmethod(_os.path.dirname)
    split = staticmethod(_os.path.split)
    splitext = staticmethod(_os.path.splitext)
    normpath = staticmethod(_os.path.normpath)
    isabs = staticmethod(_os.path.isabs)
    commonpath = staticmethod(_os.path.commonpath)
    commonprefix = staticmethod(_os.path.commonprefix)
    relpath = staticmethod(_os.path.relpath)


class _SafeOSFacade:
    path = _SafePathFacade()


class _SafeImportlibMetadataFacade:
    @staticmethod
    def version(distribution_name):
        from importlib import metadata
        return metadata.version(str(distribution_name))


class _SafeImportlibFacade:
    metadata = _SafeImportlibMetadataFacade()


'''
replace_once(path, 'class SafeBuiltins:\n', safe_facades + 'class SafeBuiltins:\n')

replace_once(
    path,
    '''    @staticmethod\n    def _safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):\n        """Safe import that checks against whitelist."""\n        top_level = name.split('.')[0]\n\n        if top_level in BLOCKED_MODULES:\n            raise SecurityError(f"Import of '{name}' is not allowed for security reasons")\n\n        if top_level not in SAFE_MODULES:\n            raise SecurityError(\n                f"Import of '{name}' is not allowed. "\n                f"Available modules: {', '.join(sorted(SAFE_MODULES))}"\n            )\n\n        # Use the real __import__\n        import builtins\n        return builtins.__import__(name, globals, locals, fromlist, level)''',
    '''    @staticmethod\n    def _safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):\n        """Safe import with tiny facades for os.path and importlib.metadata."""\n        requested = str(name)\n        requested_from = tuple(fromlist or ())\n        if requested == 'os.path':\n            return _SafePathFacade() if requested_from else _SafeOSFacade()\n        if requested == 'os' and requested_from and set(requested_from) <= {'path'}:\n            return _SafeOSFacade()\n        if requested == 'importlib.metadata':\n            return _SafeImportlibMetadataFacade() if requested_from else _SafeImportlibFacade()\n        if requested == 'importlib' and requested_from and set(requested_from) <= {'metadata'}:\n            return _SafeImportlibFacade()\n        top_level = requested.split('.')[0]\n        if top_level in BLOCKED_MODULES:\n            raise SecurityError(f"Import of '{requested}' is not allowed for security reasons")\n        if top_level not in SAFE_MODULES:\n            raise SecurityError(\n                f"Import of '{requested}' is not allowed. "\n                f"Available modules: {', '.join(sorted(SAFE_MODULES))}"\n            )\n        import builtins\n        return builtins.__import__(requested, globals, locals, fromlist, level)''',
)

replace_once(
    path,
    '''    @classmethod\n    def _safe_open(cls, file, mode='r', *args, **kwargs):\n        """Safe open that only allows reading specific files and writing to output_dir."""\n        file_str = str(file)\n\n        # Check write modes\n        if 'w' in mode or 'a' in mode or 'x' in mode or '+' in mode:\n            # Allow writes only inside output_dir\n            if cls._output_dir and file_str.startswith(cls._output_dir):\n                import builtins\n                return builtins.open(file, mode, *args, **kwargs)\n            raise SecurityError("Writing files is not allowed outside the output directory.")\n\n        # Check if file is in allowed paths\n        if not any(file_str == allowed or file_str.startswith(allowed) for allowed in cls._allowed_paths):\n            raise SecurityError(\n                f"Reading '{file}' is not allowed. "\n                f"Only files explicitly provided by the user can be read."\n            )\n\n        # Use the real open\n        import builtins\n        return builtins.open(file, mode, *args, **kwargs)''',
    '''    @classmethod\n    def _safe_open(cls, file, mode='r', *args, **kwargs):\n        """Allow user-provided inputs plus files created under OUTPUT_DIR."""\n        file_real = _os.path.realpath(str(file))\n\n        def within(candidate: str, root: str) -> bool:\n            if not root:\n                return False\n            root_real = _os.path.realpath(str(root))\n            try:\n                return _os.path.commonpath([candidate, root_real]) == root_real\n            except ValueError:\n                return False\n\n        is_write = any(flag in mode for flag in ('w', 'a', 'x', '+'))\n        if is_write:\n            if cls._output_dir and within(file_real, cls._output_dir):\n                import builtins\n                return builtins.open(file_real, mode, *args, **kwargs)\n            raise SecurityError("Writing files is not allowed outside the output directory.")\n\n        allowed_input = any(\n            file_real == _os.path.realpath(str(allowed))\n            or (_os.path.isdir(str(allowed)) and within(file_real, str(allowed)))\n            for allowed in cls._allowed_paths\n        )\n        generated_output = cls._output_dir and within(file_real, cls._output_dir)\n        if not allowed_input and not generated_output:\n            raise SecurityError(\n                f"Reading '{file}' is not allowed. Only user-provided files and files "\n                "created inside OUTPUT_DIR can be read."\n            )\n        import builtins\n        return builtins.open(file_real, mode, *args, **kwargs)''',
)

replace_once(
    path,
    '''            top_level = alias.name.split('.')[0]\n            if top_level in BLOCKED_MODULES:\n                self.errors.append(f"Import of '{alias.name}' is not allowed")''',
    '''            top_level = alias.name.split('.')[0]\n            if alias.name not in {'os.path', 'importlib.metadata'} and top_level in BLOCKED_MODULES:\n                self.errors.append(f"Import of '{alias.name}' is not allowed")''',
)
replace_once(
    path,
    '''            top_level = node.module.split('.')[0]\n            if top_level in BLOCKED_MODULES:\n                self.errors.append(f"Import from '{node.module}' is not allowed")''',
    '''            top_level = node.module.split('.')[0]\n            names = {alias.name for alias in node.names}\n            safe_blocked_subset = (\n                (node.module == 'os' and names <= {'path'})\n                or node.module == 'os.path'\n                or (node.module == 'importlib' and names <= {'metadata'})\n                or node.module == 'importlib.metadata'\n            )\n            if top_level in BLOCKED_MODULES and not safe_blocked_subset:\n                self.errors.append(f"Import from '{node.module}' is not allowed")''',
)
replace_once(
    path,
    "                                 '__name__', '__doc__'):",
    "                                 '__name__', '__doc__', '__version__'):",
)
replace_once(
    path,
    '''    This tool allows the agent to write and run Python code for:\n    - Data processing and analysis''',
    '''    This tool allows the agent to write and run Python code for:\n    - Read user-provided files and read/write files created under OUTPUT_DIR in the same execution\n    - Use safe path-string helpers via os.path; full os process/filesystem APIs remain blocked\n    - Inspect package versions with module.__version__ or importlib.metadata.version("package")\n    - Data processing and analysis''',
)

print('V15 Python sandbox patch applied.')

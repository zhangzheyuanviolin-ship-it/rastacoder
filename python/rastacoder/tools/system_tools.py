"""
System Tools - Device information, file management, and system utilities

These tools provide safe access to system information and file operations
without exposing dangerous capabilities.
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

from ..bridge import ToolError, get_bridge


def get_device_info() -> Dict:
    """
    Get device information (Android-specific via Chaquopy).
    
    Returns:
        Dict with device information
    """
    from android.os import Build
    from android.content import Context
    from java import android
    
    bridge = get_bridge()
    context = bridge.get_context()
    
    # Get device info
    device_info = {
        "manufacturer": Build.MANUFACTURER,
        "model": Build.MODEL,
        "android_version": Build.VERSION.RELEASE,
        "sdk_version": Build.VERSION.SDK_INT,
        "device": Build.DEVICE,
        "product": Build.PRODUCT,
    }
    
    # Get storage info
    try:
        stat_fs = android.os.StatFs(context.getFilesDir().getAbsolutePath())
        total_bytes = stat_fs.getTotalBytes()
        available_bytes = stat_fs.getAvailableBytes()
        free_bytes = stat_fs.getFreeBytes()
        
        device_info["storage"] = {
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "available_mb": round(available_bytes / (1024 * 1024), 2),
            "free_mb": round(free_bytes / (1024 * 1024), 2),
            "usage_percent": round((1 - available_bytes / total_bytes) * 100, 1)
        }
    except Exception as e:
        bridge.log(f"Storage info error: {e}")
        device_info["storage"] = {"error": "Could not retrieve storage info"}
    
    # Get memory info
    try:
        activity_manager = context.getSystemService(Context.ACTIVITY_SERVICE)
        memory_info = activity_manager.getMemoryInfo()
        device_info["memory"] = {
            "available_mb": round(memory_info.availMem / (1024 * 1024), 2),
            "low_memory": memory_info.lowMemory
        }
    except Exception as e:
        bridge.log(f"Memory info error: {e}")
        device_info["memory"] = {"error": "Could not retrieve memory info"}
    
    return device_info


def list_directory(
    path: str,
    recursive: bool = False,
    max_depth: int = 2
) -> Dict:
    """
    List directory contents with file information.
    
    Args:
        path: Directory path to list
        recursive: Whether to list subdirectories recursively
        max_depth: Maximum depth for recursive listing
        
    Returns:
        Dict with directory contents
    """
    bridge = get_bridge()
    
    # Validate path - only allow safe directories
    allowed_bases = [
        bridge.get_output_dir(),
        bridge.get_context().getFilesDir().getAbsolutePath(),
        bridge.get_context().getCacheDir().getAbsolutePath(),
    ]
    
    # Resolve to absolute path
    abs_path = os.path.abspath(path)
    
    # Check if path is allowed
    is_allowed = any(abs_path.startswith(base) for base in allowed_bases)
    if not is_allowed:
        # Check if it's a user-accessible directory
        user_dirs = ["/sdcard/Download", "/sdcard/Documents", "/sdcard/Pictures"]
        is_allowed = any(abs_path.startswith(d) for d in user_dirs)
    
    if not is_allowed:
        raise ToolError(
            f"Access denied: Can only list files in app directories or user folders. "
            f"Path: {abs_path}"
        )
    
    if not os.path.exists(abs_path):
        raise ToolError(f"Directory does not exist: {path}")
    
    if not os.path.isdir(abs_path):
        raise ToolError(f"Path is not a directory: {path}")
    
    result = {
        "path": abs_path,
        "type": "directory",
        "contents": []
    }
    
    def list_dir_recursive(current_path: str, depth: int = 0) -> List[Dict]:
        if depth > max_depth:
            return []
        
        items = []
        try:
            for entry in os.scandir(current_path):
                try:
                    stat_info = entry.stat()
                    item = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_directory": entry.is_dir(),
                        "size_bytes": stat_info.st_size if entry.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    }
                    
                    if entry.is_dir() and recursive and depth < max_depth:
                        item["children"] = list_dir_recursive(entry.path, depth + 1)
                    
                    items.append(item)
                except PermissionError:
                    items.append({
                        "name": entry.name,
                        "path": entry.path,
                        "error": "Permission denied"
                    })
        except PermissionError:
            bridge.log(f"Permission denied: {current_path}")
        
        return items
    
    result["contents"] = list_dir_recursive(abs_path)
    result["total_items"] = len(result["contents"])
    
    return result


def create_directory(
    path: str,
    parents: bool = True
) -> Dict:
    """
    Create a directory.
    
    Args:
        path: Directory path to create
        parents: Whether to create parent directories if needed
        
    Returns:
        Dict with creation result
    """
    bridge = get_bridge()
    abs_path = os.path.abspath(path)
    
    # Validate path
    output_dir = bridge.get_output_dir()
    if not abs_path.startswith(output_dir):
        raise ToolError(
            f"Can only create directories in output folder: {output_dir}"
        )
    
    try:
        if parents:
            os.makedirs(abs_path, exist_ok=True)
        else:
            os.mkdir(abs_path)
        
        return {
            "success": True,
            "path": abs_path,
            "message": f"Directory created: {abs_path}"
        }
    except FileExistsError:
        return {
            "success": False,
            "error": f"Directory already exists: {path}"
        }
    except PermissionError as e:
        raise ToolError(f"Permission denied: {e}")
    except OSError as e:
        raise ToolError(f"Failed to create directory: {e}")


def move_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = False
) -> Dict:
    """
    Move or rename a file.
    
    Args:
        source_path: Source file path
        dest_path: Destination path
        overwrite: Whether to overwrite if destination exists
        
    Returns:
        Dict with move result
    """
    bridge = get_bridge()
    
    source_abs = os.path.abspath(source_path)
    dest_abs = os.path.abspath(dest_path)
    
    # Validate paths
    output_dir = bridge.get_output_dir()
    for path, name in [(source_abs, "source"), (dest_abs, "destination")]:
        if not path.startswith(output_dir):
            raise ToolError(
                f"Can only move files within output folder: {output_dir}"
            )
    
    if not os.path.exists(source_abs):
        raise ToolError(f"Source file does not exist: {source_path}")
    
    if os.path.exists(dest_abs) and not overwrite:
        raise ToolError(
            f"Destination already exists. Use overwrite=True to replace: {dest_path}"
        )
    
    try:
        shutil.move(source_abs, dest_abs)
        return {
            "success": True,
            "source": source_abs,
            "destination": dest_abs,
            "message": f"File moved: {source_path} → {dest_path}"
        }
    except PermissionError as e:
        raise ToolError(f"Permission denied: {e}")
    except OSError as e:
        raise ToolError(f"Failed to move file: {e}")


def delete_file(path: str) -> Dict:
    """
    Delete a file.
    
    Args:
        path: File path to delete
        
    Returns:
        Dict with deletion result
    """
    bridge = get_bridge()
    abs_path = os.path.abspath(path)
    
    # Validate path
    output_dir = bridge.get_output_dir()
    if not abs_path.startswith(output_dir):
        raise ToolError(
            f"Can only delete files in output folder: {output_dir}"
        )
    
    if not os.path.exists(abs_path):
        return {
            "success": False,
            "error": f"File does not exist: {path}"
        }
    
    if os.path.isdir(abs_path):
        raise ToolError("Use delete_directory for folders")
    
    try:
        os.remove(abs_path)
        return {
            "success": True,
            "path": abs_path,
            "message": f"File deleted: {path}"
        }
    except PermissionError as e:
        raise ToolError(f"Permission denied: {e}")
    except OSError as e:
        raise ToolError(f"Failed to delete file: {e}")


def delete_directory(path: str, recursive: bool = False) -> Dict:
    """
    Delete a directory.
    
    Args:
        path: Directory path to delete
        recursive: Whether to delete contents recursively
        
    Returns:
        Dict with deletion result
    """
    bridge = get_bridge()
    abs_path = os.path.abspath(path)
    
    # Validate path
    output_dir = bridge.get_output_dir()
    if not abs_path.startswith(output_dir):
        raise ToolError(
            f"Can only delete directories in output folder: {output_dir}"
        )
    
    if not os.path.exists(abs_path):
        return {
            "success": False,
            "error": f"Directory does not exist: {path}"
        }
    
    if not os.path.isdir(abs_path):
        raise ToolError("Path is not a directory")
    
    try:
        if recursive:
            shutil.rmtree(abs_path)
        else:
            os.rmdir(abs_path)
        
        return {
            "success": True,
            "path": abs_path,
            "message": f"Directory deleted: {path}"
        }
    except OSError as e:
        if "not empty" in str(e).lower():
            raise ToolError(
                f"Directory not empty. Use recursive=True to delete contents: {e}"
            )
        raise ToolError(f"Failed to delete directory: {e}")


def copy_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = False
) -> Dict:
    """
    Copy a file.
    
    Args:
        source_path: Source file path
        dest_path: Destination path
        overwrite: Whether to overwrite if destination exists
        
    Returns:
        Dict with copy result
    """
    bridge = get_bridge()
    
    source_abs = os.path.abspath(source_path)
    dest_abs = os.path.abspath(dest_path)
    
    # Validate source
    output_dir = bridge.get_output_dir()
    if not source_abs.startswith(output_dir):
        raise ToolError(
            f"Can only copy files from output folder: {output_dir}"
        )
    
    if not os.path.exists(source_abs):
        raise ToolError(f"Source file does not exist: {source_path}")
    
    if os.path.exists(dest_abs) and not overwrite:
        raise ToolError(
            f"Destination already exists. Use overwrite=True to replace: {dest_path}"
        )
    
    try:
        shutil.copy2(source_abs, dest_abs)
        return {
            "success": True,
            "source": source_abs,
            "destination": dest_abs,
            "message": f"File copied: {source_path} → {dest_path}"
        }
    except PermissionError as e:
        raise ToolError(f"Permission denied: {e}")
    except OSError as e:
        raise ToolError(f"Failed to copy file: {e}")


def get_file_hash(
    path: str,
    algorithm: str = "sha256"
) -> Dict:
    """
    Calculate file hash.
    
    Args:
        path: File path to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Dict with hash result
    """
    import hashlib
    
    bridge = get_bridge()
    abs_path = os.path.abspath(path)
    
    if not os.path.exists(abs_path):
        raise ToolError(f"File does not exist: {path}")
    
    if os.path.isdir(abs_path):
        raise ToolError("Cannot hash directories")
    
    valid_algorithms = ["md5", "sha1", "sha256", "sha512"]
    if algorithm not in valid_algorithms:
        raise ToolError(
            f"Invalid algorithm. Choose from: {', '.join(valid_algorithms)}"
        )
    
    try:
        hash_func = hashlib.new(algorithm)
        
        # Read file in chunks for memory efficiency
        with open(abs_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        
        return {
            "success": True,
            "path": abs_path,
            "algorithm": algorithm,
            "hash": hash_func.hexdigest(),
            "size_bytes": os.path.getsize(abs_path)
        }
    except PermissionError:
        raise ToolError(f"Permission denied: {path}")
    except OSError as e:
        raise ToolError(f"Failed to calculate hash: {e}")

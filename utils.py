import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("ComfyDependencyIsolation.Utils")

def get_plugin_info(plugin_name: str) -> Optional[Dict]:
    """Get information about a plugin"""
    from .dependency_manager import global_dependency_manager
    
    if plugin_name in global_dependency_manager.plugins:
        plugin_info = global_dependency_manager.plugins[plugin_name].copy()
        
        # Add dependency information
        deps_paths = global_dependency_manager.get_plugin_deps_paths(plugin_name)
        plugin_info['dependency_paths'] = deps_paths
        plugin_info['dependency_count'] = len(deps_paths)
        
        return plugin_info
    
    return None

def cleanup_orphaned_deps():
    """Clean up orphaned dependency directories"""
    from .dependency_manager import global_dependency_manager
    
    logger.info("🧹 Cleaning up orphaned dependencies...")
    
    deps_dir = global_dependency_manager.global_deps_dir
    active_deps = set()
    
    # Collect all active dependency paths
    for plugin_name in global_dependency_manager.plugins:
        plugin_deps = global_dependency_manager.get_plugin_deps_paths(plugin_name)
        active_deps.update(plugin_deps)
    
    # Find and remove orphaned directories
    removed_count = 0
    for item in deps_dir.iterdir():
        if item.is_dir() and str(item) not in active_deps:
            try:
                shutil.rmtree(item)
                removed_count += 1
                logger.debug(f"Removed orphaned dependency: {item.name}")
            except Exception as e:
                logger.warning(f"Failed to remove {item}: {e}")
    
    logger.info(f"✅ Removed {removed_count} orphaned dependencies")

def validate_requirements_file(requirements_path: Path) -> bool:
    """Validate a requirements.txt file"""
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Basic validation - check if it looks like a package specification
                    if not any(char in line for char in ['==', '>=', '<=', '>', '<', '@']):
                        if not line.replace('-', '').replace('_', '').isalnum():
                            logger.warning(f"Invalid requirement format at line {line_num}: {line}")
                            return False
        return True
    except Exception as e:
        logger.error(f"Failed to validate requirements file: {e}")
        return False

def calculate_directory_size(directory: Path) -> int:
    """Calculate total size of a directory in bytes"""
    total_size = 0
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    return total_size

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
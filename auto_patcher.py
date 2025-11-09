import importlib
import sys
import builtins
import threading
from typing import Any, Optional, Set, List
import logging

logger = logging.getLogger("ComfyDependencyIsolation.AutoPatcher")

class AutoImportPatcher:
    """
    Automatic import patcher that redirects imports to isolated dependency environments
    """
    
    def __init__(self, dependency_manager):
        self.dependency_manager = dependency_manager
        self.original_import = builtins.__import__
        self.patched_plugins: Set[str] = set()
        self._lock = threading.Lock()
        
    def patch_plugin_imports(self, plugin_name: str):
        """Patch imports for a specific plugin"""
        with self._lock:
            if plugin_name in self.patched_plugins:
                return
                
            plugin_deps_paths = self.dependency_manager.get_plugin_deps_paths(plugin_name)
            if not plugin_deps_paths:
                logger.debug(f"No dependencies to patch for {plugin_name}")
                return
            
            # Store the original import function if we haven't already
            if not hasattr(self, '_original_import_saved'):
                self._original_import_saved = self.original_import
            
            def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
                """
                Custom import function that checks isolated dependencies first
                """
                # Get the plugin name from the caller's file path
                caller_plugin = self._get_caller_plugin()
                
                if caller_plugin and caller_plugin in self.patched_plugins:
                    # Try importing from the plugin's isolated dependencies first
                    plugin_deps = self.dependency_manager.get_plugin_deps_paths(caller_plugin)
                    
                    for deps_path in plugin_deps:
                        try:
                            # Temporarily modify sys.path to prefer the isolated dependency
                            original_sys_path = sys.path.copy()
                            sys.path.insert(0, deps_path)
                            
                            # Use the original import function
                            module = self._original_import_saved(
                                name, globals, locals, fromlist, level
                            )
                            
                            # Restore original path
                            sys.path[:] = original_sys_path
                            
                            logger.debug(f"✅ {caller_plugin} imported {name} from isolated env")
                            return module
                            
                        except ImportError:
                            # Restore path and continue
                            sys.path[:] = original_sys_path
                            continue
                        except Exception:
                            sys.path[:] = original_sys_path
                            raise
                
                # Fall back to global environment
                return self._original_import_saved(name, globals, locals, fromlist, level)
            
            # Replace the built-in import function
            builtins.__import__ = custom_import
            self.patched_plugins.add(plugin_name)
            
            logger.info(f"🔀 Import patching enabled for {plugin_name}")
    
    def _get_caller_plugin(self) -> Optional[str]:
        """Determine which plugin is making the import call"""
        import inspect
        
        try:
            # Get the call stack
            frame = inspect.currentframe()
            # Go up the stack to find the plugin caller
            for _ in range(10):  # Limit stack depth
                frame = frame.f_back
                if frame is None:
                    break
                    
                # Get the filename from the frame
                filename = frame.f_code.co_filename
                
                # Check if this file belongs to any of our managed plugins
                for plugin_name, plugin_info in self.dependency_manager.plugins.items():
                    plugin_dir = str(plugin_info['dir'])
                    if filename.startswith(plugin_dir):
                        return plugin_name
                        
        except Exception:
            pass
            
        return None
    
    def restore_import(self):
        """Restore the original import function"""
        with self._lock:
            if hasattr(self, '_original_import_saved'):
                builtins.__import__ = self._original_import_saved
                self.patched_plugins.clear()
                logger.info("🔁 Original import function restored")
    
    def get_patched_plugins(self) -> List[str]:
        """Get list of currently patched plugins"""
        return list(self.patched_plugins)

# Global auto patcher instance
_auto_patcher = None

def get_auto_patcher():
    """Get or create the global auto patcher instance"""
    global _auto_patcher
    if _auto_patcher is None:
        from .dependency_manager import global_dependency_manager
        _auto_patcher = AutoImportPatcher(global_dependency_manager)
    return _auto_patcher
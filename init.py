"""
ComfyUI Dependency Isolation
Automatic dependency isolation system for ComfyUI plugins
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ComfyDependencyIsolation")

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from .dependency_manager import global_dependency_manager
    from .auto_patcher import get_auto_patcher
    from .config import load_config, save_config
    from .utils import get_plugin_info, cleanup_orphaned_deps
    
    # Load configuration
    config = load_config()
    
    # Initialize the dependency manager
    if config.get('auto_initialize', True):
        logger.info("🚀 Starting ComfyUI Dependency Isolation System...")
        
        # Auto-initialize all plugins
        global_dependency_manager.auto_initialize_all_plugins()
        
        # Enable import patching for all plugins
        for plugin_name in global_dependency_manager.plugins:
            get_auto_patcher().patch_plugin_imports(plugin_name)
        
        logger.info("✅ ComfyUI Dependency Isolation System ready")
        logger.info(f"📦 Managed plugins: {list(global_dependency_manager.plugins.keys())}")
    
    # Export public API
    __all__ = [
        'global_dependency_manager',
        'get_auto_patcher', 
        'load_config',
        'save_config',
        'get_plugin_info',
        'cleanup_orphaned_deps'
    ]

except Exception as e:
    logger.error(f"❌ Failed to initialize ComfyUI Dependency Isolation: {e}")
    # Don't crash ComfyUI if our system fails
    pass

# ComfyUI integration
def init():
    """ComfyUI auto-called initialization function"""
    # System is already initialized above
    pass

# Web extension registration
WEB_DIRECTORY = "./web"
__all__ = ["WEB_DIRECTORY"]
import os
import sys
import importlib
import subprocess
import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
import logging

logger = logging.getLogger("ComfyDependencyIsolation.DependencyManager")

class GlobalDependencyManager:
    """Global dependency manager for ComfyUI plugins"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Find ComfyUI root directory
        self.comfyui_root = self._find_comfyui_root()
        self.custom_nodes_dir = self.comfyui_root / "custom_nodes"
        self.deps_manager_dir = self.custom_nodes_dir / "comfyui-dependency-isolation"
        self.global_deps_dir = self.deps_manager_dir / "isolated_deps"
        
        # Plugin and dependency tracking
        self.plugins: Dict[str, Dict] = {}
        self.installed_deps: Dict[str, Set[str]] = {}
        self.dependency_metadata: Dict[str, Dict] = {}
        
        # Create directories
        self.global_deps_dir.mkdir(exist_ok=True)
        
        # Load existing metadata
        self._load_metadata()
        
        # Auto-discover plugins
        self._auto_discover_plugins()
        
        self._initialized = True
        logger.info(f"Initialized with {len(self.plugins)} plugins discovered")
    
    def _find_comfyui_root(self) -> Path:
        """Find the ComfyUI root directory"""
        current_dir = Path(__file__).parent
        # Look for ComfyUI root by checking for typical directories
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / "web" / "extensions.py").exists() or (parent / "main.py").exists():
                return parent
        # Fallback to current directory structure
        return current_dir.parent.parent
    
    def _load_metadata(self):
        """Load dependency metadata from disk"""
        metadata_file = self.global_deps_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dependency_metadata = data.get('dependencies', {})
                    self.installed_deps = {
                        k: set(v) for k, v in data.get('installed_deps', {}).items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
    
    def _save_metadata(self):
        """Save dependency metadata to disk"""
        metadata_file = self.global_deps_dir / "metadata.json"
        try:
            data = {
                'dependencies': self.dependency_metadata,
                'installed_deps': {k: list(v) for k, v in self.installed_deps.items()},
                'last_updated': time.time()
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _auto_discover_plugins(self):
        """Automatically discover all plugins with requirements.txt"""
        for plugin_dir in self.custom_nodes_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir != self.deps_manager_dir:
                requirements_file = plugin_dir / "requirements.txt"
                if requirements_file.exists():
                    plugin_name = plugin_dir.name
                    self._register_plugin(plugin_name, plugin_dir, requirements_file)
    
    def _register_plugin(self, plugin_name: str, plugin_dir: Path, requirements_file: Path):
        """Register a plugin with the dependency manager"""
        deps_hash = self._get_requirements_hash(requirements_file)
        
        self.plugins[plugin_name] = {
            'dir': plugin_dir,
            'requirements_file': requirements_file,
            'deps_hash': deps_hash,
            'isolated_deps_dir': self.global_deps_dir / plugin_name,
            'registered_time': time.time()
        }
        
        logger.info(f"Registered plugin: {plugin_name} (hash: {deps_hash})")
    
    def _get_requirements_hash(self, requirements_file: Path) -> str:
        """Generate hash for requirements.txt content"""
        content = requirements_file.read_text(encoding='utf-8', errors='ignore')
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _parse_requirements(self, requirements_file: Path) -> List[Tuple[str, str]]:
        """Parse requirements.txt file"""
        requirements = []
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name and full spec
                        pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        requirements.append((pkg_name, line, line_num))
        except Exception as e:
            logger.error(f"Failed to parse {requirements_file}: {e}")
        
        return requirements
    
    def _install_package_isolated(self, pkg_spec: str, target_dir: Path, plugin_name: str) -> bool:
        """Install a package in isolated directory"""
        try:
            # Use pip to install to target directory
            cmd = [
                sys.executable, "-m", "pip", "install",
                pkg_spec,
                "--target", str(target_dir),
                "--no-deps",
                "--disable-pip-version-check",
                "--quiet",
                "--timeout", "60",
                "--retries", "3"
            ]
            
            logger.debug(f"Installing {pkg_spec} for {plugin_name}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully installed {pkg_spec} for {plugin_name}")
                return True
            else:
                logger.error(f"❌ Failed to install {pkg_spec} for {plugin_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout installing {pkg_spec} for {plugin_name}")
            return False
        except Exception as e:
            logger.error(f"💥 Exception installing {pkg_spec} for {plugin_name}: {e}")
            return False
    
    def initialize_plugin_dependencies(self, plugin_name: str) -> bool:
        """Initialize dependencies for a specific plugin"""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False
            
        plugin_info = self.plugins[plugin_name]
        requirements = self._parse_requirements(plugin_info['requirements_file'])
        
        if not requirements:
            logger.info(f"📭 No dependencies found for {plugin_name}")
            return True
            
        logger.info(f"🔧 Initializing dependencies for {plugin_name} ({len(requirements)} packages)")
        
        # Create plugin's isolated deps directory
        plugin_info['isolated_deps_dir'].mkdir(exist_ok=True)
        
        success_count = 0
        for pkg_name, pkg_spec, line_num in requirements:
            # Create unique directory for this package version
            pkg_hash = hashlib.md5(pkg_spec.encode()).hexdigest()[:12]
            pkg_isolated_dir = plugin_info['isolated_deps_dir'] / f"{pkg_name}_{pkg_hash}"
            
            # Check if already installed
            if pkg_isolated_dir.exists():
                logger.debug(f"📦 Using cached {pkg_spec} for {plugin_name}")
                success_count += 1
            else:
                # Install the package
                if self._install_package_isolated(pkg_spec, pkg_isolated_dir, plugin_name):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Skipping failed dependency: {pkg_spec}")
                    continue
            
            # Add to Python path if not already there
            if str(pkg_isolated_dir) not in sys.path:
                sys.path.insert(0, str(pkg_isolated_dir))
            
            # Track installed dependencies
            if plugin_name not in self.installed_deps:
                self.installed_deps[plugin_name] = set()
            self.installed_deps[plugin_name].add(str(pkg_isolated_dir))
            
            # Store metadata
            dep_key = f"{plugin_name}:{pkg_name}"
            self.dependency_metadata[dep_key] = {
                'package': pkg_name,
                'spec': pkg_spec,
                'install_dir': str(pkg_isolated_dir),
                'plugin': plugin_name,
                'installed_time': time.time()
            }
        
        # Save metadata
        self._save_metadata()
        
        logger.info(f"✅ {plugin_name}: {success_count}/{len(requirements)} dependencies initialized")
        return success_count > 0
    
    def auto_initialize_all_plugins(self):
        """Automatically initialize all discovered plugins"""
        logger.info(f"🔄 Auto-initializing {len(self.plugins)} plugins...")
        
        for plugin_name in self.plugins:
            self.initialize_plugin_dependencies(plugin_name)
        
        logger.info("🎉 All plugins initialized")
    
    def get_plugin_deps_paths(self, plugin_name: str) -> List[str]:
        """Get dependency paths for a plugin"""
        return list(self.installed_deps.get(plugin_name, []))
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """Get information about a plugin"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all managed plugins"""
        return list(self.plugins.keys())
    
    def cleanup_orphaned_deps(self):
        """Clean up orphaned dependencies"""
        # Implementation for cleaning up unused dependencies
        pass

# Global singleton instance
global_dependency_manager = GlobalDependencyManager()
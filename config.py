import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger("ComfyDependencyIsolation.Config")

DEFAULT_CONFIG = {
    "auto_initialize": True,
    "check_updates": False,
    "timeout": 300,
    "mirror_url": "",
    "log_level": "INFO",
    "cleanup_orphaned": True,
    "max_cache_size": "1GB",
    "enable_web_ui": True
}

def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    config_path = Path(__file__).parent / "config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            
            logger.info("📁 Configuration loaded from config.json")
            return config
            
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
    
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]):
    """Save configuration to file"""
    config_path = Path(__file__).parent / "config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info("💾 Configuration saved to config.json")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def get_web_config() -> Dict[str, Any]:
    """Get configuration for web interface"""
    config = load_config()
    
    return {
        "auto_initialize": config.get("auto_initialize", True),
        "enable_web_ui": config.get("enable_web_ui", True),
        "log_level": config.get("log_level", "INFO")
    }
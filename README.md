# ComfyUI Dependency Isolation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A powerful dependency isolation system for ComfyUI plugins that enables true multi-version package coexistence without conflicts.

## ✨ Features

- 🔒 **Automatic Isolation** - No code changes required for plugins
- 📦 **Multi-Version Coexistence** - Different plugins can use different package versions
- ⚡ **Zero Configuration** - Works out of the box
- 🛡️ **Conflict Prevention** - No more dependency conflicts between plugins
- 🔄 **Smart Caching** - Dependencies are cached and reused
- 🎯 **Selective Patching** - Only intercepts imports when needed
- 📊 **Web UI** - Monitor dependency status in ComfyUI

## 🚀 Installation

### Method 1: Direct Download
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/comfyui-dependency-isolation.git
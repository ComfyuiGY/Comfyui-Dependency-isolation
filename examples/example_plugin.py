"""
Example plugin demonstrating automatic dependency isolation
No special code required - just include requirements.txt!
"""

from .nodes import ExampleImageProcessor, ExampleTextProcessor

NODE_CLASS_MAPPINGS = {
    "ExampleImageProcessor": ExampleImageProcessor,
    "ExampleTextProcessor": ExampleTextProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExampleImageProcessor": "Example Image Processor",
    "ExampleTextProcessor": "Example Text Processor",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
import torch
import logging

logger = logging.getLogger("ExamplePlugin")

class ExampleImageProcessor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "threshold": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process_images"
    CATEGORY = "example"
    
    def process_images(self, images, threshold):
        try:
            # These imports will be automatically routed to isolated versions
            import numpy as np
            from PIL import Image, ImageFilter
            
            # Simple image processing example
            processed = []
            for image in images:
                # Convert to numpy
                img_np = image.cpu().numpy()
                
                # Simple threshold operation
                img_np = (img_np > threshold).astype(np.float32)
                
                # Convert back to tensor
                img_tensor = torch.from_numpy(img_np)
                processed.append(img_tensor)
            
            logger.info("✅ ExampleImageProcessor completed successfully")
            return (torch.stack(processed),)
            
        except ImportError as e:
            logger.error(f"❌ Import failed: {e}")
            # Fallback - return original images
            return (images,)

class ExampleTextProcessor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "operation": (["uppercase", "lowercase", "reverse"],),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_text"
    CATEGORY = "example"
    
    def process_text(self, text, operation):
        try:
            # This import will use the isolated version from requirements.txt
            import requests
            
            if operation == "uppercase":
                result = text.upper()
            elif operation == "lowercase":
                result = text.lower()
            elif operation == "reverse":
                result = text[::-1]
            else:
                result = text
            
            logger.info(f"✅ ExampleTextProcessor: {operation} completed")
            return (result,)
            
        except Exception as e:
            logger.error(f"❌ Text processing failed: {e}")
            return (text,)
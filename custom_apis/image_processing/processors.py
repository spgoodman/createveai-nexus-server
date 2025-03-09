"""
Image processing utilities for the Createve.AI API Server.
"""

import base64
import io
import numpy as np
from PIL import Image
from typing import Tuple, Optional

class ThumbnailGenerator:
    """Generates thumbnails from input images."""
    
    CATEGORY = "image"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the thumbnail generator."""
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INTEGER", {"default": 128, "min": 16, "max": 1024}),
                "height": ("INTEGER", {"default": 128, "min": 16, "max": 1024}),
            },
            "optional": {
                "maintain_aspect_ratio": ("BOOLEAN", {"default": True}),
                "quality": ("INTEGER", {"default": 85, "min": 1, "max": 100}),
                "format": (["JPEG", "PNG", "WEBP"], {"default": "JPEG"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("thumbnail",)
    FUNCTION = "generate_thumbnail"
    
    def generate_thumbnail(
        self, 
        image, 
        width: int = 128, 
        height: int = 128,
        maintain_aspect_ratio: bool = True,
        quality: int = 85,
        format: str = "JPEG"
    ):
        """
        Generate a thumbnail from an input image.
        
        Args:
            image: Input image data (numpy array or base64 string)
            width: Width of the thumbnail in pixels
            height: Height of the thumbnail in pixels
            maintain_aspect_ratio: Whether to maintain the aspect ratio
            quality: JPEG quality (1-100)
            format: Output format (JPEG, PNG, WEBP)
            
        Returns:
            Thumbnail image data
        """
        try:
            # Convert numpy array to PIL Image
            if isinstance(image, np.ndarray):
                # Convert from RGB to BGR if needed
                if image.shape[2] == 3:
                    img = Image.fromarray(image)
                else:
                    # Handle alpha channel if present
                    img = Image.fromarray(image)
            elif isinstance(image, str) and image.startswith('data:'):
                # Handle base64 encoded image
                format_str, base64_str = image.split(';base64,')
                img_data = base64.b64decode(base64_str)
                img = Image.open(io.BytesIO(img_data))
            else:
                # Assume it's a file path
                img = Image.open(image)
            
            # Calculate dimensions
            if maintain_aspect_ratio:
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                
                if width / height > aspect_ratio:
                    # Width is the constraint
                    new_width = int(height * aspect_ratio)
                    new_height = height
                else:
                    # Height is the constraint
                    new_width = width
                    new_height = int(width / aspect_ratio)
            else:
                new_width = width
                new_height = height
            
            # Resize image
            img_resized = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to RGB if needed
            if img_resized.mode != 'RGB' and format == 'JPEG':
                img_resized = img_resized.convert('RGB')
            
            # Convert back to numpy array
            thumbnail = np.array(img_resized)
            
            return (thumbnail,)
            
        except Exception as e:
            raise Exception(f"Error generating thumbnail: {str(e)}")


class ImageResizer:
    """Resizes images to specified dimensions."""
    
    CATEGORY = "image"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the image resizer."""
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INTEGER", {"default": 512, "min": 16, "max": 4096}),
                "height": ("INTEGER", {"default": 512, "min": 16, "max": 4096}),
            },
            "optional": {
                "maintain_aspect_ratio": ("BOOLEAN", {"default": True}),
                "resampling_method": (["LANCZOS", "BILINEAR", "BICUBIC", "NEAREST"], {"default": "LANCZOS"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("resized_image",)
    FUNCTION = "resize_image"
    
    def resize_image(
        self, 
        image, 
        width: int = 512, 
        height: int = 512,
        maintain_aspect_ratio: bool = True,
        resampling_method: str = "LANCZOS"
    ):
        """
        Resize an input image to specified dimensions.
        
        Args:
            image: Input image data (numpy array)
            width: Width of the output image in pixels
            height: Height of the output image in pixels
            maintain_aspect_ratio: Whether to maintain the aspect ratio
            resampling_method: Resampling method to use
            
        Returns:
            Resized image data
        """
        try:
            # Convert numpy array to PIL Image
            if isinstance(image, np.ndarray):
                img = Image.fromarray(image)
            elif isinstance(image, str) and image.startswith('data:'):
                # Handle base64 encoded image
                format_str, base64_str = image.split(';base64,')
                img_data = base64.b64decode(base64_str)
                img = Image.open(io.BytesIO(img_data))
            else:
                # Assume it's a file path
                img = Image.open(image)
            
            # Get resampling method
            resampling = {
                "LANCZOS": Image.LANCZOS,
                "BILINEAR": Image.BILINEAR,
                "BICUBIC": Image.BICUBIC,
                "NEAREST": Image.NEAREST
            }.get(resampling_method, Image.LANCZOS)
            
            # Calculate dimensions
            if maintain_aspect_ratio:
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                
                if width / height > aspect_ratio:
                    # Width is the constraint
                    new_width = int(height * aspect_ratio)
                    new_height = height
                else:
                    # Height is the constraint
                    new_width = width
                    new_height = int(width / aspect_ratio)
            else:
                new_width = width
                new_height = height
            
            # Resize image
            img_resized = img.resize((new_width, new_height), resampling)
            
            # Convert back to numpy array
            resized_image = np.array(img_resized)
            
            return (resized_image,)
            
        except Exception as e:
            raise Exception(f"Error resizing image: {str(e)}")

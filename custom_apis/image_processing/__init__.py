"""
Image processing module for the Createve.AI API Server.

This module provides image processing capabilities including thumbnail generation
and image resizing.
"""

from .processors import ThumbnailGenerator, ImageResizer

# Map class names to class objects
NODE_CLASS_MAPPINGS = {
    "thumbnailGenerator": ThumbnailGenerator,
    "imageResizer": ImageResizer
}

# Map class names to display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "thumbnailGenerator": "Thumbnail Generator",
    "imageResizer": "Image Resizer"
}

# Define which API endpoints use queue mode
API_SERVER_QUEUE_MODE = {
    ThumbnailGenerator: False,  # Direct mode
    ImageResizer: False  # Direct mode
}

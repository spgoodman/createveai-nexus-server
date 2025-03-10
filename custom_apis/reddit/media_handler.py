"""
Media processing utilities for Reddit content.
"""

import io
import re
import requests
from typing import Dict, Any, Optional, Tuple, Union, List
import base64
from PIL import Image
from bs4 import BeautifulSoup


class MediaHandler:
    """Handle media content from Reddit posts including images, videos, and GIFs."""
    
    # Known image hosts
    IMAGE_HOSTS = [
        "i.redd.it", "i.imgur.com", "imgur.com", 
        "i.reddituploads.com", "cdn.reddituploadss.com", 
    ]
    
    # Headers to use when making requests
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    @staticmethod
    def is_direct_image_url(url: str) -> bool:
        """Check if URL directly points to an image file."""
        if not url:
            return False
            
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']
        return any(url.lower().endswith(ext) for ext in image_extensions)
    
    @staticmethod
    def is_reddit_gallery(url: str) -> bool:
        """Check if URL is a Reddit gallery."""
        if not url:
            return False
        
        return "reddit.com/gallery/" in url.lower()
    
    @staticmethod
    def is_imgur_album(url: str) -> bool:
        """Check if URL is an Imgur album."""
        if not url:
            return False
            
        return "imgur.com/a/" in url.lower() or "imgur.com/album/" in url.lower()
    
    @staticmethod
    def is_video_url(url: str) -> bool:
        """Check if URL points to a video file."""
        if not url:
            return False
            
        video_extensions = ['.mp4', '.webm', '.mov', '.avi', '.wmv', '.flv', '.mkv']
        return any(url.lower().endswith(ext) for ext in video_extensions)
    
    @staticmethod
    def convert_to_base64(image_data: bytes, format: str = "JPEG") -> str:
        """Convert image data to base64 string."""
        if not image_data:
            return ""
        
        return base64.b64encode(image_data).decode('utf-8')
    
    @classmethod
    def get_image_from_url(cls, url: str, referer: Optional[str] = None, 
                         max_width: Optional[int] = None, 
                         max_height: Optional[int] = None,
                         output_format: str = "JPEG") -> Optional[str]:
        """
        Retrieve and process image from URL.
        
        Args:
            url: Image URL
            referer: Referer URL (often needed for some sites)
            max_width: Maximum width to resize to
            max_height: Maximum height to resize to
            output_format: Output image format (JPEG, PNG, etc.)
            
        Returns:
            Base64 encoded image or None if failed
        """
        try:
            # Set up headers
            headers = cls.DEFAULT_HEADERS.copy()
            if referer:
                headers["Referer"] = referer
            
            # Get image data
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if needed
            if max_width or max_height:
                original_width, original_height = img.size
                
                # Calculate new dimensions
                if max_width and max_height:
                    # Resize to fit within both constraints
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    ratio = min(width_ratio, height_ratio)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
                elif max_width:
                    # Scale based on width
                    ratio = max_width / original_width
                    new_width = max_width
                    new_height = int(original_height * ratio)
                else:
                    # Scale based on height
                    ratio = max_height / original_height
                    new_width = int(original_width * ratio)
                    new_height = max_height
                
                # Only resize if we need to make the image smaller
                if new_width < original_width or new_height < original_height:
                    img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to specified format
            if img.mode in ("RGBA", "LA") and output_format == "JPEG":
                # JPEG doesn't support alpha channel, convert to RGB
                img = img.convert("RGB")
                
            # Save to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=output_format, quality=85 if output_format == "JPEG" else None)
            img_byte_arr.seek(0)
            
            # Convert to base64
            return cls.convert_to_base64(img_byte_arr.getvalue())
            
        except Exception as e:
            print(f"Error retrieving image: {str(e)}")
            return None
    
    @classmethod
    def extract_media_from_submission(cls, submission_data: Dict[str, Any], 
                                     include_media: bool = True,
                                     max_width: Optional[int] = None,
                                     max_height: Optional[int] = None,
                                     output_format: str = "JPEG") -> Dict[str, Any]:
        """
        Extract and process media from a Reddit submission.
        
        Args:
            submission_data: Submission data dictionary (from API)
            include_media: Whether to include media in response
            max_width: Maximum width to resize to
            max_height: Maximum height to resize to
            output_format: Output image format
            
        Returns:
            Updated submission data with media info
        """
        if not submission_data or not include_media:
            return submission_data
        
        result = submission_data.copy()
        
        # Initialize media info
        result["media_info"] = {
            "has_media": False,
            "media_type": None,
            "media_url": None,
            "is_processed": False,
        }
        
        # Get URL from submission
        url = submission_data.get("url", "")
        if not url:
            return result
            
        # Get permalink for referer
        referer = f"https://www.reddit.com{submission_data.get('permalink', '')}"
        
        # Check for direct image
        if cls.is_direct_image_url(url):
            result["media_info"]["has_media"] = True
            result["media_info"]["media_type"] = "image"
            result["media_info"]["media_url"] = url
            
            if include_media:
                base64_img = cls.get_image_from_url(
                    url, 
                    referer=referer,
                    max_width=max_width,
                    max_height=max_height,
                    output_format=output_format
                )
                
                if base64_img:
                    result["media_info"]["base64_data"] = base64_img
                    result["media_info"]["is_processed"] = True
        
        # Check for video
        elif cls.is_video_url(url) or submission_data.get("is_video", False):
            result["media_info"]["has_media"] = True
            result["media_info"]["media_type"] = "video"
            result["media_info"]["media_url"] = url
            
            # For videos, we don't include base64 data, just metadata
            if "media" in submission_data and submission_data["media"]:
                if "reddit_video" in submission_data["media"]:
                    video_data = submission_data["media"]["reddit_video"]
                    result["media_info"]["width"] = video_data.get("width")
                    result["media_info"]["height"] = video_data.get("height")
                    result["media_info"]["duration"] = video_data.get("duration")
                    
                    # Direct video URL (without sound)
                    if "fallback_url" in video_data:
                        result["media_info"]["direct_url"] = video_data["fallback_url"]
        
        # Check for Reddit gallery
        elif cls.is_reddit_gallery(url):
            result["media_info"]["has_media"] = True
            result["media_info"]["media_type"] = "gallery"
            result["media_info"]["media_url"] = url
            
            # Gallery processing would be more complex and require additional API calls
            # This is a placeholder for more comprehensive gallery handling
        
        # Check for Imgur album
        elif cls.is_imgur_album(url):
            result["media_info"]["has_media"] = True
            result["media_info"]["media_type"] = "imgur_album"
            result["media_info"]["media_url"] = url
        
        # For other URLs, check if they're from common image hosts
        elif any(host in url for host in cls.IMAGE_HOSTS):
            result["media_info"]["has_media"] = True
            result["media_info"]["media_type"] = "image"
            result["media_info"]["media_url"] = url
            
            if include_media:
                base64_img = cls.get_image_from_url(
                    url, 
                    referer=referer,
                    max_width=max_width,
                    max_height=max_height,
                    output_format=output_format
                )
                
                if base64_img:
                    result["media_info"]["base64_data"] = base64_img
                    result["media_info"]["is_processed"] = True
        
        return result
    
    @classmethod
    def extract_image_urls_from_html(cls, html_content: str) -> List[str]:
        """Extract image URLs from HTML content."""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = []
        
        # Extract from img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and cls.is_direct_image_url(src):
                image_urls.append(src)
        
        # Extract from background images in style attributes
        for tag in soup.find_all(style=True):
            style = tag['style']
            urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', style)
            for url in urls:
                if cls.is_direct_image_url(url):
                    image_urls.append(url)
        
        return image_urls

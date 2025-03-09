# Creating Custom API Modules

This comprehensive guide explains how to create custom API modules for the Createve.AI API Server, detailing every aspect from basic structure to advanced features.

## Introduction

The Createve.AI API Server allows you to create custom API endpoints by writing Python classes following a specific pattern. These classes are dynamically loaded and exposed as both REST API endpoints and MCP tools.

Custom API modules are stored in the `custom_apis` directory and can be organized in any directory structure. The server recursively scans this directory for Python files and imports them automatically.

## File Organization

A custom API module can be structured in two ways:

1. **Single File Module**: A single Python file with one or more API classes
2. **Package Module**: A directory with multiple files, an `__init__.py` file, and optional `requirements.txt`

Recommended structure:

```
custom_apis/
├── simple_module.py                # A single file module
├── image_processing/               # A package module
│   ├── __init__.py                 # Exports classes and defines configuration
│   ├── processors.py               # Contains API classes
│   ├── helpers.py                  # Helper functions used by API classes
│   └── requirements.txt            # Dependencies (Pillow, numpy, etc.)
└── data_processing/
    ├── __init__.py
    ├── transformers.py
    ├── validators.py
    └── requirements.txt
```

## Class Structure in Detail

Each API class must follow this structure:

```python
class MyApiEndpoint:
    """
    Description of what this API endpoint does.
    This docstring will be used in the API documentation.
    """
    
    # Category for grouping in OpenAPI documentation
    CATEGORY = "my_category"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for the API endpoint."""
        return {
            "required": {
                # Required parameters
                "param1": ("STRING", {"multiline": False}),
                "param2": ("INTEGER", {"default": 1, "min": 1, "max": 10}),
            },
            "optional": {
                # Optional parameters with defaults
                "param3": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
            }
        }
    
    # Define the types of return values
    RETURN_TYPES = ("STRING", "INTEGER")
    
    # Human-readable names for return values (must match RETURN_TYPES in length)
    RETURN_NAMES = ("result", "count")
    
    # Name of the method to call when this API is invoked
    FUNCTION = "process"
    
    def process(self, param1, param2, param3=0.5):
        """
        Main processing function for the API endpoint.
        
        Args:
            param1 (str): Description of param1
            param2 (int): Description of param2
            param3 (float, optional): Description of param3. Defaults to 0.5.
            
        Returns:
            tuple: A tuple containing (result, count)
        """
        # Process the inputs
        result = f"Processed: {param1}"
        count = param2 + int(param3 * 10)
        
        # Return the results as a tuple matching RETURN_TYPES
        return (result, count)
```

### Key Class Attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `CATEGORY` | Optional | Groups related endpoints in documentation |
| `INPUT_TYPES()` | Required | Defines input parameters with types and constraints |
| `RETURN_TYPES` | Required | Tuple of data types that this endpoint returns |
| `RETURN_NAMES` | Optional | Tuple of human-readable names for return values |
| `FUNCTION` | Required | The name of the method to call when endpoint is invoked |

## Module Exports in Detail

Every API module must export its classes through three dictionaries:

```python
# Map display names to class objects
NODE_CLASS_MAPPINGS = {
    "My API Endpoint": MyApiEndpoint,  # Key is display name, value is class object
    "Another API": AnotherApiClass,
}

# Map class names to human-readable display names (optional but recommended)
NODE_DISPLAY_NAME_MAPPINGS = {
    "My API Endpoint": "My API Endpoint",
    "Another API": "Advanced Data Processor",  # Can be more descriptive than class name
}

# Define processing mode for each endpoint (direct or queue)
API_SERVER_QUEUE_MODE = {
    MyApiEndpoint: False,  # Direct mode - returns result immediately
    AnotherApiClass: True,  # Queue mode - returns queue_id for long operations
}
```

## Supported Data Types

The server supports various data types for inputs and outputs. Each type is handled differently by the API server.

| Type | Description | Input Format | Output Format | Example |
|------|-------------|--------------|--------------|---------|
| `STRING` | Text string | JSON string | JSON string | `("STRING", {"multiline": False})` |
| `INTEGER` | Integer number | JSON number | JSON number | `("INTEGER", {"default": 1, "min": 0, "max": 100})` |
| `FLOAT` | Floating-point number | JSON number | JSON number | `("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0})` |
| `BOOLEAN` | Boolean value | JSON boolean | JSON boolean | `("BOOLEAN", {"default": True})` |
| `IMAGE` | Image data | Base64 string | Base64 string | `("IMAGE",)` |
| `VIDEO` | Video data | Base64 string | Base64 string | `("VIDEO",)` |
| `FILE` | Generic file data | Base64 string | Base64 string | `("FILE",)` |
| `DICT` | Dictionary/object | JSON object | JSON object | `("DICT",)` |
| `LIST` | Array/list | JSON array | JSON array | `("LIST",)` |

### Input Type Parameters

When defining input types, you can specify additional parameters:

```python
"param_name": ("TYPE", {
    "default": value,       # Default value if not provided by client
    "min": value,           # Minimum value (for numeric types)
    "max": value,           # Maximum value (for numeric types)
    "step": value,          # Step value for UI sliders (for numeric types)
    "multiline": boolean,   # For STRING, whether it's a multi-line text area
    "placeholder": string,  # Placeholder text for documentation
})
```

### Enumeration Types

For parameters that should accept only specific values, use a list as the type:

```python
"color_mode": (["rgb", "grayscale", "cmyk"], {"default": "rgb"}),
"interpolation": (["nearest", "bilinear", "bicubic", "lanczos"], {"default": "lanczos"})
```

## Processing Modes

### Direct Mode vs. Queue Mode

The API server supports two processing modes:

1. **Direct Mode (Default)**
   - Execution happens synchronously during the request
   - Result is returned immediately in the response
   - Use for fast operations (< 1-2 seconds)
   - Client code: Single API call returns result directly

2. **Queue Mode**
   - Execution happens asynchronously in a worker process
   - Initial request returns a queue ID
   - Client must poll for results using the queue ID
   - Use for long-running operations
   - Client code: Two API calls (submit + check status)

### When to Use Queue Mode

Use Queue Mode when your API endpoint:
- Takes more than a few seconds to complete
- Involves heavy computation or resource-intensive operations
- Depends on external services with variable response times
- Processes large files or datasets

Example client polling with Queue Mode:

```python
# Step 1: Submit request
response = requests.post(api_url, headers=headers, json=payload)
queue_id = response.json()["queue_id"]

# Step 2: Poll for results
while True:
    queue_response = requests.post(
        f"{api_url}/queue",
        headers=headers,
        json={"queue_id": queue_id}
    )
    
    if "queue_id" not in queue_response.json():
        # Processing complete, get result
        result = queue_response.json()
        break
    
    time.sleep(2)  # Wait before checking again
```

## Handling Binary Data

### Images, Videos and Files

The API server automatically handles encoding/decoding for binary data types:

#### Client → Server (Input)

1. Client sends base64-encoded data
2. Server decodes base64 data automatically
3. For IMAGE type: Converted to a numpy array (RGB format)
4. For VIDEO/FILE types: Saved to temporary file, path passed to function

#### Server → Client (Output)

1. Function returns binary data (numpy array, file path)
2. Server automatically encodes to base64
3. Client receives base64-encoded string

### Working with Images

For image processing APIs:

```python
import numpy as np
from PIL import Image
import io
import base64

class ImageProcessor:
    """Image processing API endpoint."""
    
    CATEGORY = "image"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INTEGER", {"default": 512, "min": 32, "max": 4096}),
                "height": ("INTEGER", {"default": 512, "min": 32, "max": 4096}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("processed_image",)
    FUNCTION = "process_image"
    
    def process_image(self, image, width, height):
        """
        Process an input image.
        
        Args:
            image: Numpy array from decoded base64 data
            width: Target width
            height: Target height
            
        Returns:
            Processed image as numpy array
        """
        # image is already a numpy array - process it
        # Example: Resize image using PIL
        img = Image.fromarray(image)
        resized_img = img.resize((width, height), Image.LANCZOS)
        
        # Convert back to numpy array (required return type for IMAGE)
        result = np.array(resized_img)
        
        return (result,)
```

### Client-Side Image Handling

When sending images to the API:

```python
# Recommended: Send raw base64 data (not data URLs)
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("ascii")

# Send to API
response = requests.post(
    "http://localhost:43080/api/image_processing/imageProcessor",
    headers=headers,
    json={"image": image_data, "width": 800, "height": 600}
)
```

## Comprehensive Examples

### Example 1: Text Processing API

Complete example of a text processing API:

```python
"""Text processing module for Createve.AI API Server."""

class TextAnalyzer:
    """Text analyzer for sentiment and statistics."""
    
    CATEGORY = "text"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the text analyzer."""
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            },
            "optional": {
                "include_sentiment": ("BOOLEAN", {"default": True}),
                "include_statistics": ("BOOLEAN", {"default": True})
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("analysis_results",)
    FUNCTION = "analyze_text"
    
    def analyze_text(self, text, include_sentiment=True, include_statistics=True):
        """
        Analyze text for sentiment and statistics.
        
        Args:
            text (str): Text to analyze
            include_sentiment (bool): Whether to include sentiment analysis
            include_statistics (bool): Whether to include text statistics
            
        Returns:
            dict: Analysis results
        """
        result = {}
        
        if include_statistics:
            # Basic statistics
            words = text.split()
            result["statistics"] = {
                "character_count": len(text),
                "word_count": len(words),
                "line_count": len(text.splitlines()),
                "average_word_length": sum(len(word) for word in words) / max(len(words), 1)
            }
        
        if include_sentiment:
            # Basic sentiment analysis
            positive_words = ["good", "great", "excellent", "happy", "positive", "best", "love"]
            negative_words = ["bad", "awful", "terrible", "sad", "negative", "worst", "hate"]
            
            lowercase_text = text.lower()
            positive_count = sum(lowercase_text.count(word) for word in positive_words)
            negative_count = sum(lowercase_text.count(word) for word in negative_words)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
                
            result["sentiment"] = {
                "assessment": sentiment,
                "positive_word_count": positive_count,
                "negative_word_count": negative_count
            }
        
        return (result,)


class TextSummarizer:
    """Text summarizer using extraction-based methods."""
    
    CATEGORY = "text"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the text summarizer."""
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "summary_length": ("INTEGER", {"default": 3, "min": 1, "max": 10})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("summary",)
    FUNCTION = "summarize_text"
    
    def summarize_text(self, text, summary_length=3):
        """
        Summarize text using extraction-based method.
        
        Args:
            text (str): Text to summarize
            summary_length (int): Number of sentences in summary
            
        Returns:
            str: Summarized text
        """
        # This is a long-running operation, so it uses queue mode
        
        # Simple extractive text summarization
        sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        if not sentences:
            return ("No text to summarize.",)
            
        # Count word frequency
        words = text.lower().split()
        word_frequency = {}
        
        for word in words:
            if len(word) > 3:  # Ignore short words
                word_frequency[word] = word_frequency.get(word, 0) + 1
        
        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            for word in sentence.lower().split():
                if word in word_frequency:
                    score += word_frequency[word]
            sentence_scores[i] = score
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:summary_length]
        top_sentence_indices.sort()  # Keep original order
        
        summary = '. '.join(sentences[i] for i in top_sentence_indices)
        if not summary.endswith('.'):
            summary += '.'
            
        return (summary,)

# Module exports
NODE_CLASS_MAPPINGS = {
    "Text Analyzer": TextAnalyzer,
    "Text Summarizer": TextSummarizer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Analyzer": "Text Analyzer",
    "Text Summarizer": "Text Summarizer"
}

API_SERVER_QUEUE_MODE = {
    TextAnalyzer: False,  # Direct mode - fast execution
    TextSummarizer: True  # Queue mode - potentially slow for large texts
}
```

### Example 2: Image Processing API

Complete example of an image processing API package:

**custom_apis/image_processing/requirements.txt**:
```
Pillow>=9.0.0
numpy>=1.21.0
```

**custom_apis/image_processing/processors.py**:
```python
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
            image: Input image data (numpy array)
            width: Width of the thumbnail in pixels
            height: Height of the thumbnail in pixels
            maintain_aspect_ratio: Whether to maintain the aspect ratio
            quality: JPEG quality (1-100)
            format: Output format (JPEG, PNG, WEBP)
            
        Returns:
            Thumbnail image data as numpy array
        """
        try:
            # image is already a numpy array
            img = Image.fromarray(image)
            
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
            
            # Convert back to numpy array for return
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
            Resized image data as numpy array
        """
        try:
            # image is already a numpy array
            img = Image.fromarray(image)
            
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
            
            # Convert back to numpy array for return
            resized_image = np.array(img_resized)
            
            return (resized_image,)
            
        except Exception as e:
            raise Exception(f"Error resizing image: {str(e)}")
```

**custom_apis/image_processing/__init__.py**:
```python
"""
Image processing module for the Createve.AI API Server.

This module provides image processing capabilities including thumbnail generation
and image resizing.
"""

from .processors import ThumbnailGenerator, ImageResizer

# Map class names to class objects
NODE_CLASS_MAPPINGS = {
    "Thumbnail Generator": ThumbnailGenerator,
    "Image Resizer": ImageResizer
}

# Map class names to display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "Thumbnail Generator": "Thumbnail Generator",
    "Image Resizer": "Image Resizer"
}

# Define which API endpoints use queue mode
API_SERVER_QUEUE_MODE = {
    ThumbnailGenerator: False,  # Direct mode
    ImageResizer: False  # Direct mode
}
```

## Error Handling Best Practices

Proper error handling is essential for robust API endpoints:

```python
def process_data(self, input_data):
    try:
        # Validate input
        if not self._validate_input(input_data):
            raise ValueError("Invalid input data format")
            
        # Process data
        result = self._process(input_data)
        
        # Validate output
        if not self._validate_output(result):
            raise ValueError("Processing resulted in invalid output")
            
        return (result,)
        
    except ValueError as e:
        # Re-raise user input errors with clear message
        raise ValueError(f"Input validation error: {str(e)}")
        
    except Exception as e:
        # Log unexpected errors but provide generic message to client
        print(f"Error in process_data: {str(e)}")
        raise Exception("An unexpected error occurred during processing")
```

### Exception Guidelines

1. Use specific exception types to distinguish between error categories
2. Provide clear error messages that guide the user toward resolution
3. Include validation logic to catch errors early
4. Log detailed error information for debugging
5. For security, don't expose internal details to clients

## Testing Your API Endpoints

### Using the Swagger UI

The OpenAPI documentation and interactive testing UI is available at `http://localhost:43080/docs`.

### Using curl

For text-based APIs:

```bash
curl -X POST "http://localhost:43080/api/text_processing/textAnalyzer" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message."}'
```

For image-based APIs:

```bash
# Encode image to base64
BASE64_IMAGE=$(base64 -w 0 image.jpg)

# Send request
curl -X POST "http://localhost:43080/api/image_processing/thumbnailGenerator" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"image\": \"$BASE64_IMAGE\", \"width\": 100, \"height\": 100}"

# If the response contains an image, extract and save it
# grep the "thumbnail" field and extract the base64 part
```

### Using Python

```python
import requests
import json
import base64

# Configure the API
api_url = "http://localhost:43080/api/image_processing/imageResizer"
api_key = "YOUR_API_KEY"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Prepare image data
with open("image.jpg", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('ascii')

# Prepare request payload
payload = {
    "image": image_base64,
    "width": 800,
    "height": 600,
    "maintain_aspect_ratio": True
}

# Make the request
response = requests.post(api_url, headers=headers, json=payload)

# Process the response
if response.status_code == 200:
    result = response.json()
    
    # If the response contains an image, save it
    if "resized_image" in result:
        image_data = base64.b64decode(result["resized_image"])
        with open("resized_image.jpg", "wb") as f:
            f.write(image_data)
        print("Saved resized image to resized_image.jpg")
    else:
        print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

## Advanced Topics

### Working with Large Files

For processing large files, always use queue mode:

```python
class LargeFileProcessor:
    """Process large files asynchronously."""
    
    CATEGORY = "file_processing"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file": ("FILE",),
                "process_type": (["analyze", "transform", "extract"], {"default": "analyze"})
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "process_file"
    
    def process_file(self, file, process_type="analyze"):
        """Process a large file (using queue mode)."""
        # file is a path to a temporary file
        
        # Perform time-consuming processing
        result = self._process_file_by_type(file, process_type)
        
        # Clean up temporary file if needed
        
        return (result,)
```

### Dependencies Management

For APIs requiring external packages:

1. Create a `requirements.txt` file in your module directory
2. List all dependencies with version constraints
3. The server will automatically install these when loading your module

Example `requirements.txt`:
```
numpy>=1.20.0
Pillow>=9.0.0
scikit-learn>=1.0.0
transformers>=4.15.0
```

## Best Practices Summary

1. **Structure and Organization**
   - Keep related functionality in the same module
   - Use clear naming conventions for classes and methods
   - Organize complex modules as packages with multiple files

2. **Documentation**
   - Add detailed docstrings to all classes and methods
   - Include parameter descriptions and return value explanations
   - Document expected input formats and constraints

3. **Input Validation**
   - Validate all inputs before processing
   - Provide clear error messages for invalid inputs
   - Use appropriate type constraints in INPUT_TYPES

4. **Performance Considerations**
   - Use queue mode for operations that take more than 1-2 seconds
   - Process large files in chunks when possible
   - Be mindful of memory usage with large data structures

5. **Error Handling**
   - Use try/except blocks to catch and handle errors
   - Return meaningful error messages
   - Log detailed error information for debugging

6. **Testing**
   - Test your API with various input combinations
   - Test edge cases and error conditions
   - Verify performance with large inputs

7. **Security**
   - Validate and sanitize all inputs
   - Be careful with file operations
   - Don't expose sensitive information in error messages

By following these guidelines, you can create robust, efficient, and user-friendly API endpoints for the Createve.AI API Server.

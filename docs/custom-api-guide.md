# Creating Custom API Modules

This guide explains how to create custom API modules for the Createve.AI API Server.

## Introduction

The Createve.AI API Server allows you to create custom API endpoints by writing Python classes following a specific pattern. The server will dynamically load these classes and expose them as REST API endpoints.

Custom API modules are stored in the `custom_apis` directory and can be organized in any directory structure within it. The server will recursively scan this directory for Python files and import them.

## Basic Structure

### File Organization

A typical custom API module consists of:

- One or more Python files containing API classes
- An `__init__.py` file to expose the API classes
- (Optional) A `requirements.txt` file for dependencies

For example:

```
custom_apis/
├── text_processing.py           # A single file module
├── image_processing/            # A package module
│   ├── __init__.py
│   ├── filters.py
│   ├── transformations.py
│   └── requirements.txt         # Dependencies for image processing
└── audio/
    ├── __init__.py
    ├── conversion.py
    ├── effects.py
    └── requirements.txt         # Dependencies for audio processing
```

### Class Structure

Each API class must follow this structure:

```python
class MyApiEndpoint:
    """Description of what this API endpoint does."""
    
    # Optional category for grouping in documentation
    CATEGORY = "my_category"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the API endpoint."""
        return {
            "required": {
                "param1": ("STRING", {"multiline": False}),
                "param2": ("INTEGER", {"default": 1, "min": 1, "max": 10}),
                # ...
            },
            "optional": {
                "param3": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                # ...
            }
        }
    
    # Define return types
    RETURN_TYPES = ("STRING", "INTEGER")
    
    # Optional human-readable names for return values
    RETURN_NAMES = ("result", "count")
    
    # Name of the method to call
    FUNCTION = "process"
    
    def process(self, param1, param2, param3=0.5):
        """Main processing function for the API endpoint."""
        # Process the inputs
        result = f"Processed: {param1}"
        count = param2 + int(param3 * 10)
        
        # Return the results as a tuple matching RETURN_TYPES
        return (result, count)
```

### Module Exports

Each module must export its API classes using three dictionaries in the `__init__.py` file:

```python
# Map class names to class objects
NODE_CLASS_MAPPINGS = {
    "My API Endpoint": MyApiEndpoint,
    "Another API": AnotherApiClass,
}

# Map class names to display names (optional but recommended)
NODE_DISPLAY_NAME_MAPPINGS = {
    "My API Endpoint": "My API Endpoint",
    "Another API": "Another API with a Longer Name",
}

# Define which API endpoints use queue mode (for long-running operations)
API_SERVER_QUEUE_MODE = {
    MyApiEndpoint: False,  # Direct mode (default)
    AnotherApiClass: True,  # Queue mode
}
```

## Supported Data Types

The server supports the following data types for inputs and outputs:

| Type | Description | Example |
|------|-------------|---------|
| `STRING` | Text string | `("STRING", {"multiline": False})` |
| `INTEGER` | Integer number | `("INTEGER", {"default": 1, "min": 0, "max": 100})` |
| `FLOAT` | Floating-point number | `("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0})` |
| `BOOLEAN` | Boolean (true/false) | `("BOOLEAN", {"default": True})` |
| `IMAGE` | Image data (base64 encoded) | `("IMAGE",)` |
| `VIDEO` | Video data (base64 encoded) | `("VIDEO",)` |
| `FILE` | File data (base64 encoded) | `("FILE",)` |
| `DICT` | Dictionary/object | `("DICT",)` |
| `LIST` | Array/list | `("LIST",)` |

## Input Type Parameters

When defining input types, you can specify additional parameters for each input:

```python
"param_name": ("TYPE", {
    "default": value,       # Default value
    "min": value,           # Minimum value (for numeric types)
    "max": value,           # Maximum value (for numeric types)
    "step": value,          # Step value (for numeric types)
    "multiline": boolean,   # For STRING, whether it's a multi-line text area
    "placeholder": string,  # Placeholder text for documentation
})
```

For enum types (selection from a list), use a list as the type:

```python
"mode": (["option1", "option2", "option3"],)
```

## Queue Mode vs. Direct Mode

The API server supports two modes of operation for API endpoints:

1. **Direct Mode** (default): The API endpoint is executed immediately, and the result is returned in the same request.
2. **Queue Mode**: The API endpoint is queued for execution, and a queue ID is returned. The client must then check the queue status using this ID to get the result.

Use Queue Mode for long-running operations that may take more than a few seconds to complete. Use Direct Mode for operations that complete quickly.

To specify the mode, use the `API_SERVER_QUEUE_MODE` dictionary in your `__init__.py` file:

```python
API_SERVER_QUEUE_MODE = {
    MyQuickApiEndpoint: False,  # Direct mode
    MyLongRunningApiEndpoint: True,  # Queue mode
}
```

## Handling Files and Images

The API server automatically handles base64 encoding/decoding for file types (`IMAGE`, `VIDEO`, `FILE`). 

When a client sends a base64-encoded file to your API endpoint, the server will automatically decode it and pass it to your function as the appropriate type:
- `IMAGE` will be converted to a numpy array
- `VIDEO` and `FILE` will be saved to a temporary file, and the path will be passed to your function

Similarly, when your function returns a file type, the server will automatically encode it as base64 before sending it to the client.

## Example: Text Processing API

Here's a complete example of a text processing API module:

```python
# text_processing.py
class TextAnalyzer:
    """Text analyzer for sentiment and statistics."""
    
    CATEGORY = "text"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for node."""
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
        """Analyze text for sentiment and statistics."""
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
            # Very basic sentiment analysis
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

# Define exports for __init__.py
NODE_CLASS_MAPPINGS = {
    "Text Analyzer": TextAnalyzer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Analyzer": "Text Analyzer",
}

API_SERVER_QUEUE_MODE = {
    TextAnalyzer: False  # Direct mode
}
```

## Testing Your API Endpoints

You can test your API endpoints using the Swagger UI at `http://localhost:43080/docs` or using tools like curl or Postman.

Example curl command:

```bash
curl -X POST "http://localhost:43080/api/text_processing/textAnalyzer" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message."}'
```

Example Python code:

```python
import requests

api_url = "http://localhost:43080/api/text_processing/textAnalyzer"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "text": "This is a test message."
}

response = requests.post(api_url, headers=headers, json=payload)
print(response.json())
```

## Best Practices

1. **Keep functions focused**: Each API endpoint should do one thing well.
2. **Provide clear documentation**: Use docstrings to describe what your API endpoint does.
3. **Handle errors gracefully**: Catch and handle exceptions in your code.
4. **Use queue mode for long-running operations**: If your function takes more than a few seconds to complete, use queue mode.
5. **Include input validation**: Validate your inputs and provide meaningful error messages.
6. **Use dependencies wisely**: Include a `requirements.txt` file if your module requires external packages.
7. **Follow naming conventions**: Use descriptive names for your classes and methods.
8. **Categories**: Group related API endpoints with the same category.

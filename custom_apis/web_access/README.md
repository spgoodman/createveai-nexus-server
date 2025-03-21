# Web Access API Module

A powerful web access module for the Createve.AI API Server that provides capabilities for retrieving web page information and performing automated web actions.

## Features

- Web page information retrieval and link extraction
- Dynamic content support (JavaScript-rendered pages)
- Multi-step action sequences with state validation
- Session state management with disk persistence
- Screenshot capture
- Queue mode support for long-running operations
- Flexible selector types (CSS, XPath, ID, name, class)
- MCP integration

## Security Features

- URL validation and sanitization
- Rate limiting (10 requests per minute)
- Session timeout (1 hour)
- Maximum session limit (1000 concurrent sessions)
- Secure headers configuration
- SSL verification options
- Generic error messages (no internal details exposed)
- Selenium security hardening:
  - Headless mode
  - Disabled JavaScript (optional)
  - Disabled images
  - Disabled extensions
  - Disabled pop-ups
  - Custom user agent
  - Sandboxing
- Request timeout handling
- Thread-safe session management
- Automatic cleanup of expired sessions

## Installation

1. The module is part of the Createve.AI API Server's custom_apis directory
2. Required dependencies are listed in `requirements.txt`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## API Endpoints

### Web Info Retriever

Retrieves information from web pages including content, links, and metadata.

#### Parameters

Required:
- `url` (STRING): The URL to retrieve information from (must be http/https)

Optional:
- `wait_for_load` (INTEGER, default: 5): Time to wait for page load in seconds (1-60)
- `extract_links` (BOOLEAN, default: true): Whether to extract links from the page
- `dynamic_load` (BOOLEAN, default: false): Whether to use Selenium for JavaScript-rendered content
- `session_id` (STRING): Optional session ID for maintaining state
- `verify_ssl` (BOOLEAN, default: true): Whether to verify SSL certificates

#### Example Usage

```python
response = api.post("/api/web_access/webInfoRetriever", json={
    "url": "https://example.com",
    "extract_links": true,
    "dynamic_load": true,
    "wait_for_load": 10,
    "session_id": "my-session-123"
})

result = response.json()
# Returns: {
#     "url": "https://example.com",
#     "timestamp": 1616345678.9,
#     "success": true,
#     "title": "Example Domain",
#     "meta_description": "Example description",
#     "text_content": "...",
#     "links": [
#         {
#             "url": "https://example.com/page",
#             "text": "Link Text",
#             "title": "Link Title"
#         },
#         ...
#     ]
# }
```

### Web Action Performer

Executes individual actions on web pages such as clicking buttons, filling forms, and submitting data.

#### Parameters

Required:
- `url` (STRING): The URL to perform the action on (must be http/https)
- `action` (ENUM): Type of action to perform
  - "click": Click an element
  - "input": Input text into a form field
  - "submit": Submit a form
  - "wait": Wait for a specified time
  - "navigate": Navigate to a URL
- `selector` (STRING): Element selector (CSS selector, XPath, etc.)

Optional:
- `input_value` (STRING): Value to input (for input action)
- `wait_time` (INTEGER, default: 5): Time to wait in seconds (1-60)
- `session_id` (STRING): Session ID for maintaining state
- `selector_type` (ENUM, default: "css"): Type of selector
  - "css": CSS selector
  - "xpath": XPath
  - "id": Element ID
  - "name": Element name
  - "class": Class name
- `verify_ssl` (BOOLEAN, default: true): Whether to verify SSL certificates

#### Example Usage

```python
# Click a button
response = api.post("/api/web_access/webActionPerformer", json={
    "url": "https://example.com",
    "action": "click",
    "selector": "#submit-button",
    "selector_type": "css",
    "wait_time": 10,
    "session_id": "my-session-123"
})

result = response.json()
# Returns: {
#     "url": "https://example.com",
#     "action": "click",
#     "selector": "#submit-button",
#     "timestamp": 1616345678.9,
#     "success": true,
#     "page_url": "https://example.com",
#     "page_title": "Example Form",
#     "screenshot": "base64_encoded_screenshot..."
# }
```

### Action Sequence Manager

Manages sequences of web actions, enabling complex multi-step operations with state validation.

#### Parameters

Required:
- `action` (ENUM): Operation to perform
  - "create": Create a new sequence
  - "execute": Execute an existing sequence
  - "delete": Delete a sequence
  - "list": List available sequences
- `sequence_name` (STRING): Name of the sequence to manage

Optional:
- `session_id` (STRING): Session ID for maintaining state
- `steps` (STRING): JSON array of action steps (required for "create" action)

#### Step Definition

Each step in a sequence is defined as:
```json
{
    "action": "click|input|submit|wait|navigate",
    "url": "https://example.com",
    "selector": "#some-element",
    "input_value": "optional value for input action",
    "wait_time": 5,
    "selector_type": "css|xpath|id|name|class",
    "verify_ssl": true
}
```

#### Example Usage

```python
# Create a login sequence
steps = [
    {
        "action": "input",
        "url": "https://example.com/login",
        "selector": "input[name='username']",
        "input_value": "user123",
        "selector_type": "css"
    },
    {
        "action": "input",
        "url": "https://example.com/login",
        "selector": "input[name='password']",
        "input_value": "pass123",
        "selector_type": "css"
    },
    {
        "action": "click",
        "url": "https://example.com/login",
        "selector": "#login-button",
        "selector_type": "css"
    }
]

# Create sequence
response = api.post("/api/web_access/actionSequenceManager", json={
    "action": "create",
    "sequence_name": "login-sequence",
    "session_id": "my-session-123",
    "steps": json.dumps(steps)
})

# Execute sequence
response = api.post("/api/web_access/actionSequenceManager", json={
    "action": "execute",
    "sequence_name": "login-sequence",
    "session_id": "my-session-123"
})

result = response.json()
# Returns: {
#     "action": "execute",
#     "sequence_name": "login-sequence",
#     "timestamp": 1616345678.9,
#     "success": true,
#     "results": [
#         {
#             "success": true,
#             "page_url": "...",
#             "page_title": "..."
#         },
#         ...
#     ]
# }

# List sequences
response = api.post("/api/web_access/actionSequenceManager", json={
    "action": "list",
    "sequence_name": "*",
    "session_id": "my-session-123"
})
```

## Session Management

### Features
- Disk persistence of sessions
- Automatic session recovery after server restart
- Session state validation between actions
- Action sequence storage per session
- Automatic cleanup of expired sessions

### Session Data Stored
- Cookies
- Headers
- Action sequences
- State validation data
- Timestamps for creation and last use

## MCP Integration

All endpoints are available as MCP tools:

```python
# Using MCP tools
result = mcp.use_tool("webInfoRetriever", {
    "url": "https://example.com",
    "extract_links": True,
    "session_id": "my-session-123"
})

result = mcp.use_tool("actionSequenceManager", {
    "action": "execute",
    "sequence_name": "login-sequence",
    "session_id": "my-session-123"
})
```

## Queue Mode

All endpoints operate in queue mode for handling long-running operations. When using the API, you'll receive a queue ID that can be used to check the status and retrieve results:

```python
# Initial request
response = api.post("/api/web_access/actionSequenceManager", json={
    "action": "execute",
    "sequence_name": "login-sequence"
})
queue_id = response.json()["queue_id"]

# Check status
status = api.post("/api/queue", json={
    "queue_id": queue_id
})
```

## Error Handling

The API provides sanitized error information in case of failures:

```json
{
    "success": false,
    "error": "Network error occurred",
    "timestamp": 1616345678.9,
    "url": "https://example.com"
}
```

Common error types:
- URL validation errors
- Rate limit exceeded
- Network errors
- Element not found
- Session timeout/limit reached
- SSL verification errors
- Sequence not found
- Invalid sequence format
- State validation failures

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 10 requests per minute per endpoint
- Applies to both individual actions and sequences
- Returns error when limit exceeded

## Dependencies

- requests>=2.31.0: HTTP requests
- beautifulsoup4>=4.12.0: HTML parsing
- selenium>=4.15.0: Browser automation
- webdriver-manager>=4.0.0: WebDriver management
- urllib3>=2.0.0: HTTP client
- aiohttp>=3.9.0: Async HTTP
- html2text>=2020.1.16: HTML to text conversion
- lxml>=4.9.0: XML/HTML processing
- validators>=0.20.0: URL validation

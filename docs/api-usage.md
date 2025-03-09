# API Usage Guide

This guide explains how to use the Createve.AI API Server endpoints from client applications.

## Authentication

All API requests require authentication using an API key. The API key should be included in the `Authorization` header as a Bearer token:

```
Authorization: Bearer YOUR_API_KEY
```

API keys are defined in the `config.yaml` file:

```yaml
security:
  api_keys:
    - key: "sk-apiservertest1"
      description: "API Key 1"
    - key: "sk-apiservertest2"
      description: "API Key 2"
```

## API Endpoints

API endpoints are exposed at `/api/{module}/{endpoint}` where:
- `{module}` is the name of the API module (e.g., `text_processing`)
- `{endpoint}` is the name of the API endpoint (e.g., `textAnalyzer`)

### Direct API Calls

For direct API calls (non-queued), send a POST request to the endpoint with the required parameters:

```http
POST /api/text_processing/textAnalyzer HTTP/1.1
Host: localhost:43080
Authorization: Bearer sk-apiservertest1
Content-Type: application/json

{
  "text": "This is a sample text to analyze."
}
```

The response will be a JSON object with the result:

```json
{
  "analysis_results": {
    "statistics": {
      "character_count": 32,
      "word_count": 7,
      "line_count": 1,
      "average_word_length": 3.57
    },
    "sentiment": {
      "assessment": "neutral",
      "positive_word_count": 0,
      "negative_word_count": 0
    }
  }
}
```

### Queued API Calls

For queued API calls (long-running operations), the process is two-step:

1. Send a POST request to the endpoint to queue the operation:

```http
POST /api/text_processing/textSummarizer HTTP/1.1
Host: localhost:43080
Authorization: Bearer sk-apiservertest1
Content-Type: application/json

{
  "text": "This is a long text that needs to be summarized...",
  "summary_length": 2
}
```

The response will be a JSON object with a queue ID:

```json
{
  "queue_id": "224dd457-b251-490f-827e-92b708edb032"
}
```

2. Send a POST request to check the queue status:

```http
POST /api/text_processing/textSummarizer/queue HTTP/1.1
Host: localhost:43080
Authorization: Bearer sk-apiservertest1
Content-Type: application/json

{
  "queue_id": "224dd457-b251-490f-827e-92b708edb032"
}
```

If the operation is still in progress, the response will be the same queue ID:

```json
{
  "queue_id": "224dd457-b251-490f-827e-92b708edb032"
}
```

If the operation is complete, the response will be the result:

```json
{
  "summary": "This is a summary of the long text."
}
```

If there was an error, the response will include the error details:

```json
{
  "error": 500,
  "description": "Error processing request",
  "details": {
    "message": "Error details here"
  }
}
```

## File Handling

For API endpoints that accept or return file data (`IMAGE`, `VIDEO`, `FILE`), the data should be base64 encoded in the JSON request/response.

For example, to send an image to an API endpoint:

```http
POST /api/image_processing/resizeImage HTTP/1.1
Host: localhost:43080
Authorization: Bearer sk-apiservertest1
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "width": 800,
  "height": 600
}
```

The response will include the processed image as a base64-encoded string:

```json
{
  "resized_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
}
```

## Error Handling

Errors are returned as JSON responses with HTTP status codes:

- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: API endpoint not found
- `422 Unprocessable Entity`: Invalid input data
- `500 Internal Server Error`: Server error

The error response includes details about the error:

```json
{
  "error": 400,
  "description": "Invalid input",
  "details": {
    "field": "text",
    "message": "text is required"
  }
}
```

## OpenAPI Documentation

The API server provides OpenAPI documentation at:

```
http://localhost:43080/docs
```

This interactive documentation allows you to explore the available endpoints, see the required parameters, and test the endpoints directly.

## Client Examples

### Python

```python
import requests
import json
import base64

# Define API endpoint and API key
api_url = "http://localhost:43080/api/text_processing/textAnalyzer"
api_key = "sk-apiservertest1"

# Set up headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Prepare request data
data = {
    "text": "This is a test message."
}

# Make the request
response = requests.post(api_url, headers=headers, json=data)

# Print the response
print(f"Status code: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

### JavaScript

```javascript
async function callApi() {
  const apiUrl = 'http://localhost:43080/api/text_processing/textAnalyzer';
  const apiKey = 'sk-apiservertest1';
  
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: 'This is a test message.'
    })
  });
  
  const data = await response.json();
  console.log('Status code:', response.status);
  console.log('Response data:', data);
}

callApi();
```

### cURL

```bash
curl -X POST "http://localhost:43080/api/text_processing/textAnalyzer" \
  -H "Authorization: Bearer sk-apiservertest1" \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message."}'
```

## Rate Limiting and Quotas

Currently, the API server does not implement rate limiting or quotas. However, the server does have a maximum queue size and process timeout configurable in the `config.yaml` file:

```yaml
processing:
  max_threads: 10
  max_queue_size: 100
  process_timeout_seconds: 300
```

If the queue is full, the server will return a 500 error with the message "Queue is full".

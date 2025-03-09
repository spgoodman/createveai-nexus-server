# MCP Integration Guide

This guide explains how to use the Model Context Protocol (MCP) functionality of the Createve.AI Nexus Server.

## Overview

The Model Context Protocol (MCP) is a standard for enabling AI assistants to interact with external systems. The Createve.AI Nexus Server implements MCP to allow AI assistants to access and execute API endpoints as tools, and access server resources.

## Connection

Connect to the MCP server using a WebSocket connection:

```
ws://localhost:43080/mcp
```

Once connected, the server will send a `server_info` message with details about the server.

## Authentication

If authentication is enabled (`mcp_require_authentication` is set to `true` in the config), you need to provide authentication credentials. The server uses the same API keys for MCP authentication as it does for REST API authentication.

## Capabilities

The MCP server supports two main capabilities:

1. **Tools**: API endpoints exposed as executable tools
2. **Resources**: Server data exposed as accessible resources

To query the server's capabilities, send a `capabilities_request` message:

```json
{
  "type": "capabilities_request"
}
```

The server will respond with:

```json
{
  "type": "capabilities_response",
  "capabilities": {
    "tools": true,
    "resources": true
  }
}
```

## Tools

Tools are automatically created from API endpoints defined in the `custom_apis` directory. Each API endpoint becomes an MCP tool with the same input and output schema.

### Listing Tools

To list available tools, send a `list_tools_request` message:

```json
{
  "type": "list_tools_request"
}
```

The server will respond with:

```json
{
  "type": "list_tools_response",
  "tools": [
    {
      "name": "text_processing_textAnalyzer",
      "description": "Text analyzer for sentiment and statistics.",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string"
          },
          "include_sentiment": {
            "type": "boolean",
            "default": true
          },
          "include_statistics": {
            "type": "boolean",
            "default": true
          }
        },
        "required": ["text"]
      }
    },
    {
      "name": "text_processing_textSummarizer",
      "description": "Text summarizer using extraction-based methods.",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string"
          },
          "summary_length": {
            "type": "integer",
            "default": 3,
            "minimum": 1,
            "maximum": 10
          }
        },
        "required": ["text"]
      }
    }
  ]
}
```

### Executing a Tool

To execute a tool, send a `call_tool_request` message:

```json
{
  "type": "call_tool_request",
  "request_id": "abc123",
  "name": "text_processing_textAnalyzer",
  "arguments": {
    "text": "This is a test message.",
    "include_sentiment": true,
    "include_statistics": true
  }
}
```

For direct API endpoints (not queue mode), the server will respond immediately:

```json
{
  "type": "call_tool_response",
  "request_id": "abc123",
  "content": [
    {
      "type": "json",
      "json": {
        "analysis_results": {
          "statistics": {
            "character_count": 21,
            "word_count": 5,
            "line_count": 1,
            "average_word_length": 3.4
          },
          "sentiment": {
            "assessment": "neutral",
            "positive_word_count": 0,
            "negative_word_count": 0
          }
        }
      }
    }
  ],
  "is_error": false
}
```

For queue mode API endpoints, you'll get a queue ID that you can use to check the status:

```json
{
  "type": "call_tool_response",
  "request_id": "abc123",
  "content": [
    {
      "type": "json",
      "json": {
        "queue_id": "224dd457-b251-490f-827e-92b708edb032"
      }
    }
  ],
  "is_error": false
}
```

## Resources

Resources are server data exposed for access by MCP clients. The Createve.AI Nexus Server exposes several types of resources:

1. **Queue Resources**: Information about queued requests
2. **Documentation Resources**: Server documentation and API specifications
3. **Log Resources**: Server logs (if enabled)

### Listing Resources

To list available resources, send a `list_resources_request` message:

```json
{
  "type": "list_resources_request"
}
```

The server will respond with:

```json
{
  "type": "list_resources_response",
  "resources": [
    {
      "uri": "docs://openapi.json",
      "name": "OpenAPI Schema",
      "description": "Full OpenAPI specification for the API server",
      "mime_type": "application/json"
    },
    {
      "uri": "docs://readme",
      "name": "Server Documentation",
      "description": "Documentation for the Createve.AI Nexus Server",
      "mime_type": "text/markdown"
    },
    {
      "uri": "logs://server",
      "name": "Server Logs",
      "description": "Recent server logs",
      "mime_type": "text/plain"
    }
  ]
}
```

### Listing Resource Templates

Some resources are defined as templates, where parameters can be filled in to access specific resources. To list resource templates, send a `list_resource_templates_request` message:

```json
{
  "type": "list_resource_templates_request"
}
```

The server will respond with:

```json
{
  "type": "list_resource_templates_response",
  "resource_templates": [
    {
      "uri_template": "queue://{queue_id}",
      "name": "Queue Status",
      "description": "Status and result for a queued request",
      "mime_type": "application/json"
    },
    {
      "uri_template": "docs://api/{endpoint}",
      "name": "API Endpoint Documentation",
      "description": "Documentation for a specific API endpoint",
      "mime_type": "application/json"
    }
  ]
}
```

### Reading a Resource

To read a resource, send a `read_resource_request` message:

```json
{
  "type": "read_resource_request",
  "request_id": "def456",
  "uri": "docs://readme"
}
```

The server will respond with the resource content:

```json
{
  "type": "read_resource_response",
  "request_id": "def456",
  "contents": [
    {
      "uri": "docs://readme",
      "mime_type": "text/markdown",
      "text": "# Createve.AI Nexus Server\n\nA versatile server that combines REST API and Model Context Protocol (MCP) functionality in a single unified platform.\n\n..."
    }
  ]
}
```

For a queue resource, you would use a URI like `queue://224dd457-b251-490f-827e-92b708edb032`:

```json
{
  "type": "read_resource_request",
  "request_id": "ghi789",
  "uri": "queue://224dd457-b251-490f-827e-92b708edb032"
}
```

The server will respond with the queue status:

```json
{
  "type": "read_resource_response",
  "request_id": "ghi789",
  "contents": [
    {
      "uri": "queue://224dd457-b251-490f-827e-92b708edb032",
      "mime_type": "application/json",
      "text": "{\"status\":\"completed\",\"result\":{\"summary\":\"This is a summary of the text.\"},\"created_at\":1648253647.8,\"updated_at\":1648253650.2}"
    }
  ]
}
```

## Error Handling

If an error occurs, the server will respond with an error message:

```json
{
  "type": "error",
  "code": "invalid_request",
  "message": "Tool name is required",
  "request_id": "abc123"
}
```

Common error codes include:

- `invalid_json`: Invalid JSON in the request
- `unknown_message_type`: Unknown message type
- `invalid_request`: Missing or invalid request parameters
- `tool_not_found`: Requested tool not found
- `resource_not_found`: Requested resource not found
- `internal_error`: Internal server error

## Examples

### Complete Tool Execution Flow

Here's a complete example of executing a tool:

1. Connect to the WebSocket
2. Receive server info
3. List available tools
4. Execute a tool
5. Receive the result

```javascript
const ws = new WebSocket('ws://localhost:43080/mcp');

ws.onopen = () => {
  console.log('Connected to MCP server');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  if (message.type === 'server_info') {
    // List tools
    ws.send(JSON.stringify({
      type: 'list_tools_request'
    }));
  } else if (message.type === 'list_tools_response') {
    // Execute a tool
    ws.send(JSON.stringify({
      type: 'call_tool_request',
      request_id: 'abc123',
      name: 'text_processing_textAnalyzer',
      arguments: {
        text: 'This is a test message.'
      }
    }));
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from MCP server');
};
```

### Checking Queue Status

For a queue mode API, you would check the queue status periodically:

```javascript
// After receiving a queue ID from a tool execution
const queueId = '224dd457-b251-490f-827e-92b708edb032';

function checkQueueStatus() {
  ws.send(JSON.stringify({
    type: 'read_resource_request',
    request_id: 'ghi789',
    uri: `queue://${queueId}`
  }));
}

// Check every 2 seconds
const intervalId = setInterval(checkQueueStatus, 2000);

// In the message handler, check for completion
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'read_resource_response' && 
      message.request_id === 'ghi789') {
    const content = JSON.parse(message.contents[0].text);
    
    if (content.status === 'completed' || content.status === 'failed') {
      clearInterval(intervalId);
      console.log('Final result:', content);
    }
  }
};
```

## Integration with AI Assistants

To integrate the MCP server with an AI assistant:

1. Configure the AI assistant to connect to the MCP server
2. The assistant will discover available tools and resources
3. The assistant can execute tools and access resources as needed

For Claude, this would typically be configured in the Claude Dev environment settings.

## Security Considerations

- All MCP communications should be secured with TLS in production
- API keys should be kept secure and rotated regularly
- Consider restricting the tools and resources that are exposed to MCP clients
- Monitor MCP usage for suspicious activity

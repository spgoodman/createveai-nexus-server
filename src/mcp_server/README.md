# Createve.AI Nexus MCP Client Server

A TypeScript implementation of an MCP server that connects to a remote Createve.AI Nexus server and exposes its functionality through the Model Context Protocol.

## Overview

This MCP client server acts as a bridge between AI assistants that support the Model Context Protocol and a remote Createve.AI Nexus server. It dynamically generates MCP tools and resources based on the API endpoints available on the Nexus server.

## Features

- **Local Execution**: Runs on the client machine, avoiding direct WebSocket connections to remote servers
- **API Abstraction**: Interacts with the remote Nexus server via REST APIs
- **Enhanced Security**: Keeps API keys local to the client machine
- **Dynamic API Discovery**: Automatically discovers available APIs through OpenAPI schema
- **LLM-Optimized Interface**: Formats responses in a way that's optimal for LLM consumption

## Installation

### Prerequisites

- Node.js 18.0.0 or higher
- Access to a Createve.AI Nexus Server instance

### Build from Source

```bash
# Clone the repository
git clone https://github.com/createve-ai/createveai-nexus-server.git

# Navigate to the MCP server directory
cd createveai-nexus-server/src/mcp_server

# Install dependencies
npm install

# Build the project
npm run build
```

## Configuration

The MCP client server can be configured using environment variables or command-line arguments:

### Environment Variables

- `CREATEVEAI_NEXUS_BASE_URL`: The base URL of the Nexus server (required)
- `CREATEVEAI_NEXUS_API_KEY`: API key for authentication (required)
- `CREATEVEAI_NEXUS_API`: Optional API filter to limit exposed endpoints
- `DEBUG`: Set to "createveai-nexus-mcp" to enable debug logging

### Command-Line Arguments

- `--base-url <URL>`: The base URL of the Nexus server
- `--api-key <KEY>`: API key for authentication
- `--api <FILTER>`: Optional API filter
- `--debug`: Enable debug logging

## Integration with AI Assistants

### Claude Integration

Add the MCP server to your Claude environment by modifying the MCP settings configuration file:

```json
{
  "mcpServers": {
    "createveai-nexus": {
      "command": "node",
      "args": ["/path/to/createveai-nexus-server/src/mcp_server/build/index.js"],
      "env": {
        "CREATEVEAI_NEXUS_BASE_URL": "https://nexus.createve.ai",
        "CREATEVEAI_NEXUS_API_KEY": "your-api-key-here"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Available Resources

The MCP client server exposes the following resources:

- `queue://{queueId}`: Status and result for a queued request
- `schema://openapi`: OpenAPI schema for all available APIs
- `schema://{api}`: OpenAPI schema for a specific API (when using API filter)
- `docs://readme`: Server documentation
- `docs://{path}`: Specific documentation resource

## Available Tools

The MCP client server dynamically creates tools based on the API endpoints available on the Nexus server. These tools follow the naming convention of the API paths with slashes replaced by underscores.

For example, an API endpoint at `/api/text_processing/analyze` would be available as the MCP tool `text_processing_analyze`.

## Development

### Project Structure

```
src/mcp_server/
├── package.json               # Node.js package configuration
├── tsconfig.json              # TypeScript configuration
├── src/
│   ├── index.ts               # Entry point
│   ├── config.ts              # Configuration management
│   ├── nexus-client.ts        # REST API client
│   ├── tools/                 # Tool implementation
│   │   └── index.ts           # Tool registration
│   ├── resources/             # Resource implementation
│   │   └── index.ts           # Resource registration
│   └── utils/                 # Utility functions
│       └── schema-converter.ts # OpenAPI to Zod schema converter
```

## License

This project is licensed under the Apache License 2.0.

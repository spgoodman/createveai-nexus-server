# Createve.AI Nexus Server

A versatile server that combines REST API and Model Context Protocol (MCP) functionality in a single unified platform.

## Features

- **Dual Protocol Support**: 
  - REST API for traditional HTTP-based integration
  - MCP for WebSocket-based AI assistant integration
- **Dynamic API Loading**: Load API modules from a configurable directory
- **API Key Authentication**: Secure all endpoints with API key authentication
- **Queue System**: Handle long-running processes with a robust queue system
- **Auto-Reload**: Automatically reload when API files change
- **OpenAPI Documentation**: Interactive API documentation with Swagger UI
- **File Type Handling**: Base64 encoding/decoding for image and file types
- **Logging & Error Handling**: Comprehensive logging and structured error responses
- **State Persistence**: Queue state persistence for recovery after restart
- **Containerization**: Compatible with Docker and systemd

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [Architecture Overview](docs/architecture.md) - Details of the server architecture
- [Custom API Guide](docs/custom-api-guide.md) - How to create custom API modules
- [API Usage Guide](docs/api-usage.md) - How to use the API endpoints
- [MCP Integration Guide](docs/mcp-integration.md) - How to use the MCP functionality

## Configuration

The config is stored in config.yaml. This contains settings for both the API server and MCP functionality.

```yaml
apiserver:
  host: localhost # Host to listen on
  port: 43080 # Port to listen on
  debug: true # Debug to console
  log: true # Log to file
  log_file: logs/apiserver.log # Log file path
  apis_dir: custom_apis # Directory containing API modules to load

security:
  api_keys: # API keys for authentication
    - key: "sk-apiservertest1"
      description: "API Key 1"

mcp_server:
  enabled: true # Enable MCP server functionality
  server_info:
    name: "createveai-nexus" # Server name
    version: "1.0.0" # Server version
    description: "Createve.AI Nexus Server MCP Interface" # Server description
  tools:
    auto_map_apis: true # Automatically map API endpoints to MCP tools
```

An alternative config file can be specified when launching the server with `python main.py --config ./config.yaml`

## API Definitions

The APIs are loaded from the defined custom_apis folder, each in a subfolder structure that contains an __init__.py file which will load the relevant classes from the same/sub-folders.

The API definitions are inspired by ComfyUI's custom nodes, and use the same structures for defining inputs and outputs. These APIs are exposed both as REST endpoints and MCP tools.

```python
class TextAnalyzer:
    """Text analyzer for sentiment and statistics."""
    
    CATEGORY = "text"
    
    @classmethod    
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
            },
            "optional": {
                "include_sentiment": ("BOOLEAN", {"default": True})
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("analysis_results",)
    FUNCTION = "analyze_text"
    
    def analyze_text(self, text, include_sentiment=True):
        # Implementation here
        return (result,)
```

## Installation

Clone this repo and run start.sh to set up a python virtual environment and start the server.

```bash
git clone https://github.com/spgoodman/createveai-nexus-server.git
cd createveai-nexus-server
chmod +x start.sh
./start.sh
```

## Running as a service

Recommended: Use docker compose to start the server as a docker container.

```bash
docker-compose up -d
```

Alternative: Use service.sh to install as a systemd service on Ubuntu.

```bash
# Install as service
./service.sh install -U user -G group

# Uninstall service
./service.sh uninstall
```

## Command Line Options

The server can be started with the following command line options:

```bash
python main.py [--config CONFIG_PATH] [--host HOST] [--port PORT] [--reload]
```

## Using the MCP Functionality

The MCP functionality allows AI assistants to interact with the server using the Model Context Protocol. This enables assistants to:

1. Discover available tools (derived from API endpoints)
2. Execute tools with parameters
3. Access resources like queue status and documentation

To connect to the MCP server, use a WebSocket connection to `ws://localhost:43080/mcp`.

## Testing

The server includes test scripts for verifying functionality:

```bash
# Test API functionality
python test_api.py

# Test MCP functionality
python test_mcp.py
```

## License

This project is proprietary and confidential.

# Setup Guide

This guide provides instructions for installing, configuring, using, and testing the Createve.AI Nexus Server.

## Installation

1.  Clone this repo:

    ```bash
    git clone https://github.com/spgoodman/createveai-nexus-server.git
    cd createveai-nexus-server
    ```

2.  Run `start.sh` to set up a Python virtual environment and start the server:

    ```bash
    chmod +x start.sh
    ./start.sh
    ```

## Running as a Service

### Docker Compose (Recommended)

Use Docker Compose to start the server as a Docker container:

```bash
docker-compose up -d
```

### Systemd (Ubuntu)

Alternatively, use `service.sh` to install as a systemd service on Ubuntu:

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

1.  Discover available tools (derived from API endpoints)
2.  Execute tools with parameters
3.  Access resources like queue status and documentation

To connect to the MCP server, use a WebSocket connection to `ws://localhost:43080/mcp`.

## Testing and Verification

The server includes comprehensive test scripts for verifying functionality:

### API Testing

Test the REST API endpoints:

```bash
# Run API tests
python test_api.py
```

This will verify:
- Endpoint availability
- Request/response handling
- Data validation
- Error handling
- Queue functionality

### MCP Testing

Test the Model Context Protocol functionality:

```bash
# Run MCP tests
python test_mcp.py
```

This validates:
- WebSocket connections
- Tool discovery
- Tool execution
- Resource access
- Authentication
- Error scenarios

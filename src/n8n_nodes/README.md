# Createve.AI Nexus n8n Nodes

This package provides [n8n](https://n8n.io/) nodes for integrating with the [Createve.AI Nexus](https://github.com/spgoodman/createveai-nexus-server) server.

## Overview

The Createve.AI Nexus n8n Nodes package dynamically integrates with your Createve.AI Nexus server by leveraging its OpenAPI schema. This means that the node automatically discovers available API endpoints and adapts to changes without requiring package updates.

## Features

- 🔄 **Dynamic API Discovery**: Automatically discovers available endpoints from the OpenAPI schema
- 📁 **Binary Data Support**: Handles images and files with automatic encoding/decoding
- ⏱️ **Queue Support**: Works with both immediate and long-running queue-based operations
- 🔐 **Secure Authentication**: API key-based authentication for secure communication
- 🔌 **Flexible Configuration**: Configure connection details per workflow

## Installation

```bash
npm install @createveai/n8n-nodes-nexus-openapi
```

## Credentials

This package adds a new credential type:

- **Createve.AI API**: Stores connection details to your Nexus server

## Nodes

This package adds the following node:

- **Createve.AI**: A dynamic node that exposes all API endpoints available on your Nexus server

## Usage

### Basic Usage

1. Add the **Createve.AI** node to your workflow
2. Create and select the appropriate credentials
3. Select an API endpoint from the dropdown
4. Configure the required parameters
5. Connect to other nodes in your workflow

### Queue-Based Operations

For long-running operations, the node provides three operation modes:

1. **Submit & Wait for Result**: Submit job and wait for completion
2. **Submit Only**: Submit job and return queue ID immediately
3. **Check Status**: Check status of a previously submitted job

### Binary Data

The node seamlessly handles binary data:

- **Input**: Binary data from previous nodes is automatically processed
- **Output**: Binary data in responses is converted to n8n binary format

## Documentation

For comprehensive documentation, please refer to:

- [Detailed Documentation](https://github.com/spgoodman/createveai-nexus-server/blob/main/docs/n8n-nodes.md)
- [Createve.AI Nexus Server](https://github.com/spgoodman/createveai-nexus-server)

## License

Apache License 2.0

# Createve.AI Nexus Server

The Createve.AI Nexus Server acts as a versatile bridge, connecting Microsoft Copilot Studio to a wide range of capabilities via the Model Context Protocol (MCP). It empowers AI agents with:

*   **Access to Emerging AI Technologies:** Leverage the power of Python libraries and modules, including ComfyUI custom nodes, to enable cutting-edge AI scenarios.
*   **Secure Line of Business Data Access:** Establish secure Private Link connections to your internal applications, providing structured and controlled data access through familiar Python tools, APIs, databases, and real-time data warehouses.

## Key Features

*   **Universal Copilot Studio Bridge:** Seamless integration with Copilot Studio agents via MCP.
*   **Emerging AI Connectivity:** Access the latest AI advancements through Python libraries and modules.
*   **Creative AI Capabilities:** Enable Copilot Studio agents to generate 3D models, create videos, and design marketing images.
*   **Secure LOB Data Integration:** Secure Private Link connections to line of business applications.
*   **Structured Data Access:** Controlled access to data using Python libraries, APIs, and database connections.
*   **Real-time Data Connectivity:** Access real-time data from data warehouses, Apache Spark, Databricks, Oracle, SQL Server, and Azure SQL Managed Instances.
*   **Automated Action Implementation:** Interact with internal websites and automate actions.
*   **Sensor Data Integration:** Connect to sensor data for real-time insights.
*   **Optional Azure Key Vault Integration:** Securely manage API keys and secrets with Azure Key Vault (disable for local testing).
*   **Dual Protocol Support:** REST API and MCP for flexible integration.
*   **Dynamic API Loading:** Load API modules from a configurable directory.
*   **API Key Authentication:** Secure all endpoints with API key authentication.
*   **Queue System:** Robust queue system for long-running processes.
*   **Auto-Reload:** Automatically reload when API files change.
*   **OpenAPI Documentation:** Interactive API documentation with Swagger UI.
*   **File Type Handling:** Base64 encoding/decoding for image and file types.
*   **Logging & Error Handling:** Comprehensive logging and structured error responses.
*   **State Persistence:** Queue state persistence for recovery after restart.
*   **Containerization:** Compatible with Docker and systemd.

## Use Cases

*   **3D Model Creation:** Imagine a Copilot Studio agent that can design and generate 3D models based on user specifications. By leveraging Python libraries like `trimesh` or `blender`, the Createve.AI Nexus Server can provide the agent with the necessary tools to create, modify, and export 3D models in various formats.
*   **Video Generation:** Copilot Studio agents can create engaging videos for marketing or training purposes. By integrating with libraries such as `moviepy`, the agent can automate video editing tasks, add effects, and generate high-quality video content.
*   **Marketing Image Design:** Empower your agents to design compelling marketing images. Using libraries like `Pillow` and `scikit-image`, the agent can automate image manipulation tasks, add text overlays, and optimize images for different platforms.
*   **Real-time Inventory Management:** Connect your Copilot Studio agent to your real-time data warehouse to provide up-to-the-minute inventory information. Using Python libraries to connect to Oracle, SQL Server or cloud based solutions such as Databricks, your agent can keep on top of stock levels and generate low stock alerts.
*   **Automated Website Interactions:** Use the Createve.AI Nexus Server to enable Copilot Studio agents to interact with internal websites. Agents can fill in forms, click buttons, and extract data to automate website based tasks such as employee onboarding.

## Documentation

Comprehensive documentation is available in the `docs` directory:

*   [Setup Guide](docs/setup.md) - Instructions for installing and configuring the Createve.AI Nexus Server.
*   [Architecture Overview](docs/architecture.md) - Details of the server architecture.
*   [Custom API Guide](docs/custom-api-guide.md) - How to create custom API modules.
*   [API Usage Guide](docs/api-usage.md) - How to use the API endpoints.
*   [MCP Integration Guide](docs/mcp-integration.md) - How to use the MCP functionality.
*   [Azure Reference Architecture](docs/azure-reference-architecture.md) - Reference architecture for deployment in Azure.
*   [n8n Nodes](docs/n8n-nodes.md) - n8n nodes for integrating with Nexus

## Configuration

The config is stored in `config.yaml`. This contains settings for both the API server and MCP functionality.

```yaml
apiserver:
  host: 0.0.0.0 # Host to listen on
  port: 43080 # Port to listen on
  debug: true # Debug to console
  log: true # Log to file
  log_file: logs/apiserver.log # Log file relevative to main.py
  apis_dir: custom_apis # Directory containing Python source for API interfaces to load and serve using FastAPI, relevative to main.py
security:
  api_keys: # List of API keys that are valid for accessing the API server. Each has access to its own queue of jobs
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

The APIs are loaded from the defined `custom_apis` folder, each in a subfolder structure that contains an `__init__.py` file which will load the relevant classes from the same/sub-folders.

The API definitions are inspired by ComfyUI's custom nodes and use the same structures for defining inputs and outputs. These APIs are exposed both as REST endpoints and MCP tools.

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

## Using the MCP Functionality

The MCP functionality allows AI assistants to interact with the server using the Model Context Protocol. This enables assistants to:

1.  Discover available tools (derived from API endpoints)
2.  Execute tools with parameters
3.  Access resources like queue status and documentation

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

This project is licensed under the [Apache Licence v2](LICENCE)

# Quick Start: Creating Custom Integrations

This guide provides a quick introduction to creating custom integrations with Createve.AI Nexus. For complete details, see the [Custom API Guide](custom-api-guide.md).

## Overview

Createve.AI Nexus makes it easy to expose your custom functionality as both REST API endpoints and MCP tools. Each integration is automatically available to:

- Microsoft Copilot Studio agents
- Anthropic's Claude (via desktop app)
- Any OpenAPI-compatible client
- Any MCP-enabled system

## Basic Integration Example

Here's a simple example that exposes enterprise data analysis capabilities:

```python
class DataAnalyzer:
    """Enterprise data analysis endpoint."""

    CATEGORY = "analytics"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "query": ("STRING", {"multiline": True}),
                "dataset": ("STRING", {"default": "production"})
            },
            "optional": {
                "time_range": ("STRING", {"default": "1d"})
            }
        }

    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("analysis_results",)
    FUNCTION = "analyze_data"

    def analyze_data(self, query, dataset, time_range="1d"):
        # Implementation here
        return (result,)
```

## Key Concepts

1. **Class Structure**
   - Clear docstring describing functionality
   - Category for grouping in documentation
   - Input types definition with required/optional parameters
   - Return type specifications
   - Main processing function

2. **Automatic Exposure**
   - REST API endpoint at `/api/analytics/dataAnalyzer`
   - MCP tool named `analytics_dataAnalyzer`
   - OpenAPI documentation automatically generated

3. **Type System**
   - Rich type system for inputs/outputs
   - Automatic validation and conversion
   - Support for files, images, and complex data

## Quick Start Steps

1. Create a Python file in the `custom_apis` directory
2. Define your class following the example structure
3. Implement your processing logic
4. Restart the server to load your new integration

## Using Your Integration

### REST API
```bash
curl -X POST "http://localhost:43080/api/analytics/dataAnalyzer" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "sales_by_region", "dataset": "production"}'
```

### MCP (via Copilot Studio or Claude)
Your integration automatically appears as an available tool in MCP-enabled clients.

### OpenAPI
Browse to `http://localhost:43080/docs` to see your endpoint in the Swagger UI.

## Next Steps

- Read the [Custom API Guide](custom-api-guide.md) for detailed documentation
- Explore example integrations in the `custom_apis` directory
- Check the [MCP Integration Guide](mcp-integration.md) for advanced MCP features

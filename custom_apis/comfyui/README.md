# ComfyUI API Integration

This module provides integration with ComfyUI's API for the Createve.AI API Server, allowing execution of ComfyUI workflows and retrieval of workflow information.

## Features

- Execute ComfyUI workflows with customizable parameters
- Get information about available workflows
- Support for both text-to-image and image-to-image workflows
- Configuration through YAML file
- Async execution with progress monitoring
- MCP integration for AI assistant access

## Installation

1. Ensure ComfyUI is running and accessible (default: http://localhost:8188)
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The module uses a `config.yaml` file for configuration:

```yaml
url: http://localhost:8188  # ComfyUI server URL
workflows_directory: workflows  # Directory for workflow files
default_timeout: 300  # Default execution timeout

workflows:
  txt2img:  # Example workflow configuration
    file: txt2img.json
    timeout: 600
    default_params:
      prompt: "A beautiful landscape"
      negative_prompt: "blur, deformed"
      width: 512
      height: 512
      steps: 20
      cfg_scale: 7.0
      seed: -1
```

## Usage

### As REST API

Execute a workflow:
```bash
curl -X POST "http://localhost:43080/api/comfyui/comfyUIWorkflowExecutor" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "txt2img",
    "prompt": "A beautiful sunset over mountains",
    "negative_prompt": "blur, noise",
    "width": 768,
    "height": 512
  }'
```

Get workflow information:
```bash
curl -X POST "http://localhost:43080/api/comfyui/comfyUIWorkflowInfo" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "txt2img"
  }'
```

### As MCP Resource

AI assistants can interact with the ComfyUI integration through MCP:

```python
# Example MCP tool usage
response = await mcp.call_tool(
    "comfyui_workflowExecutor",
    {
        "workflow_name": "txt2img",
        "prompt": "A beautiful sunset over mountains",
        "width": 768,
        "height": 512
    }
)
```

## Workflow Files

Workflow files (`.json`) should be placed in the configured workflows directory. Each workflow file should be a valid ComfyUI workflow JSON export.

Example workflow structure:
```json
{
  "nodes": {
    "1": {
      "class_type": "CLIPTextEncode",
      "inputs": {
        "prompt": "A beautiful landscape",
        "negative_prompt": "blur, deformed"
      }
    },
    "2": {
      "class_type": "KSampler",
      "inputs": {
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg_scale": 7.0,
        "seed": -1
      }
    }
  }
}
```

## Error Handling

The module includes comprehensive error handling:

- Configuration errors (missing files, invalid YAML)
- Workflow execution errors (timeout, API errors)
- Parameter validation
- ComfyUI server connection issues

Error responses include detailed messages to help diagnose issues.

## Limitations

- Currently supports basic parameter mapping for common node types
- Limited to single-image output workflows
- Does not support all ComfyUI node types
- Queue mode required for execution (may have latency)

## Development

To add new features or modify existing ones:

1. Update workflow parameter mapping in `api.py`
2. Add new configuration options in `config.py`
3. Update input/output types in API classes
4. Test with different workflow configurations

## License

MIT License - See LICENSE file for details

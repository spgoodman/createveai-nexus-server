"""ComfyUI API integration for Createve.AI API Server."""
from .api import ComfyUIWorkflowExecutor, ComfyUIWorkflowInfo
from .config import load_config

# Map class names to class objects
NODE_CLASS_MAPPINGS = {
    "ComfyUI Workflow Executor": ComfyUIWorkflowExecutor,
    "ComfyUI Workflow Info": ComfyUIWorkflowInfo
}

# Map class names to display names 
NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyUI Workflow Executor": "Execute ComfyUI Workflow",
    "ComfyUI Workflow Info": "Get ComfyUI Workflow Info"
}

# Define queue mode (use queue mode for potentially long-running workflow executions)
API_SERVER_QUEUE_MODE = {
    ComfyUIWorkflowExecutor: True,  # Queue mode for execution
    ComfyUIWorkflowInfo: False      # Direct mode for info queries
}

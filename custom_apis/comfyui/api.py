"""ComfyUI API implementation for Createve.AI API Server."""
import os
import json
import base64
import httpx
import asyncio
import mimetypes
import logging
import uuid
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass
import aiohttp
import websockets
from aiohttp import FormData
from .config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NodeInfo:
    """Information about a ComfyUI workflow node."""
    id: str
    type: str
    title: str

@dataclass
class WorkflowStatus:
    """Status information for a workflow execution."""
    prompt_id: str
    status: str
    progress: float
    output_images: List[str]
    error: Optional[str] = None

class ComfyUIClient:
    """Client for interacting with ComfyUI server."""
    
    def __init__(self, url: str, timeout: int = 30):
        self.url = url.rstrip('/')
        self.ws_url = f"ws://{self.url.split('://',1)[1]}/ws"
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
    
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None
        if self.ws:
            await self.ws.close()
            self.ws = None
    
    async def upload_image(self, image_data: bytes, filename: str, overwrite: bool = True) -> Dict[str, Any]:
        """Upload an image to ComfyUI."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        form = FormData()
        form.add_field('image',
                      image_data,
                      filename=filename,
                      content_type=mimetypes.guess_type(filename)[0])
        form.add_field('overwrite', 'true' if overwrite else 'false')
        
        async with self.session.post(f"{self.url}/upload/image", data=form) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to upload image: {error_text}")
            return await response.json()
    
    async def execute_workflow(self, workflow: Dict, 
                             progress_callback: Optional[Callable[[float], None]] = None) -> WorkflowStatus:
        """Execute a workflow and monitor its progress."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Queue the workflow
        async with self.session.post(f"{self.url}/prompt", json={"prompt": workflow}) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Failed to queue workflow: {response.text}")
            queue_data = await response.json()
        
        prompt_id = queue_data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError("No prompt ID received from ComfyUI")
        
        # Connect to WebSocket for progress updates
        if not self.ws:
            self.ws = await websockets.connect(self.ws_url)
        
        status = WorkflowStatus(
            prompt_id=prompt_id,
            status="pending",
            progress=0.0,
            output_images=[]
        )
        
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    
                    if data.get("type") == "progress":
                        status.progress = data["data"]["value"]
                        if progress_callback:
                            progress_callback(status.progress)
                    
                    elif data.get("type") == "executing":
                        if data["data"]["node"] is None:
                            status.status = "completed"
                            # Get the final image outputs
                            async with self.session.get(f"{self.url}/history/{prompt_id}") as history_resp:
                                if history_resp.status == 200:
                                    history_data = await history_resp.json()
                                    if "output" in history_data:
                                        status.output_images = history_data["output"]
                            break
                    
                    elif data.get("type") == "error":
                        status.status = "error"
                        status.error = data["data"].get("message", "Unknown error")
                        break
                
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            status.status = "error"
            status.error = str(e)
        
        return status

class ComfyUIWorkflowInfo:
    """Get information about available ComfyUI workflows."""
    
    CATEGORY = "comfyui"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for workflow info retrieval."""
        config = load_config()
        available_workflows = list(config.workflows.keys())
        
        return {
            "required": {
                "workflow_name": (available_workflows, {"default": available_workflows[0] if available_workflows else None}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("workflow_info",)
    FUNCTION = "get_workflow_info"
    
    def get_workflow_info(self, workflow_name: str) -> Tuple[Dict[str, Any]]:
        """Get information about a specific workflow."""
        config = load_config()
        workflow_config = config.get_workflow_config(workflow_name)
        
        if not workflow_config:
            raise ValueError(f"Workflow '{workflow_name}' not found")
            
        workflow_path = config.get_workflow_path(workflow_name)
        if not workflow_path or not os.path.exists(workflow_path):
            raise ValueError(f"Workflow file not found for '{workflow_name}'")
            
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load workflow file: {str(e)}")
            
        return ({
            "name": workflow_name,
            "timeout": config.get_workflow_timeout(workflow_name),
            "default_params": config.get_workflow_default_params(workflow_name),
            "workflow_data": workflow_data
        },)

class ComfyUIWorkflowExecutor:
    """Execute ComfyUI workflows."""
    
    CATEGORY = "comfyui"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for workflow execution."""
        config = load_config()
        available_workflows = list(config.workflows.keys())
        
        return {
            "required": {
                "workflow_name": (available_workflows, {"default": available_workflows[0] if available_workflows else None}),
            },
            "optional": {
                # Optional parameters that can override defaults
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "width": ("INTEGER", {"default": 512, "min": 64, "max": 2048}),
                "height": ("INTEGER", {"default": 512, "min": 64, "max": 2048}),
                "steps": ("INTEGER", {"default": 20, "min": 1, "max": 150}),
                "cfg_scale": ("FLOAT", {"default": 7.0, "min": 1.0, "max": 30.0}),
                "seed": ("INTEGER", {"default": -1}),
                "input_image": ("IMAGE", {"default": None}),  # For img2img
                "denoising_strength": ("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.0}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "DICT")
    RETURN_NAMES = ("generated_image", "execution_info")
    FUNCTION = "execute_workflow"
    
    async def _query_progress(self, client: httpx.AsyncClient, config: Any, history_id: str) -> Dict[str, Any]:
        """Query workflow execution progress."""
        try:
            response = await client.get(f"{config.url}/history/{history_id}")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def _wait_for_completion(self, client: httpx.AsyncClient, config: Any, history_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for workflow execution to complete."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")
                
            progress = await self._query_progress(client, config, history_id)
            
            if "error" in progress:
                raise RuntimeError(f"Error querying progress: {progress['error']}")
                
            if progress.get("status", {}).get("completed", False):
                return progress
                
            await asyncio.sleep(1.0)
    
    def execute_workflow(self, workflow_name: str, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """Execute a ComfyUI workflow."""
        config = load_config()
        workflow_path = config.get_workflow_path(workflow_name)
        
        if not workflow_path or not os.path.exists(workflow_path):
            raise ValueError(f"Workflow file not found for '{workflow_name}'")
            
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load workflow file: {str(e)}")
            
        # Merge default parameters with provided parameters
        params = config.get_workflow_default_params(workflow_name).copy()
        params.update({k: v for k, v in kwargs.items() if v is not None})
        
        # Update workflow data with parameters
        # Note: This is a simplified example. In practice, you'd need to map
        # parameters to the correct nodes in the workflow graph
        for node_id, node in workflow_data.get("nodes", {}).items():
            if node.get("class_type") in ["CLIPTextEncode", "KSampler"]:
                if "inputs" in node:
                    for param_name, param_value in params.items():
                        if param_name in node["inputs"]:
                            node["inputs"][param_name] = param_value
        
        # Execute workflow using async httpx
        async def run_workflow():
            timeout = config.get_workflow_timeout(workflow_name)
            
            async with httpx.AsyncClient() as client:
                # Queue the workflow
                response = await client.post(
                    f"{config.url}/prompt",
                    json={"prompt": workflow_data}
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"Failed to queue workflow: {response.text}")
                
                queue_data = response.json()
                history_id = queue_data.get("prompt_id")
                
                if not history_id:
                    raise RuntimeError("No prompt ID received from ComfyUI")
                
                # Wait for completion
                result = await self._wait_for_completion(client, config, history_id, timeout)
                
                # Get the output image
                if "output" in result:
                    image_data = result["output"]
                    # Note: This is a simplified example. You'd need to properly
                    # extract and decode the image data based on your workflow
                    return image_data, result
                else:
                    raise RuntimeError("No output image in workflow result")
        
        # Run the async workflow in the event loop
        loop = asyncio.get_event_loop()
        image_data, execution_info = loop.run_until_complete(run_workflow())
        
        return image_data, execution_info

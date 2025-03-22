# src/api_server/mcp/resources.py
import logging
import json
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP, Context
from ..utils import ConfigManager
from ..models import APIError, APIErrorCode

logger = logging.getLogger(__name__)

class ResourceRegistry:
    """Registry for MCP resources."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        """Initialize resource registry."""
        self.config = config
        self.logger = logger
        self.queue_manager = None
        self.mcp: Optional[FastMCP] = None

    async def setup(self, queue_manager: Any, mcp: FastMCP):
        """Set up the resource registry with queue manager and MCP instance."""
        self.queue_manager = queue_manager
        self.mcp = mcp
        await self.register_resources()

    async def register_resources(self):
        """Register all resources with the MCP instance."""
        if not self.mcp:
            raise RuntimeError("MCP instance not set")
        register_resources(self.mcp)

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all registered resources."""
        if not self.mcp:
            return []
        return [
            {
                "uri": uri,
                "description": resource.description,
                "mime_type": resource.mime_type
            }
            for uri, resource in self.mcp.resources.items()
        ]

    async def list_resource_templates(self) -> List[Dict[str, Any]]:
        """List all registered resource templates."""
        if not self.mcp:
            return []
        return [
            {
                "uri_template": template.uri_template,
                "description": template.description,
                "mime_type": template.mime_type
            }
            for template in self.mcp.resource_templates
        ]

    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read a resource by URI."""
        if not self.mcp:
            return []
        try:
            content = await self.mcp.read_resource(uri)
            return content
        except Exception as e:
            self.logger.exception(f"Error reading resource {uri}: {e}")
            raise APIError(APIErrorCode.RESOURCE_ERROR, str(e))

def register_resources(mcp: FastMCP):
    """Register MCP resources with the given FastMCP instance."""
    
    async def example_resource_impl(name: str) -> Dict[str, Any]:
        """Example resource that takes a name parameter."""
        return {"message": f"This is the {name} resource"}

    async def another_resource_impl(type: str, id: str) -> Dict[str, Any]:
        """Example resource that takes type and id parameters."""
        return {"message": f"This is a {type} resource with id {id}"}

    @mcp.resource("resource://{name}")
    async def example_resource(name: str) -> Dict[str, Any]:
        """Example resource that takes a name parameter."""
        return await example_resource_impl(name)

    @mcp.resource("resource://{type}/{id}")
    async def another_resource(type: str, id: str) -> Dict[str, Any]:
        """Example resource that takes type and id parameters."""
        return await another_resource_impl(type, id)

    # Add more resources here

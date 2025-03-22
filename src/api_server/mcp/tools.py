# src/api_server/mcp/tools.py

import logging
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP, Context
from src.api_server.api.executor import APIExecutor
from src.api_server.utils import ConfigManager

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        """Initialize tool registry."""
        self.config = config
        self.logger = logger
        self.api_executor: Optional[APIExecutor] = None
        self.mcp: Optional[FastMCP] = None

    async def setup(self, api_executor: APIExecutor, mcp: FastMCP):
        """Set up the tool registry with API executor and MCP instance."""
        self.api_executor = api_executor
        self.mcp = mcp
        await self.register_tools()

    async def register_tools(self):
        """Register all tools with the MCP instance."""
        if not self.mcp:
            raise RuntimeError("MCP instance not set")
        register_tools(self.mcp, self.api_executor)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        if not self.mcp:
            return []
        return [
            {
                "name": name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for name, tool in self.mcp.tools.items()
        ]

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments."""
        if not self.mcp or name not in self.mcp.tools:
            return {
                "content": [{"type": "text", "text": f"Tool not found: {name}"}],
                "is_error": True
            }
        
        try:
            ctx = Context()  # You might want to add more context here
            result = await self.mcp.tools[name].execute(arguments, ctx)
            return result
        except Exception as e:
            self.logger.exception(f"Error executing tool {name}: {e}")
            return {
                "content": [{"type": "text", "text": str(e)}],
                "is_error": True
            }

def register_tools(mcp: FastMCP, api_executor: Optional[APIExecutor] = None):
    """Register MCP tools with the given FastMCP instance."""
    
    async def api_path_tool_impl(arg1: str, arg2: int) -> Dict[str, Any]:
        """Example tool that executes an API endpoint."""
        executor = api_executor or APIExecutor()
        try:
            result = await executor.execute_api("/api/path", {"arg1": arg1, "arg2": arg2})
            return {"content": [{"type": "json", "json": result}], "is_error": False}
        except Exception as e:
            logger.exception(f"Error executing API: {e}")
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def another_api_tool_impl(input_string: str) -> Dict[str, Any]:
        """Another example tool."""
        executor = api_executor or APIExecutor()
        try:
            result = await executor.execute_api("/another/api", {"input": input_string})
            return {"content": [{"type": "json", "json": result}], "is_error": False}
        except Exception as e:
            logger.exception(f"Error executing API: {e}")
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    @mcp.tool()
    async def api_path_tool(arg1: str, arg2: int) -> Dict[str, Any]:
        """Example tool that executes an API endpoint."""
        return await api_path_tool_impl(arg1, arg2)

    @mcp.tool()
    async def another_api_tool(input_string: str) -> Dict[str, Any]:
        """Another example tool."""
        return await another_api_tool_impl(input_string)

    # Add more tools here, mapping them to your API endpoints

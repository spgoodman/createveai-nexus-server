"""MCP Server implementation for Createve.AI Nexus Server."""

import logging
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ..utils import ConfigManager
from .tools import ToolRegistry
from .resources import ResourceRegistry

class MCPServer:
    """Model Context Protocol server implementation."""
    
    def __init__(
        self, 
        app: FastAPI, 
        config: ConfigManager, 
        logger: logging.Logger,
        security_manager=None
    ):
        """Initialize MCP server."""
        self.app = app
        self.config = config
        self.logger = logger
        self.security_manager = security_manager
        
        # Initialize registries
        self.tool_registry = ToolRegistry(config, logger)
        self.resource_registry = ResourceRegistry(config, logger)
        
        # Connected clients
        self.active_connections: List[WebSocket] = []
        
        # Only set up endpoints if MCP is enabled
        if config.mcp_enabled:
            self._setup_endpoints()
            
    def _setup_endpoints(self):
        """Set up WebSocket endpoint for MCP communication."""
        @self.app.websocket("/mcp")
        async def mcp_endpoint(websocket: WebSocket):
            await self._handle_connection(websocket)
    
    async def _handle_connection(self, websocket: WebSocket):
        """Handle new MCP client connection."""
        await websocket.accept()
        
        # Add to active connections
        self.active_connections.append(websocket)
        
        try:
            # Send server info
            await websocket.send_json({
                "type": "server_info", 
                "name": self.config.mcp_server_name,
                "version": self.config.mcp_server_version,
                "description": self.config.mcp_server_description
            })
            
            # Process messages
            while True:
                message = await websocket.receive_text()
                
                try:
                    # Parse message
                    data = json.loads(message)
                    
                    # Process message
                    if data.get("type") == "capabilities_request":
                        await self._handle_capabilities_request(websocket)
                    elif data.get("type") == "list_tools_request":
                        await self._handle_list_tools_request(websocket)
                    elif data.get("type") == "call_tool_request":
                        await self._handle_call_tool_request(websocket, data)
                    elif data.get("type") == "list_resources_request":
                        await self._handle_list_resources_request(websocket) 
                    elif data.get("type") == "list_resource_templates_request":
                        await self._handle_list_resource_templates_request(websocket)
                    elif data.get("type") == "read_resource_request":
                        await self._handle_read_resource_request(websocket, data)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "code": "unknown_message_type",
                            "message": f"Unknown message type: {data.get('type')}"
                        })
                        
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "code": "invalid_json",
                        "message": "Invalid JSON"
                    })
                except Exception as e:
                    self.logger.error(f"Error processing MCP message: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "code": "internal_error",
                        "message": f"Internal error: {str(e)}"
                    })
                
        except WebSocketDisconnect:
            # Remove from active connections
            self.active_connections.remove(websocket)
            self.logger.info("MCP client disconnected")
        except Exception as e:
            # Handle other exceptions
            self.logger.error(f"WebSocket error: {str(e)}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def _handle_capabilities_request(self, websocket: WebSocket):
        """Handle capabilities request."""
        await websocket.send_json({
            "type": "capabilities_response",
            "capabilities": {
                "tools": self.config.mcp_auto_map_apis,
                "resources": self.config.mcp_expose_queue or self.config.mcp_expose_docs
            }
        })
    
    async def _handle_list_tools_request(self, websocket: WebSocket):
        """Handle list tools request."""
        tools = await self.tool_registry.list_tools()
        
        await websocket.send_json({
            "type": "list_tools_response",
            "tools": tools
        })
    
    async def _handle_call_tool_request(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle call tool request."""
        request_id = data.get("request_id")
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        
        if not tool_name:
            await websocket.send_json({
                "type": "error",
                "code": "invalid_request",
                "message": "Tool name is required",
                "request_id": request_id
            })
            return
            
        # Check authentication if required
        if self.config.mcp_require_authentication:
            # TODO: Add authentication check
            pass
            
        # Execute tool
        result = await self.tool_registry.execute_tool(tool_name, arguments)
        
        # Send response
        await websocket.send_json({
            "type": "call_tool_response",
            "request_id": request_id,
            "content": result.get("content", []),
            "is_error": result.get("is_error", False)
        })
    
    async def _handle_list_resources_request(self, websocket: WebSocket):
        """Handle list resources request."""
        resources = await self.resource_registry.list_resources()
        
        await websocket.send_json({
            "type": "list_resources_response",
            "resources": resources
        })
    
    async def _handle_list_resource_templates_request(self, websocket: WebSocket):
        """Handle list resource templates request."""
        templates = await self.resource_registry.list_resource_templates()
        
        await websocket.send_json({
            "type": "list_resource_templates_response",
            "resource_templates": templates
        })
        
    async def _handle_read_resource_request(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle read resource request."""
        request_id = data.get("request_id")
        uri = data.get("uri")
        
        if not uri:
            await websocket.send_json({
                "type": "error",
                "code": "invalid_request",
                "message": "Resource URI is required",
                "request_id": request_id
            })
            return
            
        # Check authentication if required
        if self.config.mcp_require_authentication:
            # TODO: Add authentication check
            pass
            
        # Read resource
        contents = await self.resource_registry.read_resource(uri)
        
        # Send response
        await websocket.send_json({
            "type": "read_resource_response",
            "request_id": request_id,
            "contents": contents
        })
        
    async def setup_registries(self, api_executor, queue_manager, api_registry):
        """Set up tool and resource registries with API and queue data."""
        await self.tool_registry.setup(api_executor, api_registry)
        await self.resource_registry.setup(queue_manager, api_registry)

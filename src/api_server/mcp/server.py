"""MCP Server implementation for Createve.AI Nexus Server."""

import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from starlette.responses import StreamingResponse
from ..utils import ConfigManager
from mcp.server.fastmcp import FastMCP, Context
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
        #self.active_connections: List[WebSocket] = []
        
        # Only set up endpoints if MCP is enabled
        #if config.mcp_enabled:
        #    self._setup_endpoints()

    #def _setup_endpoints(self):
    #    """Set up WebSocket and SSE endpoints for MCP communication."""
    #    @self.app.websocket("/mcp")
    #    async def mcp_websocket_endpoint(websocket: WebSocket):
    #        await self._handle_websocket_connection(websocket)

    #    @self.app.get("/mcp_sse")
    #    async def mcp_sse_endpoint(request: Request):
    #        return StreamingResponse(
    #            self._handle_sse_connection(request),
    #            media_type="text/event-stream"
    #        )

    #async def _handle_websocket_connection(self, websocket: WebSocket):
    #    """Handle new MCP client WebSocket connection."""
    #    await websocket.accept()

        # Add to active connections
    #    self.websocket_connections.append(websocket)

    #    try:
            # Send server info
    #        await websocket.send_json({
    #            "type": "server_info",
    #            "name": self.config.mcp_server_name,
    #            "version": self.config.mcp_server_version,
    #            "description": self.config.mcp_server_description
    #        })

            # Process messages
    #        while True:
    #            message = await websocket.receive_text()
    #            await self._process_message(websocket, message)

    #    except WebSocketDisconnect:
            # Remove from active connections
    #        self.websocket_connections.remove(websocket)
    #        self.logger.info("MCP client disconnected (WebSocket)")
    #    except Exception as e:
            # Handle other exceptions
    #        self.logger.error(f"WebSocket error: {str(e)}")
    #        if websocket in self.websocket_connections:
    #            self.websocket_connections.remove(websocket)

    #async def _handle_sse_connection(self, request: Request):
    #    """Handle new MCP client SSE connection."""
    #    queue = asyncio.Queue()

    #    async def send_server_info():
    #        """Send initial server info message."""
    #        server_info = {
    #            "type": "server_info",
    #            "name": self.config.mcp_server_name,
    #            "version": self.config.mcp_server_version,
    #            "description": self.config.mcp_server_description
    #        }
    #        await queue.put(f"data: {json.dumps(server_info)}\n\n")

    #    async def process_messages():
    #        """Process incoming messages."""
    #        try:
    #            await send_server_info()  # Send server info immediately

    #            while True:
                    # SSE doesn't natively receive messages, so this is for demonstration.
                    # In real-world scenarios, SSE is often paired with a separate channel
                    # (e.g., HTTP POST) for sending messages from the client to the server.
                    # Here, I will simulate sending capabilities request after server info is sent

    #                capabilities_request = {"type": "capabilities_request"}
    #                await self._process_message(queue, json.dumps(capabilities_request))
    #                await asyncio.sleep(5) # wait for 5 seconds before sending it again

    #        except asyncio.CancelledError:
    #            self.logger.info("SSE client disconnected")
    #        except Exception as e:
    #            self.logger.error(f"SSE error: {str(e)}")
    #        finally:
    #            await queue.put(None)  # Signal completion

    #    async def generate():
    #        """Generator function for SSE stream."""
    #        task = asyncio.create_task(process_messages())
    #        try:
    #            while True:
    #                data = await queue.get()
    #                if data is None:
    #                    break
    #                yield data
    #                queue.task_done()
    #        finally:
    #            task.cancel()
    #            if not task.done():
    #                try:
    #                    await task
    #                except asyncio.CancelledError:
    #                    pass

    #    return generate()


    #async def _process_message(self, transport, message: str):
    #    """Process incoming MCP message."""
    #    try:
            # Parse message
    #        data = json.loads(message)

            # Process message
    #        if data.get("type") == "capabilities_request":
    #            await self._handle_capabilities_request(transport)
    #        elif data.get("type") == "list_tools_request":
    #            await self._handle_list_tools_request(transport)
    #        elif data.get("type") == "call_tool_request":
    #            await self._handle_call_tool_request(transport, data)
    #        elif data.get("type") == "list_resources_request":
    #            await self._handle_list_resources_request(transport)
    #        elif data.get("type") == "list_resource_templates_request":
    #            await self._handle_list_resource_templates_request(transport)
    #        elif data.get("type") == "read_resource_request":
    #            await self._handle_read_resource_request(transport, data)
    #        else:
    #            error_message = {
    #                "type": "error",
    #                "code": "unknown_message_type",
    #                "message": f"Unknown message type: {data.get('type')}"
    #            }
    #            if isinstance(transport, WebSocket):
    #                await transport.send_json(error_message)
    #            else:
    #                 await transport.put(f"data: {json.dumps(error_message)}\n\n")


    #    except json.JSONDecodeError:
    #        error_message = {
    #            "type": "error",
    #            "code": "invalid_json",
    #            "message": "Invalid JSON"
    #        }
    #        if isinstance(transport, WebSocket):
    #            await transport.send_json(error_message)
    #        else:
    #             await transport.put(f"data: {json.dumps(error_message)}\n\n")
    #    except Exception as e:
    #        self.logger.error(f"Error processing MCP message: {str(e)}")
    #        error_message = {
    #            "type": "error",
    #            "code": "internal_error",
    #            "message": f"Internal error: {str(e)}"
    #        }
    #        if isinstance(transport, WebSocket):
    #            await transport.send_json(error_message)
    #        else:
    #             await transport.put(f"data: {json.dumps(error_message)}\n\n")

    #async def _handle_capabilities_request(self, transport):
    #    """Handle capabilities request."""
    #    response = {
    #        "type": "capabilities_response",
    #        "capabilities": {
    #            "tools": self.config.mcp_auto_map_apis,
    #            "resources": self.config.mcp_expose_queue or self.config.mcp_expose_docs
    #        }
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(error_message)}\n\n")


    #async def _handle_list_tools_request(self, transport):
    #    """Handle list tools request."""
    #    tools = await self.tool_registry.list_tools()

    #    response = {
    #        "type": "list_tools_response",
    #        "tools": tools
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(response)}\n\n")

    #async def _handle_call_tool_request(self, transport, data: Dict[str, Any]):
    #    """Handle call tool request."""
    #    request_id = data.get("request_id")
    #    tool_name = data.get("name")
    #    arguments = data.get("arguments", {})

    #    if not tool_name:
    #        error_message = {
    #            "type": "error",
    #            "code": "invalid_request",
    #            "message": "Tool name is required",
    #            "request_id": request_id
    #        }
    #        if isinstance(transport, WebSocket):
    #            await transport.send_json(error_message)
    #        else:
    #             await transport.put(f"data: {json.dumps(error_message)}\n\n")
    #        return

        # Check authentication if required
    #    if self.config.mcp_require_authentication:
            # TODO: Add authentication check
    #        pass

        # Execute tool
    #    result = await self.tool_registry.execute_tool(tool_name, arguments)

        # Send response
    #    response = {
    #        "type": "call_tool_response",
    #        "request_id": request_id,
    #        "content": result.get("content", []),
    #        "is_error": result.get("is_error", False)
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(response)}\n\n")



    #async def _handle_list_resources_request(self, transport):
    #    """Handle list resources request."""
    #    resources = await self.resource_registry.list_resources()

    #    response = {
    #        "type": "list_resources_response",
    #        "resources": resources
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(response)}\n\n")


    #async def _handle_list_resource_templates_request(self, transport):
    #    """Handle list resource templates request."""
    #    templates = await self.resource_registry.list_resource_templates()

    #    response = {
    #        "type": "list_resource_templates_response",
    #        "resource_templates": templates
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(response)}\n\n")


    #async def _handle_read_resource_request(self, transport, data: Dict[str, Any]):
    #    """Handle read resource request."""
    #    request_id = data.get("request_id")
    #    uri = data.get("uri")

    #    if not uri:
    #        error_message = {
    #            "type": "error",
    #            "code": "invalid_request",
    #            "message": "Resource URI is required",
    #            "request_id": request_id
    #        }
    #        if isinstance(transport, WebSocket):
    #            await transport.send_json(error_message)
    #        else:
    #             await transport.put(f"data: {json.dumps(error_message)}\n\n")
    #        return

        # Check authentication if required
    #    if self.config.mcp_require_authentication:
            # TODO: Add authentication check
    #        pass

        # Read resource
    #    contents = await self.resource_registry.read_resource(uri)

        # Send response
    #    response = {
    #        "type": "read_resource_response",
    #        "request_id": request_id,
        #        "contents": contents
    #    }
    #    if isinstance(transport, WebSocket):
    #        await transport.send_json(response)
    #    else:
    #         await transport.put(f"data: {json.dumps(response)}\n\n")


    async def setup_registries(self, api_executor, queue_manager, api_registry, mcp: Optional[FastMCP] = None):
        """Set up tool and resource registries with API and queue data."""
        if mcp:
            await self.tool_registry.setup(api_executor, mcp)
            await self.resource_registry.setup(queue_manager, mcp)

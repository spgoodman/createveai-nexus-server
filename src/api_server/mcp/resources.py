"""Resource registry for MCP server."""

import logging
import json
from typing import Dict, Any, List, Optional

from ..utils import ConfigManager
from ..models import APIError, APIErrorCode

class ResourceRegistry:
    """Registry for MCP resources."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        """Initialize resource registry."""
        self.config = config
        self.logger = logger
        self.queue_manager = None
        self.api_registry = None
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.resource_templates: Dict[str, Dict[str, Any]] = {}
        
    async def setup(self, queue_manager, api_registry):
        """Set up resource registry with queue manager and API registry."""
        self.queue_manager = queue_manager
        self.api_registry = api_registry
        
        # Set up queue resources if enabled
        if self.config.mcp_expose_queue:
            await self._setup_queue_resources()
            
        # Set up docs resources if enabled
        if self.config.mcp_expose_docs:
            await self._setup_docs_resources()
            
        # Set up logs resources if enabled
        if self.config.mcp_expose_logs:
            await self._setup_logs_resources()
            
    async def _setup_queue_resources(self):
        """Set up queue-related resources."""
        # Add queue template
        self.resource_templates["queue://{queue_id}"] = {
            "uri_template": "queue://{queue_id}",
            "name": "Queue Status",
            "description": "Status and result for a queued request",
            "mime_type": "application/json"
        }
        
        self.logger.info("Set up queue resource template")
            
    async def _setup_docs_resources(self):
        """Set up documentation-related resources."""
        # Add static documentation resources
        self.resources["docs://openapi.json"] = {
            "uri": "docs://openapi.json",
            "name": "OpenAPI Schema",
            "description": "Full OpenAPI specification for the API server",
            "mime_type": "application/json"
        }
        
        self.resources["docs://readme"] = {
            "uri": "docs://readme",
            "name": "Server Documentation",
            "description": "Documentation for the Createve.AI Nexus Server",
            "mime_type": "text/markdown"
        }
        
        # Add template for API endpoint docs
        self.resource_templates["docs://api/{endpoint}"] = {
            "uri_template": "docs://api/{endpoint}",
            "name": "API Endpoint Documentation",
            "description": "Documentation for a specific API endpoint",
            "mime_type": "application/json"
        }
        
        self.logger.info("Set up documentation resources")
            
    async def _setup_logs_resources(self):
        """Set up logging-related resources."""
        # Add log resource
        self.resources["logs://server"] = {
            "uri": "logs://server",
            "name": "Server Logs",
            "description": "Recent server logs",
            "mime_type": "text/plain"
        }
        
        self.logger.info("Set up log resources")
            
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return list(self.resources.values())
        
    async def list_resource_templates(self) -> List[Dict[str, Any]]:
        """List available resource templates."""
        return list(self.resource_templates.values())
        
    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read a resource."""
        try:
            # Check if URI is for queue status
            if uri.startswith("queue://"):
                return await self._read_queue_resource(uri)
                
            # Check if URI is for documentation
            elif uri.startswith("docs://"):
                return await self._read_docs_resource(uri)
                
            # Check if URI is for logs
            elif uri.startswith("logs://"):
                return await self._read_logs_resource(uri)
                
            # Unknown URI scheme
            else:
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Unknown resource URI scheme: {uri}"
                    }
                ]
                
        except APIError as e:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": e.message
                }
            ]
        except Exception as e:
            self.logger.error(f"Error reading resource {uri}: {str(e)}")
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Error reading resource: {str(e)}"
                }
            ]
            
    async def _read_queue_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read queue resource."""
        # Check if queue manager is available
        if not self.queue_manager:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": "Queue manager not available"
                }
            ]
            
        # Parse queue ID from URI
        try:
            # Format: queue://{queue_id}
            queue_id = uri.split("://")[1]
        except:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Invalid queue resource URI: {uri}"
                }
            ]
            
        # Get queue status
        try:
            # Note: We're ignoring the API key check here as the MCP server
            # already handles authentication. In a real implementation,
            # you'd need to ensure proper authorization.
            status = self.queue_manager.queue.get(queue_id)
            
            if not status:
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Queue item {queue_id} not found"
                    }
                ]
                
            # Format response based on status
            if status.status == "completed":
                return [
                    {
                        "uri": uri,
                        "mime_type": "application/json",
                        "text": json.dumps({
                            "status": status.status,
                            "result": status.result,
                            "created_at": status.created_at,
                            "updated_at": status.updated_at
                        })
                    }
                ]
            elif status.status == "failed":
                return [
                    {
                        "uri": uri,
                        "mime_type": "application/json",
                        "text": json.dumps({
                            "status": status.status,
                            "error": status.error,
                            "created_at": status.created_at,
                            "updated_at": status.updated_at
                        })
                    }
                ]
            else:
                return [
                    {
                        "uri": uri,
                        "mime_type": "application/json",
                        "text": json.dumps({
                            "status": status.status,
                            "queue_id": status.queue_id,
                            "created_at": status.created_at,
                            "updated_at": status.updated_at
                        })
                    }
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting queue status for {queue_id}: {str(e)}")
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Error getting queue status: {str(e)}"
                }
            ]
            
    async def _read_docs_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read documentation resource."""
        # Parse resource path from URI
        try:
            # Format: docs://{resource_path}
            resource_path = uri.split("://")[1]
        except:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Invalid documentation resource URI: {uri}"
                }
            ]
            
        # Handle different documentation resources
        if resource_path == "openapi.json":
            # Return OpenAPI schema
            try:
                from ..api.generator import OpenAPIGenerator
                if not self.api_registry:
                    return [
                        {
                            "uri": uri,
                            "mime_type": "text/plain",
                            "text": "API registry not available"
                        }
                    ]
                    
                generator = OpenAPIGenerator(self.api_registry)
                schema = generator.generate_schema()
                
                return [
                    {
                        "uri": uri,
                        "mime_type": "application/json",
                        "text": json.dumps(schema)
                    }
                ]
            except Exception as e:
                self.logger.error(f"Error generating OpenAPI schema: {str(e)}")
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Error generating OpenAPI schema: {str(e)}"
                    }
                ]
                
        elif resource_path == "readme":
            # Return server documentation
            try:
                with open("README.md", "r") as f:
                    content = f.read()
                    
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/markdown",
                        "text": content
                    }
                ]
            except Exception as e:
                self.logger.error(f"Error reading README.md: {str(e)}")
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Error reading documentation: {str(e)}"
                    }
                ]
                
        elif resource_path.startswith("api/"):
            # Return API endpoint documentation
            try:
                endpoint = resource_path[4:]  # Remove "api/" prefix
                
                if not self.api_registry or endpoint not in self.api_registry:
                    return [
                        {
                            "uri": uri,
                            "mime_type": "text/plain",
                            "text": f"API endpoint {endpoint} not found"
                        }
                    ]
                    
                api_info = self.api_registry[endpoint]
                
                return [
                    {
                        "uri": uri,
                        "mime_type": "application/json",
                        "text": json.dumps({
                            "name": api_info.get('display_name', endpoint),
                            "description": api_info.get('description', ''),
                            "category": api_info.get('category', ''),
                            "queue_mode": api_info.get('queue_mode', False)
                        })
                    }
                ]
            except Exception as e:
                self.logger.error(f"Error getting API documentation for {resource_path}: {str(e)}")
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Error getting API documentation: {str(e)}"
                    }
                ]
                
        else:
            # Unknown documentation resource
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Unknown documentation resource: {resource_path}"
                }
            ]
            
    async def _read_logs_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Read logs resource."""
        # Parse resource path from URI
        try:
            # Format: logs://{resource_path}
            resource_path = uri.split("://")[1]
        except:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Invalid logs resource URI: {uri}"
                }
            ]
            
        # Check if logs are enabled
        if not self.config.log_enabled:
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": "Logs are not enabled on this server"
                }
            ]
            
        # Handle different logs resources
        if resource_path == "server":
            # Return server logs
            try:
                with open(self.config.log_file, "r") as f:
                    content = f.read()
                    
                # Get last 100 lines
                lines = content.splitlines()
                if len(lines) > 100:
                    lines = lines[-100:]
                    
                content = "\n".join(lines)
                    
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": content
                    }
                ]
            except Exception as e:
                self.logger.error(f"Error reading logs: {str(e)}")
                return [
                    {
                        "uri": uri,
                        "mime_type": "text/plain",
                        "text": f"Error reading logs: {str(e)}"
                    }
                ]
                
        else:
            # Unknown logs resource
            return [
                {
                    "uri": uri,
                    "mime_type": "text/plain",
                    "text": f"Unknown logs resource: {resource_path}"
                }
            ]

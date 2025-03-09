"""Tool registry for MCP server."""

import logging
import json
from typing import Dict, Any, List, Optional

from ..utils import ConfigManager
from ..models import APIError, APIErrorCode

class ToolRegistry:
    """Registry for MCP tools mapped from API endpoints."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        """Initialize tool registry."""
        self.config = config
        self.logger = logger
        self.api_executor = None
        self.api_registry = None
        self.tools: Dict[str, Dict[str, Any]] = {}
        
    async def setup(self, api_executor, api_registry):
        """Set up tool registry with API executor and registry."""
        self.api_executor = api_executor
        self.api_registry = api_registry
        
        # Map APIs to tools if enabled
        if self.config.mcp_auto_map_apis:
            await self._map_apis_to_tools()
            
        # Add additional tools from config
        await self._add_additional_tools()
        
    async def _map_apis_to_tools(self):
        """Map API endpoints to MCP tools."""
        if not self.api_registry:
            self.logger.warning("API registry not available, cannot map APIs to tools")
            return
            
        # Get excluded APIs
        excluded_apis = set(self.config.mcp_excluded_apis)
        
        # Map each API endpoint to a tool
        for api_path, api_info in self.api_registry.items():
            # Skip excluded APIs
            if api_path in excluded_apis:
                continue
                
            # Get tool information
            cls = api_info.get('class')
            if not cls:
                continue
                
            # Create tool name
            tool_name = self._api_path_to_tool_name(api_path)
            
            # Get input schema
            input_schema = self._get_input_schema(cls)
            
            # Set up tool definition
            self.tools[tool_name] = {
                'name': tool_name,
                'description': api_info.get('description') or cls.__doc__ or f"API endpoint for {api_path}",
                'input_schema': input_schema,
                'api_path': api_path,
                'queue_mode': api_info.get('queue_mode', False)
            }
            
            self.logger.info(f"Mapped API {api_path} to MCP tool {tool_name}")
            
    def _api_path_to_tool_name(self, api_path: str) -> str:
        """Convert API path to tool name."""
        # Replace slashes with underscores
        return api_path.replace('/', '_')
        
    def _get_input_schema(self, cls) -> Dict[str, Any]:
        """Convert INPUT_TYPES to MCP input schema."""
        input_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Get input types method
        input_types_method = getattr(cls, 'INPUT_TYPES', None)
        if not callable(input_types_method):
            return input_schema
            
        # Get input types
        input_types = input_types_method()
        
        # Process required parameters
        for param_name, param_info in input_types.get('required', {}).items():
            schema = self._convert_type_to_json_schema(param_info)
            input_schema['properties'][param_name] = schema
            input_schema['required'].append(param_name)
            
        # Process optional parameters
        for param_name, param_info in input_types.get('optional', {}).items():
            schema = self._convert_type_to_json_schema(param_info)
            input_schema['properties'][param_name] = schema
            
        return input_schema
        
    def _convert_type_to_json_schema(self, type_info) -> Dict[str, Any]:
        """Convert ComfyUI type to JSON Schema."""
        schema = {}
        
        if isinstance(type_info, tuple) and len(type_info) > 0:
            type_name = type_info[0]
            
            # Check type
            if isinstance(type_name, list):
                # Enum
                schema = {
                    "type": "string",
                    "enum": type_name
                }
            elif type_name in ["IMAGE", "VIDEO", "FILE"]:
                # Base64 encoded string
                schema = {
                    "type": "string",
                    "format": "base64",
                    "description": f"Base64 encoded {type_name.lower()}"
                }
            elif type_name in ["FLOAT", "NUMBER"]:
                # Number
                schema = {
                    "type": "number"
                }
                
                # Check for min/max
                if len(type_info) > 1 and isinstance(type_info[1], dict):
                    if "min" in type_info[1]:
                        schema["minimum"] = type_info[1]["min"]
                    if "max" in type_info[1]:
                        schema["maximum"] = type_info[1]["max"]
                    if "step" in type_info[1]:
                        schema["multipleOf"] = type_info[1]["step"]
                    if "default" in type_info[1]:
                        schema["default"] = type_info[1]["default"]
                        
            elif type_name == "INT" or type_name == "INTEGER":
                # Integer
                schema = {
                    "type": "integer"
                }
                
                # Check for min/max
                if len(type_info) > 1 and isinstance(type_info[1], dict):
                    if "min" in type_info[1]:
                        schema["minimum"] = type_info[1]["min"]
                    if "max" in type_info[1]:
                        schema["maximum"] = type_info[1]["max"]
                    if "step" in type_info[1]:
                        schema["multipleOf"] = type_info[1]["step"]
                    if "default" in type_info[1]:
                        schema["default"] = type_info[1]["default"]
                        
            elif type_name == "BOOLEAN":
                # Boolean
                schema = {
                    "type": "boolean"
                }
                
                if len(type_info) > 1 and isinstance(type_info[1], dict):
                    if "default" in type_info[1]:
                        schema["default"] = type_info[1]["default"]
                
            elif type_name == "STRING":
                # String
                schema = {
                    "type": "string"
                }
                
                if len(type_info) > 1 and isinstance(type_info[1], dict):
                    if "default" in type_info[1]:
                        schema["default"] = type_info[1]["default"]
                        
            elif type_name == "DICT":
                # Dictionary
                schema = {
                    "type": "object"
                }
                
            elif type_name == "LIST":
                # List
                schema = {
                    "type": "array"
                }
                
            else:
                # Unknown type
                schema = {
                    "type": "string",
                    "description": f"Unknown type: {type_name}"
                }
        else:
            schema = {
                "type": "string",
                "description": "Unknown type"
            }
        
        return schema
        
    async def _add_additional_tools(self):
        """Add additional tools from config."""
        for tool_config in self.config.mcp_additional_tools:
            tool_name = tool_config.get('name')
            if not tool_name:
                self.logger.warning("Tool configuration missing name, skipping")
                continue
                
            self.tools[tool_name] = {
                'name': tool_name,
                'description': tool_config.get('description', ''),
                'input_schema': tool_config.get('input_schema', {}),
                'handler': tool_config.get('handler'),
                'custom': True
            }
            
            self.logger.info(f"Added custom MCP tool {tool_name}")
            
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [
            {
                'name': tool_info['name'],
                'description': tool_info['description'],
                'input_schema': tool_info['input_schema']
            }
            for tool_info in self.tools.values()
        ]
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool."""
        # Check if tool exists
        if tool_name not in self.tools:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Tool {tool_name} not found"
                    }
                ],
                'is_error': True
            }
            
        tool_info = self.tools[tool_name]
        
        try:
            # Handle custom tool
            if tool_info.get('custom'):
                if callable(tool_info.get('handler')):
                    result = await tool_info['handler'](arguments)
                    return result
                else:
                    return {
                        'content': [
                            {
                                'type': 'text',
                                'text': f"Tool {tool_name} has no handler"
                            }
                        ],
                        'is_error': True
                    }
            
            # Handle API-mapped tool
            api_path = tool_info.get('api_path')
            if not api_path or not self.api_executor:
                return {
                    'content': [
                        {
                            'type': 'text',
                            'text': f"Tool {tool_name} is not properly configured"
                        }
                    ],
                    'is_error': True
                }
                
            # Execute API
            result = await self.api_executor.execute_api(api_path, arguments)
            
            # Format result
            return {
                'content': [
                    {
                        'type': 'json',
                        'json': result
                    }
                ],
                'is_error': False
            }
            
        except APIError as e:
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': e.message
                    }
                ],
                'is_error': True
            }
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': f"Error executing tool: {str(e)}"
                    }
                ],
                'is_error': True
            }

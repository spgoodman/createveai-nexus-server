"""OpenAPI schema generator for API endpoints."""

from typing import Dict, Any, List, Optional
import re

class OpenAPIGenerator:
    """OpenAPI schema generator for API endpoints."""
    
    def __init__(self, apis: Dict[str, Dict[str, Any]], config=None):
        self.apis = apis
        self.config = config
    
    def generate_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI schema for all API endpoints."""
        paths = {}
        schemas = {
            "QueueRequest": {
                "type": "object",
                "properties": {
                    "queue_id": {
                        "type": "string",
                        "description": "Queue ID for a previously submitted request"
                    }
                },
                "required": ["queue_id"]
            },
            "QueueResponse": {
                "type": "object",
                "properties": {
                    "queue_id": {
                        "type": "string",
                        "description": "Queue ID for the submitted request"
                    }
                }
            }
        }
        
        # Add path for each API
        for api_path, api_info in self.apis.items():
            cls = api_info['class']
            schema_name = self._get_schema_name(api_path)
            
            # Generate schemas
            request_schema = self._generate_request_schema(cls, schema_name)
            response_schema = self._generate_response_schema(cls, schema_name)
            
            # Add schemas to components
            schemas[f"{schema_name}Request"] = request_schema
            schemas[f"{schema_name}Response"] = response_schema
            
            # Generate path
            path = self._generate_path(api_path, api_info, schema_name)
            paths[f"/api/{api_path}"] = path
            
            # Add queue path if in queue mode
            if api_info.get('queue_mode', False):
                queue_path = self._generate_queue_path(api_path, api_info, schema_name)
                paths[f"/api/{api_path}/queue"] = queue_path
        
        # Build schema
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Createve.AI API Server",
                "description": "API server for various services",
                "version": "1.0.0"
            },
            # Adding servers array which is required by the OpenAPI spec
            "servers": self._generate_servers(),
            "paths": paths,
            "components": {
                "schemas": schemas,
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "API key"
                    }
                }
            },
            "security": [
                {
                    "bearerAuth": []
                }
            ]
        }
    
    def _get_schema_name(self, api_path: str) -> str:
        """Convert API path to valid schema name."""
        # Replace slashes with underscores
        name = api_path.replace('/', '_')
        
        # Capitalize each word
        name = ''.join(word.capitalize() for word in name.split('_'))
        
        return name
    
    def _generate_request_schema(self, cls, schema_name: str) -> Dict[str, Any]:
        """Generate request schema for API endpoint."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Get input types
        input_types = self._get_input_types(cls)
        
        # Add required properties
        for field, type_info in input_types.get('required', {}).items():
            property_schema = self._convert_type_to_schema(type_info)
            schema["properties"][field] = property_schema
            schema["required"].append(field)
        
        # Add optional properties
        for field, type_info in input_types.get('optional', {}).items():
            property_schema = self._convert_type_to_schema(type_info)
            schema["properties"][field] = property_schema
        
        return schema
    
    def _generate_response_schema(self, cls, schema_name: str) -> Dict[str, Any]:
        """Generate response schema for API endpoint."""
        schema = {
            "type": "object",
            "properties": {}
        }
        
        # Get return types
        return_types = getattr(cls, 'RETURN_TYPES', None)
        return_names = getattr(cls, 'RETURN_NAMES', None)
        
        if return_types and isinstance(return_types, tuple):
            for i, type_name in enumerate(return_types):
                # Get field name
                if return_names and i < len(return_names):
                    field = return_names[i]
                else:
                    field = f"output_{i}"
                
                # Add property
                property_schema = self._convert_type_to_json_schema(type_name)
                schema["properties"][field] = property_schema
        
        return schema
    
    def _generate_path(self, api_path: str, api_info: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """Generate path for API endpoint."""
        method = {
            "post": {
                "summary": api_info.get('display_name', api_path),
                "description": api_info.get('description', ''),
                "tags": [api_info.get('category', 'api')],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{schema_name}Request"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{schema_name}Response"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request"
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "404": {
                        "description": "Not found"
                    },
                    "500": {
                        "description": "Server error"
                    }
                }
            }
        }
        
        # If queue mode, return queue ID instead of response
        if api_info.get('queue_mode', False):
            method["post"]["responses"]["200"]["content"]["application/json"]["schema"] = {
                "$ref": "#/components/schemas/QueueResponse"
            }
        
        return method
    
    def _generate_queue_path(self, api_path: str, api_info: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """Generate queue path for API endpoint."""
        return {
            "post": {
                "summary": f"Check queue status for {api_info.get('display_name', api_path)}",
                "description": "Check status of a queued request",
                "tags": [api_info.get('category', 'api')],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/QueueRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Queue status or result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "oneOf": [
                                        {
                                            "$ref": "#/components/schemas/QueueResponse"
                                        },
                                        {
                                            "$ref": f"#/components/schemas/{schema_name}Response"
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request"
                    },
                    "401": {
                        "description": "Unauthorized"
                    },
                    "404": {
                        "description": "Not found"
                    },
                    "500": {
                        "description": "Server error"
                    }
                }
            }
        }
    
    def _get_input_types(self, cls) -> Dict[str, Dict[str, Any]]:
        """Get input types for class."""
        try:
            input_types_method = getattr(cls, 'INPUT_TYPES')
            if callable(input_types_method):
                input_types = input_types_method()
            else:
                input_types = input_types_method
                
            return input_types
        except Exception as e:
            return {}
    
    def _convert_type_to_schema(self, type_info) -> Dict[str, Any]:
        """Convert ComfyUI type to OpenAPI schema."""
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
                    if "placeholder" in type_info[1]:
                        schema["description"] = type_info[1]["placeholder"]
                        
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
                    if "placeholder" in type_info[1]:
                        schema["description"] = type_info[1]["placeholder"]
                        
            elif type_name == "BOOLEAN":
                # Boolean
                schema = {
                    "type": "boolean"
                }
                
            elif type_name == "STRING":
                # String
                schema = {
                    "type": "string"
                }
                
                # Check for multiline
                if len(type_info) > 1 and isinstance(type_info[1], dict):
                    if "multiline" in type_info[1] and type_info[1]["multiline"]:
                        schema["format"] = "text"
                    if "default" in type_info[1]:
                        schema["default"] = type_info[1]["default"]
                    if "placeholder" in type_info[1]:
                        schema["description"] = type_info[1]["placeholder"]
                        
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
    
    def _generate_servers(self) -> List[Dict[str, str]]:
        """Generate servers array for OpenAPI schema."""
        servers = []
        
        # Use configuration if available
        if self.config:
            host = self.config.host
            port = self.config.port
            
            # Add the main configured host
            servers.append({
                "url": f"http://{host}:{port}",
                "description": "Primary server"
            })
            
            # Include alternative access methods only if they differ from the main host
            if host != 'localhost' and host != '127.0.0.1':
                servers.append({
                    "url": f"http://localhost:{port}",
                    "description": "Local access"
                })
            
            if host != '0.0.0.0' and host != 'localhost':
                servers.append({
                    "url": f"http://0.0.0.0:{port}",
                    "description": "All interfaces"
                })
            
            # Include internal IP if different
            if host != '127.0.0.1' and host != 'localhost':
                servers.append({
                    "url": f"http://127.0.0.1:{port}",
                    "description": "Loopback access"
                })
        else:
            # Default if no configuration available
            servers.append({
                "url": "http://localhost:43080",
                "description": "Default server"
            })
        
        return servers
    
    def _convert_type_to_json_schema(self, type_name: str) -> Dict[str, Any]:
        """Convert ComfyUI type to JSON schema."""
        if type_name in ["IMAGE", "VIDEO", "FILE"]:
            return {
                "type": "string",
                "format": "base64",
                "description": f"Base64 encoded {type_name.lower()}"
            }
        elif type_name in ["FLOAT", "NUMBER"]:
            return {
                "type": "number"
            }
        elif type_name in ["INT", "INTEGER"]:
            return {
                "type": "integer"
            }
        elif type_name == "BOOLEAN":
            return {
                "type": "boolean"
            }
        elif type_name == "STRING":
            return {
                "type": "string"
            }
        elif type_name == "DICT":
            return {
                "type": "object"
            }
        elif type_name == "LIST":
            return {
                "type": "array"
            }
        else:
            return {
                "type": "string",
                "description": f"Unknown type: {type_name}"
            }

"""
Createve.AI Nexus Server - Main entry point.

This is a simplified version for testing the MCP concepts.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List

import yaml
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("nexus-server")

# Create FastAPI app
app = FastAPI(
    title="Createve.AI Nexus Server",
    description="API and MCP server for various services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Simple in-memory storage for demo
api_registry = {
    "text_processing/textAnalyzer": {
        "class": None,  # No actual class implementation for demo
        "display_name": "Text Analyzer",
        "description": "Analyzes text for sentiment and statistics",
        "category": "text",
        "queue_mode": False
    },
    "text_processing/textSummarizer": {
        "class": None,  # No actual class implementation for demo
        "display_name": "Text Summarizer",
        "description": "Summarizes text to the specified length",
        "category": "text",
        "queue_mode": True
    }
}

# Connected WebSocket clients
active_connections: List[WebSocket] = []

# API Keys (normally loaded from config)
API_KEYS = ["sk-apiservertest1", "sk-apiservertest2", "sk-apiservertest3"]

# Set up demo handlers
@app.get("/")
async def root():
    return {"message": "Welcome to Createve.AI Nexus Server"}

@app.get("/api/info")
async def api_info():
    return {
        "title": "Createve.AI Nexus Server",
        "version": "1.0.0",
        "description": "API and MCP server for various services",
        "endpoints": list(api_registry.keys())
    }

# Set up WebSocket endpoint for MCP
@app.websocket("/mcp")
async def mcp_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send server info
        await websocket.send_json({
            "type": "server_info", 
            "name": "createveai-nexus",
            "version": "1.0.0",
            "description": "Createve.AI Nexus Server MCP Interface"
        })
        
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "capabilities_request":
                await websocket.send_json({
                    "type": "capabilities_response",
                    "capabilities": {
                        "tools": True,
                        "resources": True
                    }
                })
                
            elif message_type == "list_tools_request":
                tools = []
                for api_path, api_info in api_registry.items():
                    tool_name = api_path.replace("/", "_")
                    tools.append({
                        "name": tool_name,
                        "description": api_info.get("description", ""),
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string"
                                }
                            },
                            "required": ["text"]
                        }
                    })
                
                await websocket.send_json({
                    "type": "list_tools_response",
                    "tools": tools
                })
                
            elif message_type == "call_tool_request":
                tool_name = data.get("name")
                request_id = data.get("request_id")
                arguments = data.get("arguments", {})
                
                api_path = tool_name.replace("_", "/")
                api_info = api_registry.get(api_path)
                
                if not api_info:
                    await websocket.send_json({
                        "type": "error",
                        "code": "tool_not_found",
                        "message": f"Tool {tool_name} not found",
                        "request_id": request_id
                    })
                    continue
                
                # Check if queue mode
                if api_info.get("queue_mode", False):
                    # Return a queue ID
                    queue_id = f"demo-queue-{hash(tool_name + str(arguments))}"
                    await websocket.send_json({
                        "type": "call_tool_response",
                        "request_id": request_id,
                        "content": [
                            {
                                "type": "json",
                                "json": {
                                    "queue_id": queue_id
                                }
                            }
                        ],
                        "is_error": False
                    })
                else:
                    # For non-queue mode, return a demo result
                    if "text_analyzer" in tool_name.lower():
                        # Demo text analyzer result
                        result = {
                            "analysis_results": {
                                "statistics": {
                                    "character_count": len(arguments.get("text", "")),
                                    "word_count": len(arguments.get("text", "").split()),
                                    "line_count": len(arguments.get("text", "").splitlines()),
                                    "average_word_length": 4.5
                                },
                                "sentiment": {
                                    "assessment": "positive",
                                    "positive_word_count": 2,
                                    "negative_word_count": 0
                                }
                            }
                        }
                    else:
                        # Generic result
                        result = {
                            "result": f"Processed {tool_name} with arguments: {arguments}"
                        }
                    
                    await websocket.send_json({
                        "type": "call_tool_response",
                        "request_id": request_id,
                        "content": [
                            {
                                "type": "json",
                                "json": result
                            }
                        ],
                        "is_error": False
                    })
                    
            elif message_type == "list_resources_request":
                # Return demo resources
                resources = [
                    {
                        "uri": "docs://readme",
                        "name": "Server Documentation",
                        "description": "Documentation for the Createve.AI Nexus Server",
                        "mime_type": "text/markdown"
                    },
                    {
                        "uri": "docs://openapi.json",
                        "name": "OpenAPI Schema",
                        "description": "Full OpenAPI specification for the API server",
                        "mime_type": "application/json"
                    }
                ]
                
                await websocket.send_json({
                    "type": "list_resources_response",
                    "resources": resources
                })
                
            elif message_type == "list_resource_templates_request":
                # Return demo resource templates
                templates = [
                    {
                        "uri_template": "queue://{queue_id}",
                        "name": "Queue Status",
                        "description": "Status and result for a queued request",
                        "mime_type": "application/json"
                    }
                ]
                
                await websocket.send_json({
                    "type": "list_resource_templates_response",
                    "resource_templates": templates
                })
                
            elif message_type == "read_resource_request":
                uri = data.get("uri")
                request_id = data.get("request_id")
                
                if uri == "docs://readme":
                    with open("README.md", "r") as f:
                        content = f.read()
                    
                    await websocket.send_json({
                        "type": "read_resource_response",
                        "request_id": request_id,
                        "contents": [
                            {
                                "uri": uri,
                                "mime_type": "text/markdown",
                                "text": content
                            }
                        ]
                    })
                elif uri.startswith("queue://"):
                    # Demo queue status
                    queue_id = uri.split("://")[1]
                    
                    await websocket.send_json({
                        "type": "read_resource_response",
                        "request_id": request_id,
                        "contents": [
                            {
                                "uri": uri,
                                "mime_type": "application/json",
                                "text": json.dumps({
                                    "status": "completed",
                                    "result": {
                                        "summary": "This is a demo summary result"
                                    },
                                    "created_at": 1648253647.8,
                                    "updated_at": 1648253650.2
                                })
                            }
                        ]
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "code": "resource_not_found",
                        "message": f"Resource {uri} not found",
                        "request_id": request_id
                    })
                    
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "code": "unknown_message_type",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# HTTP endpoint for API calls (demo)
@app.post("/api/{module}/{endpoint}")
async def handle_api_request(module: str, endpoint: str):
    api_path = f"{module}/{endpoint}"
    
    if api_path not in api_registry:
        return {"error": "API endpoint not found"}
    
    api_info = api_registry[api_path]
    
    # Check if queue mode
    if api_info.get("queue_mode", False):
        # Return a queue ID
        queue_id = f"demo-queue-{hash(api_path)}"
        return {"queue_id": queue_id}
    
    # For non-queue mode, return a demo result
    if "textanalyzer" in endpoint.lower():
        # Demo text analyzer result
        return {
            "analysis_results": {
                "statistics": {
                    "character_count": 100,
                    "word_count": 20,
                    "line_count": 1,
                    "average_word_length": 4.5
                },
                "sentiment": {
                    "assessment": "positive",
                    "positive_word_count": 2,
                    "negative_word_count": 0
                }
            }
        }
    else:
        # Generic result
        return {"result": f"Processed {api_path}"}

if __name__ == "__main__":
    logger.info("Starting Createve.AI Nexus Server")
    uvicorn.run(app, host="0.0.0.0", port=43080)

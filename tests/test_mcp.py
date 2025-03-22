"""Tests for MCP server functionality."""

import os
import pytest
import asyncio
from fastapi.testclient import TestClient
import json
from api_server.core.app import create_app

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_app():
    """Create test application."""
    app = await create_app("tests/test_config.yaml")
    return app

@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)

async def test_mcp_endpoints(test_client):
    """Test MCP endpoints."""
    # Test modelcontextprotocol/invoke endpoint
    response = test_client.post("/modelcontextprotocol/invoke", json={
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "capabilities",
        "params": {}
    })
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert "result" in data or "error" in data

async def test_mcp_tools(test_client):
    """Test MCP tools."""
    # Test calling a tool
    response = test_client.post("/modelcontextprotocol/invoke", json={
        "jsonrpc": "2.0",
        "id": "test-2",
        "method": "call_tool",
        "params": {
            "name": "api_path_tool",
            "arguments": {
                "arg1": "test",
                "arg2": 123
            }
        }
    })
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert "result" in data or "error" in data

    if "result" in data:
        result = data["result"]
        assert "content" in result
        assert "is_error" in result
        assert not result["is_error"]

async def test_mcp_resources(test_client):
    """Test MCP resources."""
    # Test reading a resource
    response = test_client.post("/modelcontextprotocol/invoke", json={
        "jsonrpc": "2.0",
        "id": "test-3",
        "method": "read_resource",
        "params": {
            "uri": "resource://example"
        }
    })
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert "result" in data or "error" in data

    if "result" in data:
        result = data["result"]
        assert "content" in result
        assert isinstance(result["content"], str)

async def test_error_handling(test_client):
    """Test MCP error handling."""
    # Test invalid method
    response = test_client.post("/modelcontextprotocol/invoke", json={
        "jsonrpc": "2.0",
        "id": "test-4",
        "method": "invalid_method",
        "params": {}
    })
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"
    assert "id" in data
    assert "error" in data
    
    error = data["error"]
    assert "code" in error
    assert "message" in error

    # Test invalid tool name
    response = test_client.post("/modelcontextprotocol/invoke", json={
        "jsonrpc": "2.0",
        "id": "test-5",
        "method": "call_tool",
        "params": {
            "name": "nonexistent_tool",
            "arguments": {}
        }
    })
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == -32601  # Method not found

async def test_openapi_schema(test_client):
    """Test OpenAPI schema generation."""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "/modelcontextprotocol/invoke" in schema["paths"]
    
    # Check MCP path
    mcp_path = schema["paths"]["/modelcontextprotocol/invoke"]
    assert "post" in mcp_path
    assert "Agentic" in mcp_path["post"]["tags"]

    # Check required definitions
    definitions = schema.get("definitions", schema.get("components", {}).get("schemas", {}))
    assert "QueryRequest" in definitions
    assert "QueryResponse" in definitions

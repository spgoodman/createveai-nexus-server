"""
Test client for the MCP server functionality of Createve.AI Nexus Server.

This script connects to the MCP WebSocket endpoint, interacts with tools and resources,
and demonstrates the core functionality of the MCP protocol.
"""

import asyncio
import json
import sys
import websockets

# Configuration
MCP_WS_URL = "ws://localhost:43080/mcp"

async def run_test_client():
    """Run the test client."""
    print(f"Connecting to MCP server at {MCP_WS_URL}...")
    
    async with websockets.connect(MCP_WS_URL) as websocket:
        print("Connected to MCP server")
        
        # Receive server info
        response = await websocket.recv()
        server_info = json.loads(response)
        print(f"\n=== Server Info ===")
        print(json.dumps(server_info, indent=2))
        
        # Request capabilities
        print("\n=== Requesting Capabilities ===")
        await websocket.send(json.dumps({
            "type": "capabilities_request"
        }))
        response = await websocket.recv()
        capabilities = json.loads(response)
        print(json.dumps(capabilities, indent=2))
        
        # List tools
        print("\n=== Requesting Tools ===")
        await websocket.send(json.dumps({
            "type": "list_tools_request"
        }))
        response = await websocket.recv()
        tools = json.loads(response)
        print(json.dumps(tools, indent=2))
        
        # List resources
        print("\n=== Requesting Resources ===")
        await websocket.send(json.dumps({
            "type": "list_resources_request"
        }))
        response = await websocket.recv()
        resources = json.loads(response)
        print(json.dumps(resources, indent=2))
        
        # List resource templates
        print("\n=== Requesting Resource Templates ===")
        await websocket.send(json.dumps({
            "type": "list_resource_templates_request"
        }))
        response = await websocket.recv()
        templates = json.loads(response)
        print(json.dumps(templates, indent=2))
        
        # Execute direct tool (Text Analyzer)
        print("\n=== Executing Text Analyzer Tool ===")
        await websocket.send(json.dumps({
            "type": "call_tool_request",
            "request_id": "test-1",
            "name": "text_processing_textAnalyzer",
            "arguments": {
                "text": "This is a test message that should be analyzed. It's a great example of a positive statement!"
            }
        }))
        response = await websocket.recv()
        result = json.loads(response)
        print(json.dumps(result, indent=2))
        
        # Execute queue tool (Text Summarizer)
        print("\n=== Executing Text Summarizer Tool (Queue Mode) ===")
        await websocket.send(json.dumps({
            "type": "call_tool_request",
            "request_id": "test-2",
            "name": "text_processing_textSummarizer",
            "arguments": {
                "text": "This is a test message with multiple sentences. It should be summarized. The summarizer should pick the most important sentences. This is a great example of how the queue system works."
            }
        }))
        response = await websocket.recv()
        queue_result = json.loads(response)
        print(json.dumps(queue_result, indent=2))
        
        # Extract queue ID
        queue_id = None
        if queue_result["type"] == "call_tool_response" and not queue_result["is_error"]:
            for content in queue_result["content"]:
                if content["type"] == "json" and "queue_id" in content["json"]:
                    queue_id = content["json"]["queue_id"]
        
        if queue_id:
            # Check queue status
            print(f"\n=== Checking Queue Status for ID: {queue_id} ===")
            await websocket.send(json.dumps({
                "type": "read_resource_request",
                "request_id": "test-3",
                "uri": f"queue://{queue_id}"
            }))
            response = await websocket.recv()
            status = json.loads(response)
            print(json.dumps(status, indent=2))
        
        # Read documentation resource
        print("\n=== Reading Documentation Resource ===")
        await websocket.send(json.dumps({
            "type": "read_resource_request",
            "request_id": "test-4",
            "uri": "docs://readme"
        }))
        response = await websocket.recv()
        doc = json.loads(response)
        print(f"Resource type: {doc['contents'][0]['mime_type']}")
        print(f"Resource length: {len(doc['contents'][0]['text'])} characters")
        print(f"Resource preview: {doc['contents'][0]['text'][:150]}...")
        
        # Try invalid tool
        print("\n=== Testing Error Handling with Invalid Tool ===")
        await websocket.send(json.dumps({
            "type": "call_tool_request",
            "request_id": "test-5",
            "name": "nonexistent_tool",
            "arguments": {}
        }))
        response = await websocket.recv()
        error = json.loads(response)
        print(json.dumps(error, indent=2))
        
        print("\n=== Test Complete ===")

if __name__ == "__main__":
    try:
        asyncio.run(run_test_client())
    except KeyboardInterrupt:
        print("Test client stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

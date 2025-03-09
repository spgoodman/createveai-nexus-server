import asyncio
import json
import websockets
import sys

async def test_mcp_server():
    # Connect to the MCP server
    headers = {"Authorization": "Bearer sk-apiservertest1"}
    uri = "ws://10.152.0.5:43080/mcp"
    
    print(f"Connecting to {uri} with auth header...")
    
    try:
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            print("Connected successfully!")
            
            # Expect server_info message
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received server info: {json.dumps(response_data, indent=2)}")
            
            # Request capabilities
            print("\nSending capabilities request...")
            await websocket.send(json.dumps({
                "type": "capabilities_request"
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received capabilities: {json.dumps(response_data, indent=2)}")
            
            # List tools
            print("\nSending list_tools_request...")
            await websocket.send(json.dumps({
                "type": "list_tools_request"
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received tools list: {json.dumps(response_data, indent=2)}")
            
            # Use text_processing_textAnalyzer tool
            print("\nSending call_tool_request for text_processing_textAnalyzer...")
            await websocket.send(json.dumps({
                "type": "call_tool_request",
                "request_id": "test-123",
                "name": "text_processing_textAnalyzer",
                "arguments": {
                    "text": "This is a test message. I'm very happy with the MCP integration!",
                    "include_sentiment": True,
                    "include_statistics": True
                }
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Received tool response: {json.dumps(response_data, indent=2)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)

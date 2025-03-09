"""
Createve.AI Nexus Server - Main entry point.

This is the main entry point for the Createve.AI Nexus Server, which combines REST API
and Model Context Protocol (MCP) functionality in a single unified platform.
"""

import argparse
import asyncio
import logging
import os
import sys
import uvicorn
from src.api_server.core.app import create_app

# Handle command line arguments
parser = argparse.ArgumentParser(description="Createve.AI Nexus Server")
parser.add_argument("--config", type=str, default="./config.yaml", help="Path to config file")
parser.add_argument("--host", type=str, help="Host to listen on (overrides config)")
parser.add_argument("--port", type=int, help="Port to listen on (overrides config)")
parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
args = parser.parse_args()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("nexus-server")

async def main():
    # Create the application
    logger.info(f"Creating application using config: {args.config}")
    app = await create_app(args.config)
    
    # Get config from app
    from src.api_server.utils import ConfigManager
    config = ConfigManager(args.config)
    
    # Override host/port if provided in command line arguments
    host = args.host if args.host else config.host
    port = args.port if args.port else config.port
    
    # Ensure host is 0.0.0.0 to listen on all interfaces if it's localhost
    if host == "localhost":
        logger.warning("Changing host from 'localhost' to '0.0.0.0' to allow external access")
        host = "0.0.0.0"
    
    logger.info(f"Server configured to run on {host}:{port}")
    return app, host, port

# Run the server
if __name__ == "__main__":
    # Get application and config
    app, host, port = asyncio.run(main())
    
    # Run the server
    print(f"Starting Createve.AI Nexus Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=args.reload)

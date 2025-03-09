"""Main application factory for the Createve.AI Nexus Server."""

import asyncio
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..utils import ConfigManager, LoggingManager
from .security import SecurityManager
from .queue import QueueManager
from ..api import APILoader, APIExecutor, OpenAPIGenerator, RouteGenerator
from ..mcp import MCPServer

async def create_app(config_path: str = "./config.yaml"):
    """Create a new FastAPI application instance."""
    # Initialize config
    config = ConfigManager(config_path)
    
    # Initialize logging
    logging_manager = LoggingManager(config)
    logger = logging_manager.logger
    
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
    
    # Add authentication middleware
    security_manager = SecurityManager(config, logger)
    app.middleware("http")(security_manager.authenticate_request)
    
    # Load APIs
    api_loader = APILoader(config, logger)
    apis = await api_loader.load_apis()
    
    # Create API executor
    api_executor = APIExecutor(apis, logger)
    
    # Create queue manager
    queue_manager = QueueManager(config, logger)
    await queue_manager.start_workers(api_executor)
    
    # Create OpenAPI generator
    openapi_generator = OpenAPIGenerator(apis)
    
    # Create routes
    route_generator = RouteGenerator(
        app,
        apis,
        api_executor,
        queue_manager,
        security_manager,
        openapi_generator,
        logger
    )
    route_generator.generate_routes()
    
    # Initialize MCP server (if enabled)
    if config.mcp_enabled:
        logger.info("Initializing MCP server")
        mcp_server = MCPServer(app, config, logger, security_manager)
        await mcp_server.setup_registries(api_executor, queue_manager, apis)
        logger.info(f"MCP server initialized: {config.mcp_server_name}")
    else:
        logger.info("MCP server is disabled")
    
    # Add file watcher for API changes
    if config.reload_on_api_dir_change or config.reload_on_api_file_change:
        @app.on_event("startup")
        async def start_api_watcher():
            asyncio.create_task(api_watcher())
    
        async def api_watcher():
            while True:
                try:
                    # Check for changes
                    if await api_loader.check_for_changes():
                        # Wait for processing to complete if configured
                        if config.wait_for_processing_before_reload:
                            # TODO: Wait for queue to be empty
                            pass
                        
                        # Reload APIs
                        logger.info("Reloading APIs...")
                        new_apis = await api_loader.load_apis()
                        
                        # Update executor
                        api_executor.apis = new_apis
                        
                        # TODO: Update routes
                        logger.info("APIs reloaded")
                
                except Exception as e:
                    logger.error(f"API watcher error: {str(e)}")
                
                # Sleep before checking again
                if config.reload_on_api_dir_change:
                    await asyncio.sleep(config.reload_on_api_dir_change_interval_seconds)
                elif config.reload_on_api_file_change:
                    await asyncio.sleep(config.reload_on_api_file_change_interval_seconds)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await queue_manager.stop_workers()
    
    return app

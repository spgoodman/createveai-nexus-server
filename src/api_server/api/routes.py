"""API routes generation for FastAPI endpoints."""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.security import HTTPBearer
from ..models import APIError, APIErrorCode

class RouteGenerator:
    """Route generator for API endpoints."""
    
    def __init__(
        self, 
        app, 
        apis: Dict[str, Dict[str, Any]], 
        api_executor, 
        queue_manager, 
        security_manager, 
        openapi_generator, 
        logger: logging.Logger
    ):
        self.app = app
        self.apis = apis
        self.api_executor = api_executor
        self.queue_manager = queue_manager
        self.security_manager = security_manager
        self.openapi_generator = openapi_generator
        self.logger = logger
        self.security_scheme = HTTPBearer()
    
    def generate_routes(self):
        """Generate routes for all API endpoints."""
        # Create router
        api_router = APIRouter(
            prefix="/api",
            tags=["API"]
        )
        
        # Generate routes for APIs
        for api_path, api_info in self.apis.items():
            # Get queue mode
            queue_mode = api_info.get('queue_mode', False)
            
            # Add main route
            if queue_mode:
                self._add_queue_route(api_router, api_path, api_info)
            else:
                self._add_direct_route(api_router, api_path, api_info)
                
            # Add queue status route if in queue mode
            if queue_mode:
                self._add_queue_status_route(api_router, api_path, api_info)
        
        # Add OpenAPI route
        @api_router.get("/openapi.json", tags=["Documentation"])
        async def get_openapi():
            """Get OpenAPI schema."""
            return self.openapi_generator.generate_schema()
        
        # Include router in app
        self.app.include_router(api_router)
    
    def _add_direct_route(self, router, api_path: str, api_info: Dict[str, Any]):
        """Add direct route for API endpoint."""
        @router.post(f"/{api_path}", tags=[api_info.get('category', 'api')])
        async def direct_route(
            request: Request, 
            data: Dict[str, Any] = Body(...),
            auth = Depends(self.security_scheme)
        ):
            """Direct API endpoint."""
            try:
                # Validate API key
                api_key = self.security_manager.get_api_key_from_request(auth)
                
                # Execute API
                result = await self.api_executor.execute_api(api_path, data)
                return result
                
            except APIError as e:
                self.logger.error(f"API error: {e.message}")
                raise HTTPException(
                    status_code=e.code.value,
                    detail=e.to_response()
                )
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=APIError(
                        APIErrorCode.API_ERROR,
                        f"Unexpected error: {str(e)}"
                    ).to_response()
                )
    
    def _add_queue_route(self, router, api_path: str, api_info: Dict[str, Any]):
        """Add queue route for API endpoint."""
        @router.post(f"/{api_path}", tags=[api_info.get('category', 'api')])
        async def queue_route(
            request: Request, 
            data: Dict[str, Any] = Body(...),
            auth = Depends(self.security_scheme)
        ):
            """Queue API endpoint."""
            try:
                # Validate API key
                api_key = self.security_manager.get_api_key_from_request(auth)
                
                # Add to queue
                queue_id = await self.queue_manager.add_to_queue(api_key, api_path, data)
                return {"queue_id": queue_id}
                
            except APIError as e:
                self.logger.error(f"API error: {e.message}")
                raise HTTPException(
                    status_code=e.code.value,
                    detail=e.to_response()
                )
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=APIError(
                        APIErrorCode.API_ERROR,
                        f"Unexpected error: {str(e)}"
                    ).to_response()
                )
    
    def _add_queue_status_route(self, router, api_path: str, api_info: Dict[str, Any]):
        """Add queue status route for API endpoint."""
        @router.post(f"/{api_path}/queue", tags=[api_info.get('category', 'api')])
        async def queue_status_route(
            request: Request, 
            data: Dict[str, Any] = Body(...),
            auth = Depends(self.security_scheme)
        ):
            """Queue status endpoint."""
            try:
                # Validate API key
                api_key = self.security_manager.get_api_key_from_request(auth)
                
                # Check queue status
                if "queue_id" not in data:
                    raise APIError(
                        APIErrorCode.INVALID_INPUT,
                        "Missing queue_id"
                    )
                
                result = await self.queue_manager.get_queue_status(data["queue_id"], api_key)
                return result
                
            except APIError as e:
                self.logger.error(f"API error: {e.message}")
                raise HTTPException(
                    status_code=e.code.value,
                    detail=e.to_response()
                )
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=APIError(
                        APIErrorCode.API_ERROR,
                        f"Unexpected error: {str(e)}"
                    ).to_response()
                )

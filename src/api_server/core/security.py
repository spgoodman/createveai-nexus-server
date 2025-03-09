"""API Server security and authentication."""

from typing import Dict
import logging
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from ..models import APIError, APIErrorCode
from ..utils import ConfigManager

class SecurityManager:
    """Security manager for API authentication."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.api_keys = {key['key']: key.get('description', '') for key in config.api_keys}
        self.security_scheme = HTTPBearer()
    
    async def authenticate_request(self, request: Request, call_next):
        """Middleware for API key authentication."""
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json", "/favicon.ico")):
            # Skip authentication for documentation paths
            return await call_next(request)
        
        try:
            # Extract bearer token
            auth = await self.security_scheme(request)
            api_key = auth.credentials
            
            # Validate API key
            if api_key not in self.api_keys:
                raise APIError(
                    APIErrorCode.UNAUTHORIZED,
                    "Invalid API key"
                )
            
            # Continue with request
            return await call_next(request)
        except HTTPException:
            # Convert FastAPI exceptions to our format
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=APIError(
                    APIErrorCode.UNAUTHORIZED,
                    "Authentication required"
                ).to_response()
            )
        except APIError as e:
            # Handle API errors
            return JSONResponse(
                status_code=e.code.value,
                content=e.to_response()
            )
        except Exception as e:
            # Handle unexpected errors
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=APIError(
                    APIErrorCode.API_ERROR,
                    f"Authentication error: {str(e)}"
                ).to_response()
            )
    
    def get_api_key_from_request(self, auth: HTTPBearer) -> str:
        """Extract and validate API key from request."""
        api_key = auth.credentials
        if api_key not in self.api_keys:
            raise APIError(
                APIErrorCode.UNAUTHORIZED,
                "Invalid API key"
            )
        return api_key

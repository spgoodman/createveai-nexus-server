"""API Server error models."""

from enum import Enum
from typing import Dict, Any, Optional

class APIErrorCode(Enum):
    """API error codes mapped to HTTP status codes."""
    INVALID_INPUT = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    VALIDATION_ERROR = 422
    API_ERROR = 500
    TIMEOUT_ERROR = 504

class APIError(Exception):
    """Custom API error exception with error code and details."""
    
    def __init__(
        self, 
        code: APIErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        uri: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.uri = uri

    def to_response(self) -> dict:
        """Convert error to response dictionary."""
        return {
            "error": self.code.value,
            "description": self.message,
            "details": self.details,
            "uri": self.uri
        }

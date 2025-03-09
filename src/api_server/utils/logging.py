"""API Server logging utilities."""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from ..models import APIError
from .config import ConfigManager

class LoggingManager:
    """Logging manager for API Server."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logging system."""
        logger = logging.getLogger("api_server")
        
        # Set log level
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        log_level = level_map.get(self.config.log_level.lower(), logging.INFO)
        logger.setLevel(log_level)
        
        # Create formatters
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # Create handlers
        if self.config.log_enabled:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.config.log_file)
            os.makedirs(log_dir, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        if self.config.debug:
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def log_error(self, error: APIError, request_data: Optional[dict] = None, stack_trace: Optional[str] = None):
        """Log an API error with context."""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_code": error.code.value,
            "message": error.message,
            "uri": error.uri,
            "request_data": request_data,
            "stack_trace": stack_trace
        }
        
        self.logger.error(f"API Error: {json.dumps(error_data)}")

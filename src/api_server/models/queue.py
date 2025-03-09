"""API Server queue models."""

import time
from typing import Dict, Any, Optional

class QueueItem:
    """Queue item for long-running API requests."""
    
    def __init__(self, queue_id: str, api_key: str, endpoint: str, data: dict):
        self.queue_id = queue_id
        self.api_key = api_key
        self.endpoint = endpoint
        self.data = data
        self.status = "queued"  # queued, processing, completed, failed
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def to_dict(self) -> dict:
        """Convert queue item to dictionary for persistence."""
        return {
            "queue_id": self.queue_id,
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "data": self.data,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QueueItem':
        """Create queue item from dictionary."""
        item = cls(
            data["queue_id"],
            data["api_key"],
            data["endpoint"],
            data["data"]
        )
        item.status = data["status"]
        item.result = data["result"]
        item.error = data["error"]
        item.created_at = data["created_at"]
        item.updated_at = data["updated_at"]
        return item

"""API Server queue management."""

import os
import time
import json
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..models import APIError, APIErrorCode, QueueItem
from ..utils import ConfigManager

class QueueManager:
    """Queue manager for handling long-running API requests."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.queue: Dict[str, QueueItem] = {}
        self.processing_queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_queue_size)
        self.workers: List[asyncio.Task] = []
        self.temp_dir = Path(config.temp_dir)
        self.state_file = Path(config.state_file)
        
        # Create directories
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean up or restore state
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize queue state based on configuration."""
        if self.config.resume_on_startup and self.state_file.exists():
            self._load_state()
        elif self.config.clear_temp_on_startup_without_resume:
            self._clean_temp_dir()
    
    def _load_state(self):
        """Load queue state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
                
            for item_data in state_data.get("queue", []):
                item = QueueItem.from_dict(item_data)
                if item.status in ["queued", "processing"]:
                    # Requeue incomplete items
                    item.status = "queued"
                    item.updated_at = time.time()
                    self.queue[item.queue_id] = item
                    self.processing_queue.put_nowait(item.queue_id)
                else:
                    # Keep completed/failed items in queue for reference
                    self.queue[item.queue_id] = item
            
            self.logger.info(f"Loaded {len(self.queue)} items from state file")
        except Exception as e:
            self.logger.error(f"Failed to load state: {str(e)}")
            self._clean_temp_dir()
    
    def _save_state(self):
        """Save queue state to file."""
        try:
            state_data = {
                "queue": [item.to_dict() for item in self.queue.values()]
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")
    
    def _clean_temp_dir(self):
        """Clean temporary directory."""
        try:
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            
            self.logger.info("Cleaned temporary directory")
        except Exception as e:
            self.logger.error(f"Failed to clean temporary directory: {str(e)}")
    
    async def start_workers(self, api_executor):
        """Start worker tasks for processing queue."""
        self.api_executor = api_executor
        
        for _ in range(self.config.max_threads):
            worker = asyncio.create_task(self._worker_task())
            self.workers.append(worker)
        
        self.logger.info(f"Started {len(self.workers)} worker tasks")
    
    async def _worker_task(self):
        """Worker task for processing queue items."""
        while True:
            try:
                # Get queue item ID
                queue_id = await self.processing_queue.get()
                
                # Get queue item
                item = self.queue.get(queue_id)
                if not item:
                    self.logger.warning(f"Queue item {queue_id} not found")
                    self.processing_queue.task_done()
                    continue
                
                # Update status
                item.status = "processing"
                item.updated_at = time.time()
                self._save_state()
                
                # Process item
                try:
                    result = await self.api_executor.execute_api(
                        item.endpoint,
                        item.data
                    )
                    
                    # Update item with result
                    item.status = "completed"
                    item.result = result
                    item.updated_at = time.time()
                    
                except Exception as e:
                    # Update item with error
                    item.status = "failed"
                    if isinstance(e, APIError):
                        item.error = e.to_response()
                    else:
                        item.error = {
                            "error": 500,
                            "description": f"Processing error: {str(e)}"
                        }
                    item.updated_at = time.time()
                
                # Save state
                self._save_state()
                
                # Clean up temp files if configured
                if self.config.clear_temp_files_after_processing:
                    # TODO: Implement temp file cleanup for this item
                    pass
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker error: {str(e)}")
    
    async def add_to_queue(self, api_key: str, endpoint: str, data: dict) -> str:
        """Add item to processing queue."""
        # Check queue size
        if self.processing_queue.qsize() >= self.config.max_queue_size:
            raise APIError(
                APIErrorCode.API_ERROR,
                "Queue is full"
            )
        
        # Create queue item
        import uuid
        queue_id = str(uuid.uuid4())
        item = QueueItem(queue_id, api_key, endpoint, data)
        
        # Add to queue
        self.queue[queue_id] = item
        await self.processing_queue.put(queue_id)
        
        # Save state
        self._save_state()
        
        return queue_id
    
    async def get_queue_status(self, queue_id: str, api_key: str) -> dict:
        """Get status of queue item."""
        # Get queue item
        item = self.queue.get(queue_id)
        if not item:
            raise APIError(
                APIErrorCode.NOT_FOUND,
                f"Queue item {queue_id} not found"
            )
        
        # Check API key
        if item.api_key != api_key:
            raise APIError(
                APIErrorCode.UNAUTHORIZED,
                "Not authorized to access this queue item"
            )
        
        # Return status
        if item.status == "completed":
            return item.result
        elif item.status == "failed":
            return item.error
        else:
            return {"queue_id": queue_id}
    
    async def stop_workers(self):
        """Stop worker tasks."""
        for worker in self.workers:
            worker.cancel()
        
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers = []
        
        self.logger.info("Stopped worker tasks")

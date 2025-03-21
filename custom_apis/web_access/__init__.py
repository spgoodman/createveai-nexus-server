"""Web access module for the Createve.AI API Server.

This module provides API endpoints for retrieving web page information and
performing web actions with session persistence and dynamic content support.

Features:
- Web page information retrieval (with link extraction)
- Dynamic page content loading via Selenium
- Multi-step action execution
- Session state management
- Screenshots and state capture
"""

from .api import WebInfoRetriever, WebActionPerformer, ActionSequenceManager

# Map class names to class objects
NODE_CLASS_MAPPINGS = {
    "webInfoRetriever": WebInfoRetriever,
    "webActionPerformer": WebActionPerformer,
    "actionSequenceManager": ActionSequenceManager
}

# Map class names to display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "webInfoRetriever": "Web Info Retriever",
    "webActionPerformer": "Web Action Performer",
    "actionSequenceManager": "Action Sequence Manager"
}

# Set queue mode for endpoints
API_SERVER_QUEUE_MODE = {
    WebInfoRetriever: True,  # Queue mode for potentially slow operations
    WebActionPerformer: True,  # Queue mode for web automation
    ActionSequenceManager: True  # Queue mode for sequence operations
}

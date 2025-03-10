"""
Reddit API using PRAW integration for Createve.AI API Server.

This module provides comprehensive access to Reddit's functionality through PRAW,
allowing read and write operations such as retrieving posts, creating content,
and managing subreddit subscriptions.
"""

from .api import (
    SubredditReader,
    PostViewer, 
    UserProfileViewer,
    PostCreator,
    InteractionManager,
    CommentMonitor,
    SubredditManager,
    BatchSubredditManager,
    SubredditAnalyzerAPI
)

# Map display names to class objects
# Keys follow convention: remove spaces and set first character to lowercase
NODE_CLASS_MAPPINGS = {
    "subredditReader": SubredditReader,
    "postViewer": PostViewer,
    "userProfileViewer": UserProfileViewer,
    "postCreator": PostCreator,
    "interactionManager": InteractionManager,
    "commentMonitor": CommentMonitor,
    "subredditManager": SubredditManager,
    "batchSubredditManager": BatchSubredditManager,
    "subredditAnalyzer": SubredditAnalyzerAPI
}

# Map class names to human-readable display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "subredditReader": "Subreddit Reader",
    "postViewer": "Post Viewer",
    "userProfileViewer": "User Profile Viewer",
    "postCreator": "Post Creator",
    "interactionManager": "Interaction Manager",
    "commentMonitor": "Comment Monitor",
    "subredditManager": "Subreddit Manager",
    "batchSubredditManager": "Batch Subreddit Manager",
    "subredditAnalyzer": "Subreddit Analyzer"
}

# Define which APIs run in queue mode based on expected execution time
API_SERVER_QUEUE_MODE = {
    SubredditReader: False,  # Fast read operations
    PostViewer: False,       # Fast read operations
    UserProfileViewer: False, # Fast read operations
    PostCreator: True,       # Content creation - potentially slow, depends on Reddit API
    InteractionManager: True, # Interactions - potentially slow, depends on Reddit API
    CommentMonitor: False,    # Fast read operations
    SubredditManager: True,   # Subscription management - depends on Reddit API
    BatchSubredditManager: True, # Batch operations - potentially slow
    SubredditAnalyzerAPI: True   # Deep analysis can be slow, especially at "deep" analysis_depth
}

# Export classes for the API server
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "API_SERVER_QUEUE_MODE",
]

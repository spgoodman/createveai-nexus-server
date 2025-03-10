"""
LinkedIn API module for the Createve.AI API Server.

This module provides access to LinkedIn functionality including profile retrieval,
people search, job search, messaging, company information, connection management,
conversation retrieval, and profile view tracking.
"""

from .api import (
    LinkedInProfileFetcher, 
    LinkedInPeopleSearch,
    LinkedInJobSearch,
    LinkedInMessaging,
    LinkedInCompanyInfo,
    LinkedInConnectionManager,
    LinkedInConversationFetcher,
    LinkedInProfileViewTracker
)

# Map display names to class objects
NODE_CLASS_MAPPINGS = {
    "LinkedIn Profile Fetcher": LinkedInProfileFetcher,
    "LinkedIn People Search": LinkedInPeopleSearch,
    "LinkedIn Job Search": LinkedInJobSearch,
    "LinkedIn Messaging": LinkedInMessaging,
    "LinkedIn Company Info": LinkedInCompanyInfo,
    "LinkedIn Connection Manager": LinkedInConnectionManager,
    "LinkedIn Conversation Fetcher": LinkedInConversationFetcher,
    "LinkedIn Profile View Tracker": LinkedInProfileViewTracker
}

# Map class names to human-readable display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "LinkedIn Profile Fetcher": "LinkedIn Profile Fetcher",
    "LinkedIn People Search": "LinkedIn People Search",
    "LinkedIn Job Search": "LinkedIn Job Search",
    "LinkedIn Messaging": "LinkedIn Messaging",
    "LinkedIn Company Info": "LinkedIn Company Info",
    "LinkedIn Connection Manager": "LinkedIn Connection Manager",
    "LinkedIn Conversation Fetcher": "LinkedIn Conversation Fetcher",
    "LinkedIn Profile View Tracker": "LinkedIn Profile View Tracker"
}

# Define processing mode for each endpoint
API_SERVER_QUEUE_MODE = {
    LinkedInProfileFetcher: False,      # Direct mode
    LinkedInPeopleSearch: True,         # Queue mode (may take time)
    LinkedInJobSearch: True,            # Queue mode (may take time)
    LinkedInMessaging: False,           # Direct mode
    LinkedInCompanyInfo: False,         # Direct mode
    LinkedInConnectionManager: False,   # Direct mode
    LinkedInConversationFetcher: True,  # Queue mode (may take time)
    LinkedInProfileViewTracker: False   # Direct mode
}

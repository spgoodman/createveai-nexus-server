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
    "linkedInProfileFetcher": LinkedInProfileFetcher,
    "linkedInPeopleSearch": LinkedInPeopleSearch,
    "linkedInJobSearch": LinkedInJobSearch,
    "linkedInMessaging": LinkedInMessaging,
    "linkedInCompanyInfo": LinkedInCompanyInfo,
    "linkedInConnectionManager": LinkedInConnectionManager,
    "linkedInConversationFetcher": LinkedInConversationFetcher,
    "linkedInProfileViewTracker": LinkedInProfileViewTracker
}

# Map class names to human-readable display names
NODE_DISPLAY_NAME_MAPPINGS = {
    "linkedInProfileFetcher": "LinkedIn Profile Fetcher",
    "linkedInPeopleSearch": "LinkedIn People Search",
    "linkedInJobSearch": "LinkedIn Job Search",
    "linkedInMessaging": "LinkedIn Messaging",
    "linkedInCompanyInfo": "LinkedIn Company Info",
    "linkedInConnectionManager": "LinkedIn Connection Manager",
    "linkedInConversationFetcher": "LinkedIn Conversation Fetcher",
    "linkedInProfileViewTracker": "LinkedIn Profile View Tracker"
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

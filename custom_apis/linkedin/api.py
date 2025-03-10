"""
LinkedIn API implementation for the Createve.AI API Server.

This module implements various LinkedIn API functionality using the unofficial linkedin-api package.
"""

import os
import json
import time
import traceback
from typing import Dict, List, Optional, Tuple, Union

from linkedin_api import Linkedin
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta

# Load environment variables (for API credentials)
load_dotenv()

class LinkedInClientManager:
    """Singleton manager for LinkedIn API client."""
    
    _instance = None
    _client = None
    
    @classmethod
    def get_client(cls, email=None, password=None):
        """Get or create a LinkedIn client instance."""
        if cls._client is None:
            # Try environment variables if not provided directly
            email = email or os.getenv("LINKEDIN_EMAIL")
            password = password or os.getenv("LINKEDIN_PASSWORD")
            
            if not email or not password:
                raise ValueError(
                    "LinkedIn credentials not provided. Please set LINKEDIN_EMAIL and "
                    "LINKEDIN_PASSWORD environment variables or provide them as parameters."
                )
            
            cls._client = Linkedin(email, password)
        
        return cls._client


class LinkedInProfileFetcher:
    """
    Fetches comprehensive LinkedIn profile information.
    
    Retrieves detailed profile data including work experience, education, 
    skills, and contact information.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for the profile fetcher."""
        return {
            "required": {
                "profile_identifier": ("STRING", {
                    "multiline": False, 
                    "placeholder": "Username or URN ID (e.g., 'john-doe' or 'urn:li:fs_miniProfile:AbC123')"
                }),
            },
            "optional": {
                "include_contact_info": ("BOOLEAN", {"default": False}),
                "include_skills": ("BOOLEAN", {"default": True}),
                "use_urn": ("BOOLEAN", {"default": False}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("profile_data",)
    FUNCTION = "fetch_profile"
    
    def fetch_profile(
        self, 
        profile_identifier: str,
        include_contact_info: bool = False,
        include_skills: bool = True,
        use_urn: bool = False,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Fetch a LinkedIn profile using either a public ID or URN ID.
        
        Args:
            profile_identifier: Username (from URL) or URN ID of the profile
            include_contact_info: Whether to fetch contact information
            include_skills: Whether to fetch skills information
            use_urn: Whether the profile_identifier is a URN instead of username
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing profile information
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Determine how to fetch the profile
            if use_urn:
                profile = client.get_profile(urn_id=profile_identifier)
            else:
                profile = client.get_profile(public_id=profile_identifier)
            
            # Get additional information if requested
            if include_contact_info:
                try:
                    contact_info = client.get_profile_contact_info(
                        profile_identifier if use_urn else profile_identifier
                    )
                    profile['contact_info'] = contact_info
                except Exception as e:
                    profile['contact_info'] = {"error": str(e)}
            
            if include_skills:
                try:
                    skills = client.get_profile_skills(
                        profile_identifier if use_urn else profile_identifier
                    )
                    profile['skills'] = skills
                except Exception as e:
                    profile['skills'] = {"error": str(e)}
            
            # Add metadata
            profile['_metadata'] = {
                'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'linkedin-api'
            }
            
            return (profile,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInPeopleSearch:
    """
    Searches for people on LinkedIn based on various criteria.
    
    Provides comprehensive people search functionality with filters for keywords,
    companies, locations, and more.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for people search."""
        return {
            "required": {
                "keywords": ("STRING", {
                    "multiline": False,
                    "placeholder": "Search keywords (e.g., 'Software Engineer')"
                }),
            },
            "optional": {
                "location": ("STRING", {"multiline": False, "default": ""}),
                "company_name": ("STRING", {"multiline": False, "default": ""}),
                "school_name": ("STRING", {"multiline": False, "default": ""}),
                "network_depth": (["All", "1st", "2nd", "3rd"], {"default": "All"}),
                "max_results": ("INTEGER", {"default": 10, "min": 1, "max": 100}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("search_results",)
    FUNCTION = "search_people"
    
    def search_people(
        self,
        keywords: str,
        location: str = "",
        company_name: str = "",
        school_name: str = "",
        network_depth: str = "All",
        max_results: int = 10,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Search for people on LinkedIn based on provided criteria.
        
        Args:
            keywords: Search keywords or phrases
            location: Location filter
            company_name: Company name filter
            school_name: School name filter
            network_depth: Connection level (All, 1st, 2nd, 3rd)
            max_results: Maximum number of results to return
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Prepare search parameters
            search_params = {}
            
            if keywords:
                search_params["keywords"] = keywords
                
            if company_name:
                search_params["keyword_company"] = company_name
                
            if location:
                search_params["keyword_location"] = location
                
            if school_name:
                search_params["keyword_school"] = school_name
            
            # Map network depth
            network_map = {
                "1st": ["F"],
                "2nd": ["S"],
                "3rd": ["O"],
                "All": ["F", "S", "O"]
            }
            if network_depth in network_map:
                search_params["network_depths"] = network_map[network_depth]
            
            # Execute search
            results = client.search_people(**search_params)
            
            # Limit results
            results = results[:max_results]
            
            # Get full profiles for the results
            enriched_results = []
            for result in results:
                public_id = result.get('public_id')
                if public_id:
                    try:
                        profile = client.get_profile(public_id=public_id)
                        enriched_results.append(profile)
                    except Exception as e:
                        # If we can't get the full profile, include the basic one
                        result['profile_error'] = str(e)
                        enriched_results.append(result)
                else:
                    enriched_results.append(result)
            
            response = {
                'count': len(enriched_results),
                'results': enriched_results,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api',
                    'search_criteria': {
                        'keywords': keywords,
                        'location': location,
                        'company_name': company_name,
                        'school_name': school_name,
                        'network_depth': network_depth
                    }
                }
            }
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInJobSearch:
    """
    Searches for job listings on LinkedIn based on various criteria.
    
    Provides comprehensive job search functionality with filters for keywords,
    location, experience level, and job types.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for job search."""
        return {
            "required": {
                "keywords": ("STRING", {
                    "multiline": False,
                    "placeholder": "Job search keywords (e.g., 'Data Scientist')"
                }),
            },
            "optional": {
                "location": ("STRING", {"multiline": False, "default": ""}),
                "experience_levels": (["All", "Internship", "Entry level", "Associate", "Mid-Senior", "Director", "Executive"], {"default": "All"}),
                "job_types": (["All", "Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Internship"], {"default": "All"}),
                "remote_options": (["All", "On-site", "Remote", "Hybrid"], {"default": "All"}),
                "max_results": ("INTEGER", {"default": 10, "min": 1, "max": 100}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("job_results",)
    FUNCTION = "search_jobs"
    
    def search_jobs(
        self,
        keywords: str,
        location: str = "",
        experience_levels: str = "All",
        job_types: str = "All",
        remote_options: str = "All",
        max_results: int = 10,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Search for jobs on LinkedIn based on provided criteria.
        
        Args:
            keywords: Search keywords or phrases
            location: Location filter
            experience_levels: Experience level filter
            job_types: Job type filter
            remote_options: Remote work options filter
            max_results: Maximum number of results to return
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing job search results
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Prepare search parameters
            search_params = {}
            
            if keywords:
                search_params["keywords"] = keywords
                
            if location:
                search_params["location_name"] = location
            
            # Map experience levels
            experience_map = {
                "Internship": ["1"],
                "Entry level": ["2"],
                "Associate": ["3"],
                "Mid-Senior": ["4"],
                "Director": ["5"],
                "Executive": ["6"]
            }
            if experience_levels != "All":
                search_params["experience"] = experience_map.get(experience_levels, [])
            
            # Map job types
            job_type_map = {
                "Full-time": ["F"],
                "Part-time": ["P"],
                "Contract": ["C"],
                "Temporary": ["T"],
                "Volunteer": ["V"],
                "Internship": ["I"]
            }
            if job_types != "All":
                search_params["job_type"] = job_type_map.get(job_types, [])
            
            # Map remote options
            remote_map = {
                "On-site": ["1"],
                "Remote": ["2"],
                "Hybrid": ["3"]
            }
            if remote_options != "All":
                search_params["remote"] = remote_map.get(remote_options, [])
            
            # Execute search
            results = client.search_jobs(**search_params)
            
            # Limit results
            results = results[:max_results]
            
            # Get full job details for each result
            enriched_results = []
            for job in results:
                job_id = job.get('entityUrn', '').split(':')[-1]
                if job_id:
                    try:
                        details = client.get_job(job_id)
                        # Get skills if available
                        try:
                            skills = client.get_job_skills(job_id)
                            details['skills'] = skills
                        except:
                            pass
                        enriched_results.append(details)
                    except Exception as e:
                        # If we can't get the full details, include the basic one
                        job['details_error'] = str(e)
                        enriched_results.append(job)
                else:
                    enriched_results.append(job)
            
            response = {
                'count': len(enriched_results),
                'results': enriched_results,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api',
                    'search_criteria': {
                        'keywords': keywords,
                        'location': location,
                        'experience_levels': experience_levels,
                        'job_types': job_types,
                        'remote_options': remote_options
                    }
                }
            }
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInMessaging:
    """
    Sends messages to LinkedIn connections.
    
    Enables sending messages to existing conversations or starting new ones.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for messaging."""
        return {
            "required": {
                "message_body": ("STRING", {
                    "multiline": True,
                    "placeholder": "Your message text here..."
                }),
            },
            "optional": {
                "conversation_urn_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Conversation URN ID for existing conversations"
                }),
                "recipient_profile_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Public ID of recipient (for new conversations)"
                }),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("message_result",)
    FUNCTION = "send_message"
    
    def send_message(
        self,
        message_body: str,
        conversation_urn_id: Optional[str] = None,
        recipient_profile_id: Optional[str] = None,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Send a message on LinkedIn.
        
        Args:
            message_body: Text content of the message
            conversation_urn_id: ID for existing conversations
            recipient_profile_id: Public ID for new conversations
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing message status
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Validate inputs
            if not conversation_urn_id and not recipient_profile_id:
                raise ValueError(
                    "Either conversation_urn_id or recipient_profile_id must be provided"
                )
            
            # Prepare parameters
            params = {
                "message_body": message_body
            }
            
            # Determine if we're messaging an existing conversation or creating a new one
            if conversation_urn_id:
                params["conversation_urn_id"] = conversation_urn_id
                message_type = "existing_conversation"
            else:
                # First get the profile to get the URN
                profile = client.get_profile(public_id=recipient_profile_id)
                
                if not profile:
                    raise ValueError(f"Could not find profile with ID: {recipient_profile_id}")
                
                # Get the entity URN from the profile
                urn = profile.get('entityUrn')
                if not urn:
                    raise ValueError("Could not find URN for the specified profile")
                
                params["recipients"] = [urn]
                message_type = "new_conversation"
            
            # Send the message
            success = client.send_message(**params)
            
            # API returns True on failure, False on success (counterintuitive)
            is_success = not success
            
            response = {
                'success': is_success,
                'message_type': message_type,
                'recipient': recipient_profile_id or conversation_urn_id,
                '_metadata': {
                    'sent_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInCompanyInfo:
    """
    Retrieves comprehensive information about companies on LinkedIn.
    
    Fetches company profiles including details, updates, and statistics.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for company info retrieval."""
        return {
            "required": {
                "company_identifier": ("STRING", {
                    "multiline": False,
                    "placeholder": "Company name or ID (e.g., 'google')"
                }),
            },
            "optional": {
                "include_updates": ("BOOLEAN", {"default": False}),
                "max_updates": ("INTEGER", {"default": 5, "min": 1, "max": 50}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("company_data",)
    FUNCTION = "get_company"
    
    def get_company(
        self,
        company_identifier: str,
        include_updates: bool = False,
        max_updates: int = 5,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Fetch information about a LinkedIn company.
        
        Args:
            company_identifier: Company name or ID
            include_updates: Whether to include company updates
            max_updates: Maximum number of updates to include
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing company information
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Get company data
            company = client.get_company(company_identifier)
            
            # Get company updates if requested
            if include_updates:
                try:
                    updates = client.get_company_updates(
                        public_id=company_identifier,
                        max_results=max_updates
                    )
                    company['updates'] = updates
                except Exception as e:
                    company['updates'] = {"error": str(e)}
            
            # Add metadata
            company['_metadata'] = {
                'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'linkedin-api'
            }
            
            return (company,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInConnectionManager:
    """
    Manages LinkedIn connections.
    
    Enables sending connection requests, accepting/declining invitations,
    and managing connection status.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for connection management."""
        return {
            "required": {
                "action_type": (["add_connection", "get_pending_invitations"], {
                    "default": "add_connection"
                }),
                "profile_identifier": ("STRING", {
                    "multiline": False,
                    "placeholder": "Username or URN ID (e.g., 'john-doe' or 'urn:li:fs_miniProfile:AbC123')"
                }),
            },
            "optional": {
                "message": ("STRING", {
                    "multiline": True,
                    "default": "I'd like to connect with you on LinkedIn.",
                    "placeholder": "Custom message for connection request..."
                }),
                "use_urn": ("BOOLEAN", {"default": False}),
                "track_status": ("BOOLEAN", {"default": False}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("connection_result",)
    FUNCTION = "manage_connection"
    
    def manage_connection(
        self,
        action_type: str,
        profile_identifier: str,
        message: str = "I'd like to connect with you on LinkedIn.",
        use_urn: bool = False,
        track_status: bool = False,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Manage LinkedIn connections.
        
        Args:
            action_type: The type of action to perform
            profile_identifier: Username or URN ID of the profile
            message: Custom message for connection request
            use_urn: Whether the profile_identifier is a URN instead of username
            track_status: Whether to track the status of the request
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing operation result
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Prepare response
            response = {
                'action_type': action_type,
                'profile_identifier': profile_identifier,
                'success': False,
                '_metadata': {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            
            # Handle different actions
            if action_type == "add_connection":
                # Determine if we're using a public ID or URN
                if use_urn:
                    # For URN, we can use it directly
                    profile_urn = profile_identifier
                else:
                    # For public ID, we need to get the profile first to get the URN
                    profile = client.get_profile(public_id=profile_identifier)
                    if not profile:
                        raise ValueError(f"Could not find profile with ID: {profile_identifier}")
                    
                    profile_urn = profile.get('entityUrn')
                    if not profile_urn:
                        raise ValueError("Could not find URN for the specified profile")
                
                # Send the connection request
                result = client.add_connection(profile_urn, message=message)
                
                # Store request details if tracking is enabled
                if track_status:
                    request_id = f"conn-{uuid.uuid4()}"
                    response['request_id'] = request_id
                    # In a real implementation, you might store this in a database
                
                response['success'] = result
                response['message_sent'] = message if result else None
                
            elif action_type == "get_pending_invitations":
                # Get pending connection invitations
                invitations = client.get_invitations()
                response['invitations'] = invitations
                response['count'] = len(invitations)
                response['success'] = True
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'action_type': action_type,
                'profile_identifier': profile_identifier,
                '_metadata': {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInConversationFetcher:
    """
    Retrieves LinkedIn messages and conversations.
    
    Fetches message threads, individual messages, and conversation history.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for conversation fetching."""
        return {
            "required": {
                "fetch_type": (["all_conversations", "conversation_details"], {
                    "default": "all_conversations"
                }),
            },
            "optional": {
                "conversation_urn_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Conversation URN ID (required for conversation_details)"
                }),
                "max_conversations": ("INTEGER", {"default": 10, "min": 1, "max": 100}),
                "include_message_body": ("BOOLEAN", {"default": True}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("conversation_data",)
    FUNCTION = "fetch_conversations"
    
    def fetch_conversations(
        self,
        fetch_type: str,
        conversation_urn_id: Optional[str] = None,
        max_conversations: int = 10,
        include_message_body: bool = True,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Fetch LinkedIn conversations and messages.
        
        Args:
            fetch_type: Type of fetch operation to perform
            conversation_urn_id: URN ID of specific conversation (for conversation_details)
            max_conversations: Maximum number of conversations to return
            include_message_body: Whether to include message content
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing conversation data
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Prepare response
            response = {
                'fetch_type': fetch_type,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            
            # Handle different fetch types
            if fetch_type == "all_conversations":
                # Get list of all conversations
                conversations = client.get_conversations()
                
                # Limit to max requested
                conversations = conversations[:max_conversations]
                
                # Include message body if requested
                if include_message_body:
                    for conversation in conversations:
                        conversation_id = conversation.get('entityUrn', '').split(':')[-1]
                        if conversation_id:
                            try:
                                messages = client.get_conversation(conversation_id)
                                conversation['messages'] = messages
                            except Exception as e:
                                conversation['messages'] = {"error": str(e)}
                
                response['conversations'] = conversations
                response['count'] = len(conversations)
                
            elif fetch_type == "conversation_details":
                # Validate input
                if not conversation_urn_id:
                    raise ValueError("conversation_urn_id is required for conversation_details")
                
                # Get conversation details
                conversation_id = conversation_urn_id.split(':')[-1] if ':' in conversation_urn_id else conversation_urn_id
                messages = client.get_conversation(conversation_id)
                
                response['conversation_id'] = conversation_id
                response['messages'] = messages
                response['count'] = len(messages) if isinstance(messages, list) else 0
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'fetch_type': fetch_type,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)


class LinkedInProfileViewTracker:
    """
    Tracks and analyzes LinkedIn profile views.
    
    Retrieves information about who viewed your profile and provides analytics.
    """
    
    CATEGORY = "linkedin"
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for profile view tracking."""
        return {
            "required": {
                "track_type": (["viewers", "analytics", "visit_profile"], {
                    "default": "viewers"
                }),
            },
            "optional": {
                "target_profile_id": ("STRING", {
                    "multiline": False,
                    "placeholder": "Username of profile to visit (for visit_profile)"
                }),
                "time_range": (["day", "week", "month"], {"default": "week"}),
                "max_results": ("INTEGER", {"default": 20, "min": 1, "max": 100}),
                "linkedin_email": ("STRING", {"multiline": False}),
                "linkedin_password": ("STRING", {"multiline": False}),
            }
        }
    
    RETURN_TYPES = ("DICT",)
    RETURN_NAMES = ("tracking_data",)
    FUNCTION = "track_profile_views"
    
    def track_profile_views(
        self,
        track_type: str,
        target_profile_id: Optional[str] = None,
        time_range: str = "week",
        max_results: int = 20,
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ) -> Tuple[Dict]:
        """
        Track and analyze LinkedIn profile views.
        
        Args:
            track_type: Type of tracking operation to perform
            target_profile_id: Profile ID to visit (for visit_profile)
            time_range: Time range for analytics (day, week, month)
            max_results: Maximum number of results to return
            linkedin_email: Optional email for LinkedIn login
            linkedin_password: Optional password for LinkedIn login
            
        Returns:
            Dictionary containing tracking data
        """
        try:
            # Get client
            client = LinkedInClientManager.get_client(linkedin_email, linkedin_password)
            
            # Prepare response
            response = {
                'track_type': track_type,
                'time_range': time_range,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            
            # Handle different tracking types
            if track_type == "viewers":
                # Get profile viewers
                viewers = client.get_profile_views()
                
                # Limit to max requested
                viewers = viewers[:max_results] if isinstance(viewers, list) else viewers
                
                # Enrich viewer profiles with additional info
                if isinstance(viewers, list):
                    enriched_viewers = []
                    for viewer in viewers:
                        public_id = viewer.get('publicIdentifier')
                        if public_id:
                            try:
                                profile = client.get_profile(public_id=public_id)
                                viewer['profile'] = profile
                                enriched_viewers.append(viewer)
                            except Exception as e:
                                viewer['profile_error'] = str(e)
                                enriched_viewers.append(viewer)
                        else:
                            enriched_viewers.append(viewer)
                    
                    viewers = enriched_viewers
                
                response['viewers'] = viewers
                response['count'] = len(viewers) if isinstance(viewers, list) else 0
                
            elif track_type == "analytics":
                # Get profile view analytics (in a real implementation, this might
                # involve aggregating and analyzing the raw viewer data)
                
                # Calculate time period for analytics
                if time_range == "day":
                    period = timedelta(days=1)
                elif time_range == "month":
                    period = timedelta(days=30)
                else:  # week
                    period = timedelta(days=7)
                
                start_date = datetime.now() - period
                
                # In this implementation, we'll simulate analytics with some detailed metrics
                # In a real implementation, you would use client.get_profile_views() and analyze the data
                analytics = {
                    'total_views': 0,  # Would be calculated from actual data
                    'unique_viewers': 0,  # Would be calculated from actual data
                    'view_trends': {
                        'daily': [],  # Would contain daily view counts
                        'by_industry': {},  # Would contain views broken down by viewer industry
                        'by_company': {},  # Would contain views broken down by viewer company
                    },
                    'engagement_metrics': {
                        'connection_requests': 0,
                        'message_responses': 0,
                        'content_engagement': 0,
                    },
                    'period': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': datetime.now().strftime('%Y-%m-%d'),
                        'range': time_range
                    }
                }
                
                response['analytics'] = analytics
                
            elif track_type == "visit_profile":
                # Validate input
                if not target_profile_id:
                    raise ValueError("target_profile_id is required for visit_profile")
                
                # Visit the profile to register a view
                # Note: The LinkedIn API doesn't have a direct "visit profile" method
                # But getting a profile simulates visiting it
                profile = client.get_profile(public_id=target_profile_id)
                
                response['visited_profile'] = {
                    'profile_id': target_profile_id,
                    'success': bool(profile),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            return (response,)
            
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'track_type': track_type,
                '_metadata': {
                    'retrieved_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'linkedin-api'
                }
            }
            return (error_details,)

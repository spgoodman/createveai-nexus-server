# LinkedIn API Module for Createve.AI

This module provides a comprehensive set of tools for interacting with LinkedIn through the Createve.AI API Server. It allows you to fetch profiles, search for people and jobs, send messages, retrieve company information, manage connections, access conversations, and track profile views.

## Features

The module provides the following API endpoints:

### LinkedIn Profile Fetcher
- Fetches detailed LinkedIn profile information 
- Includes work experience, education, and skills
- Optional contact information retrieval
- Supports both public ID and URN ID for profile identification

### LinkedIn People Search
- Searches for people based on keywords, location, company, and school
- Filters by connection level (1st, 2nd, 3rd)
- Returns enriched profile information for each result
- Configurable result limit

### LinkedIn Job Search  
- Searches for job listings with comprehensive filtering options
- Filters by experience level, job type, and remote work options
- Retrieves detailed job information including required skills
- Configurable result limit

### LinkedIn Messaging
- Sends messages to LinkedIn connections
- Supports both existing conversations and starting new ones  
- Requires either a conversation URN ID or recipient profile ID

### LinkedIn Company Info
- Retrieves comprehensive company information
- Optional inclusion of company updates
- Configurable number of updates to include

### LinkedIn Connection Manager
- Sends connection requests to other LinkedIn users
- Retrieves pending connection invitations
- Supports custom connection request messages
- Option to track connection request status

### LinkedIn Conversation Fetcher
- Retrieves all conversations or specific conversation details
- Fetches message content and conversation metadata
- Configurable limit on number of conversations
- Option to include or exclude message body content

### LinkedIn Profile View Tracker
- Tracks who has viewed your LinkedIn profile
- Provides analytics on profile views over different time periods
- Simulates profile visits to other users
- Enriches viewer profiles with additional information

## Setup

1. Install the required dependencies:
```bash
pip install -r custom_apis/linkedin/requirements.txt
```

2. Configure LinkedIn credentials:
Either:
- Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` environment variables
- Provide credentials directly as parameters to each API endpoint

## Usage Examples

### Fetching a Profile

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInProfileFetcher",
    headers=headers, 
    json={
        "profile_identifier": "john-doe",
        "include_contact_info": True,
        "include_skills": True
    }
)
profile_data = response.json()

# Using the MCP tool 
result = claude.use_mcp_tool(
    server_name="createveai-nexus-server",
    tool_name="LinkedIn Profile Fetcher",
    arguments={
        "profile_identifier": "john-doe", 
        "include_contact_info": True,
        "include_skills": True
    }
)
```

### Searching for People

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInPeopleSearch",
    headers=headers,
    json={
        "keywords": "Software Engineer",
        "location": "San Francisco",
        "company_name": "Google", 
        "network_depth": "All",
        "max_results": 10
    }
)
search_results = response.json()
```

### Searching for Jobs

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInJobSearch",
    headers=headers,
    json={
        "keywords": "Data Scientist",
        "location": "London",
        "experience_levels": "Mid-Senior",
        "job_types": "Full-time",
        "remote_options": "Remote",
        "max_results": 20
    }
)
job_results = response.json()
```

### Sending a Message

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInMessaging",
    headers=headers,
    json={
        "message_body": "Hi! Thanks for connecting. I'd love to learn more about your work.",
        "recipient_profile_id": "john-doe"
    }
)
message_result = response.json()
```

### Getting Company Information

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInCompanyInfo",
    headers=headers,
    json={
        "company_identifier": "google",
        "include_updates": True,
        "max_updates": 10
    }
)
company_data = response.json()
```

### Adding a Connection

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInConnectionManager", 
    headers=headers,
    json={
        "action_type": "add_connection",
        "profile_identifier": "jane-doe",
        "message": "I'd like to connect with you after seeing your work on AI research."
    }
)
connection_result = response.json()
```

### Fetching Conversations

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInConversationFetcher",
    headers=headers,
    json={
        "fetch_type": "all_conversations",
        "max_conversations": 5,
        "include_message_body": True
    }
)
conversation_data = response.json()
```

### Tracking Profile Views

```python
# Using the REST API
response = requests.post(
    "http://localhost:43080/api/linkedin/linkedInProfileViewTracker",
    headers=headers,
    json={
        "track_type": "viewers",
        "time_range": "week",
        "max_results": 10
    }
)
tracking_data = response.json()
```

## Important Notes

1. This module uses the unofficial [linkedin-api](https://github.com/tomquirk/linkedin-api) Python package
2. LinkedIn credentials are required to use any of the API endpoints
3. Long-running operations like people search and job search use queue mode
4. Rate limits and other restrictions from LinkedIn apply
5. Always use this API responsibly and in accordance with LinkedIn's terms of service

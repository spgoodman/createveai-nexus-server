# Createve.AI API Server Architecture

This document provides an overview of the architecture of the Createve.AI API Server.

## Overall Architecture

The Createve.AI API Server is designed as a modular FastAPI application that dynamically loads and serves Python modules as REST API endpoints. It follows a service-oriented architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                          │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ API Loader  │    │ API Executor│    │ Queue       │              │
│  │             │───▶│             │───▶│ Manager     │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│         │                  ▲                   │                    │
│         │                  │                   │                    │
│         ▼                  │                   ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ Compatibility│   │ Type        │    │ State       │              │
│  │ Checker     │   │ Converter   │    │ Management  │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ Security    │    │ OpenAPI     │    │ Route       │              │
│  │ Manager     │    │ Generator   │    │ Generator   │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Custom API Modules                          │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ Module 1    │    │ Module 2    │    │ Module 3    │   ...        │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Components

### API Loader

The API loader is responsible for dynamically loading Python modules from the configured `apis_dir` directory. It:

- Scans for Python files and packages
- Imports the modules and processes their class definitions
- Checks compatibility with the API server
- Installs any required dependencies specified in `requirements.txt` files
- Monitors files for changes and triggers reloading when needed

### API Executor

The API executor handles the execution of API endpoints:

- Creates instances of API classes
- Processes input data and converts it to the expected types
- Executes the appropriate methods on the API classes
- Processes and converts the output data to the correct format
- Handles errors and exceptions

### Queue Manager

The queue manager handles long-running API requests:

- Maintains a queue of requests to be processed
- Assigns worker tasks to process queue items
- Manages the state of queue items
- Provides endpoints for checking queue status
- Persists queue state to disk for recovery after restart

### Security Manager

The security manager handles authentication and authorization:

- Validates API keys from the request headers
- Enforces API key-based access control
- Handles security-related error responses
- Protects API endpoints from unauthorized access

### Route Generator

The route generator creates FastAPI routes for the API endpoints:

- Creates POST routes for API endpoints
- Creates POST routes for queue status endpoints
- Handles request validation
- Maps requests to the appropriate API executor and queue manager methods

### OpenAPI Generator

The OpenAPI generator creates OpenAPI documentation for the API endpoints:

- Generates OpenAPI schemas for API inputs and outputs
- Creates documentation for API endpoints
- Provides Swagger UI for interactive API exploration

## Request Flow

1. Client makes a request to an API endpoint
2. FastAPI routes the request to the appropriate endpoint handler
3. The security manager validates the API key
4. For direct endpoints:
   - The API executor processes the request and returns the result
5. For queue endpoints:
   - The queue manager adds the request to the queue
   - The client receives a queue ID
   - The client checks the queue status using the queue ID
   - When the request is processed, the client receives the result

## Data Flow

1. Input data is received as JSON
2. The API executor converts the input data to the expected types
3. The API class processes the data
4. The API executor converts the output data to JSON
5. The response is returned to the client

## Error Handling

Errors are handled at multiple levels:

- FastAPI validation errors for request data
- API executor errors for API-specific errors
- Queue manager errors for queue-related errors
- Security manager errors for authentication errors
- Global error handler for unhandled exceptions

## Persistence

The API server persists several types of data:

- Queue state is saved to a JSON file
- Temporary files are stored in a configured directory
- Logs are stored in a configured file or streamed to the console

## Extensibility

The API server is designed to be extensible:

- New API modules can be added without modifying the core code
- The core components can be extended or replaced as needed
- The configuration can be customized for different deployment scenarios

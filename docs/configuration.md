# Configuration Guide

This guide details the configuration options for Createve.AI Nexus.

## Configuration File

The `config.yaml` file centralizes all server and MCP settings. Below is a comprehensive breakdown of all available configuration options:

### API Server Configuration

```yaml
apiserver:
  host: 0.0.0.0 # Host to listen on
  port: 43080 # Port to listen on
  debug: true # Debug to console
  log: true # Log to file
  log_file: logs/apiserver.log # Log file relative to main.py
  log_level: debug # Log level
  log_max_size: 10 # Max size of log file in MB
  apis_dir: custom_apis # Directory containing Python source for API interfaces
```

### Security Configuration

```yaml
security:
  api_keys: # List of API keys for API server access
    - key: "sk-apiservertest1"
      description: "API Key 1"
    - key: "sk-apiservertest2"
      description: "API Key 2"
```

### Processing Configuration

```yaml
processing:
  max_threads: 10 # Maximum worker threads
  max_queue_size: 100 # Maximum queued jobs
  process_timeout_seconds: 300 # Job timeout
  client_idle_timeout_seconds: 300 # Client connection timeout
  state_file: processing/state.json # State persistence file
  temp_dir: processing/tmp # Temporary file directory
  resume_on_startup: true # Resume processing from state file on startup
  clear_temp_on_startup_without_resume: true # Clear temp files on startup when not resuming
  clear_temp_files_after_processing: true # Clear temp files after job completion
  reload_on_api_dir_change: true # Monitor API directory for changes
  reload_on_api_dir_change_interval_seconds: 120 # API directory monitoring interval
  reload_on_api_file_change: true # Monitor API files for changes
  reload_on_api_file_change_interval_seconds: 120 # API file monitoring interval
  wait_for_processing_before_reload: true # Complete current jobs before reloading
```

### MCP Server Configuration

```yaml
mcp_server:
  enabled: true # Enable MCP server functionality
  server_info:
    name: "createveai-nexus" # Server name
    version: "1.0.0" # Server version
    description: "Createve.AI Nexus Server MCP Interface" # Server description
  tools:
    auto_map_apis: true # Automatically map API endpoints to MCP tools
    excluded_apis: [] # APIs to exclude from tool mapping
    additional_tools: [] # Additional tool definitions
  resources:
    expose_queue: true # Expose queue state as resources
    expose_docs: true # Expose API documentation as resources
    expose_logs: false # Expose server logs as resources
  security:
    use_api_keys: true # Use API keys for MCP authentication
    require_authentication: true # Require authentication for MCP endpoints
```

## Launch Options

The server can be started with a custom configuration file:

```bash
python main.py --config ./config.yaml
```

## Environment Variables

The following environment variables can override configuration settings:

- `APISERVER_HOST`: Override apiserver.host
- `APISERVER_PORT`: Override apiserver.port
- `APISERVER_DEBUG`: Override apiserver.debug
- `APISERVER_LOG`: Override apiserver.log
- `APISERVER_LOG_FILE`: Override apiserver.log_file
- `APISERVER_LOG_LEVEL`: Override apiserver.log_level
- `MCP_SERVER_ENABLED`: Override mcp_server.enabled
- `MCP_SERVER_NAME`: Override mcp_server.server_info.name
- `MCP_SERVER_VERSION`: Override mcp_server.server_info.version

## Security Considerations

1. API Keys:
   - Use strong, randomly generated keys
   - Rotate keys regularly
   - Limit key distribution
   - Monitor key usage

2. Network Security:
   - Configure appropriate firewall rules
   - Use TLS/HTTPS in production
   - Consider IP whitelisting
   - Keep ports secured

3. File System Security:
   - Ensure proper permissions on log files
   - Regularly clean temporary files
   - Monitor disk usage for logs and state files

4. Processing Security:
   - Set appropriate timeouts
   - Monitor thread usage
   - Implement job queuing limits
   - Enable secure resumption of processing

## Development Best Practices

1. Debugging:
   - Enable debug mode during development
   - Use appropriate log levels
   - Monitor API reloading behavior
   - Test with multiple API keys

2. API Development:
   - Place custom APIs in the configured apis_dir
   - Implement proper error handling
   - Follow the API interface guidelines
   - Test MCP tool mapping

3. State Management:
   - Test state file persistence
   - Verify queue processing
   - Validate temp file cleanup
   - Check resumption behavior

## Production Recommendations

1. Server Configuration:
   - Set debug to false
   - Configure appropriate log levels
   - Set realistic thread and queue limits
   - Enable authentication

2. Monitoring:
   - Monitor log files
   - Track queue sizes
   - Watch resource usage
   - Set up alerts

3. Security:
   - Use strong API keys
   - Enable authentication
   - Configure proper permissions
   - Regular security audits

4. Maintenance:
   - Regular log rotation
   - Temp file cleanup
   - State file backups
   - Configuration reviews

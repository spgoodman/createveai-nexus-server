# Configuration Guide

This guide details the configuration options for Createve.AI Nexus.

## Configuration File

The `config.yaml` file centralizes all server and MCP settings:

```yaml
apiserver:
  host: 0.0.0.0 # Host to listen on
  port: 43080 # Port to listen on
  debug: true # Debug to console
  log: true # Log to file
  log_file: logs/apiserver.log # Log file relative to main.py
  apis_dir: custom_apis # Directory containing API interfaces

security:
  api_keys: # List of API keys that are valid for accessing the API server
    - key: "sk-apiservertest1"
      description: "API Key 1"

mcp_server:
  enabled: true # Enable MCP server functionality
  server_info:
    name: "createveai-nexus" # Server name
    version: "1.0.0" # Server version
    description: "Createve.AI Nexus MCP Interface" # Server description
  tools:
    auto_map_apis: true # Automatically map API endpoints to MCP tools
```

## Launch Options

Alternative configuration can be specified at launch:

```bash
python main.py --config ./config.yaml
```

## Environment Variables

You can override configuration settings using environment variables:

- `APISERVER_HOST`: Override the host setting
- `APISERVER_PORT`: Override the port setting
- `APISERVER_DEBUG`: Enable/disable debug mode
- `APISERVER_LOG`: Enable/disable logging
- `APISERVER_LOG_FILE`: Specify an alternative log file path
- `MCP_SERVER_ENABLED`: Enable/disable MCP server
- `USE_KEY_VAULT`: Enable Azure Key Vault integration

## Azure Key Vault Integration

When deploying in Azure:

1. Set `USE_KEY_VAULT=true`
2. Configure managed identity for Key Vault access
3. Store sensitive configuration in Key Vault
4. Reference secrets in config.yaml using Key Vault secret names

Example Key Vault configuration:

```yaml
security:
  api_keys:
    - key: "${API_KEY_SECRET}" # References Key Vault secret
      description: "Production API Key"
```

## Security Considerations

1. API Keys:
   - Use strong, randomly generated keys
   - Rotate keys regularly
   - Limit key distribution
   - Monitor key usage

2. Network Security:
   - Configure appropriate firewall rules
   - Use TLS in production
   - Consider IP whitelisting

3. Authentication:
   - Enable API key authentication
   - Consider additional auth methods for production
   - Implement rate limiting

4. Logging:
   - Configure appropriate log levels
   - Implement log rotation
   - Monitor disk usage

## Advanced Configuration

### Queue Management

Configure queue behavior:

```yaml
processing:
  max_threads: 10 # Maximum worker threads
  max_queue_size: 100 # Maximum queued jobs
  process_timeout_seconds: 300 # Job timeout
```

### SSL/TLS Configuration

For HTTPS:

```yaml
apiserver:
  ssl_cert: "/path/to/cert.pem"
  ssl_key: "/path/to/key.pem"
```

### Custom API Directory

Configure multiple API directories:

```yaml
apiserver:
  apis_dirs:
    - custom_apis
    - more_apis
    - enterprise_apis
```

## Development Configuration

For development environments:

```yaml
apiserver:
  debug: true
  auto_reload: true
  cors_origins: ["http://localhost:3000"]
```

## Production Configuration

Recommended production settings:

```yaml
apiserver:
  debug: false
  log: true
  log_level: "INFO"
  workers: 4

security:
  require_authentication: true
  rate_limit_enabled: true
  rate_limit_requests: 100
  rate_limit_window_seconds: 60
```

## Docker Configuration

When running in Docker, use environment variables or mount a custom config file:

```bash
docker run -v $(pwd)/config.yaml:/app/config.yaml createveai/nexus
```

Or use environment variables:

```bash
docker run -e APISERVER_PORT=8080 -e API_KEY=custom-key createveai/nexus

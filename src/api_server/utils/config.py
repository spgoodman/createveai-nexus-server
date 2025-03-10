"""API Server configuration manager."""

import yaml
from ..models import APIError, APIErrorCode
from typing import List, Dict, Any

class ConfigManager:
    """Configuration manager for API Server."""
    
    def __init__(self, config_path: str = "./config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load the configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise APIError(
                APIErrorCode.API_ERROR,
                f"Failed to load configuration: {str(e)}"
            )
    
    @property
    def host(self) -> str:
        """Get API server host."""
        return self.config.get('apiserver', {}).get('host', 'localhost')
    
    @property
    def port(self) -> int:
        """Get API server port."""
        return self.config.get('apiserver', {}).get('port', 43080)
    
    @property
    def debug(self) -> bool:
        """Get debug mode flag."""
        return self.config.get('apiserver', {}).get('debug', False)
    
    @property
    def log_enabled(self) -> bool:
        """Get log enabled flag."""
        return self.config.get('apiserver', {}).get('log', False)
    
    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.config.get('apiserver', {}).get('log_file', 'logs/apiserver.log')
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.config.get('apiserver', {}).get('log_level', 'info')
    
    @property
    def apis_dir(self) -> str:
        """Get APIs directory path."""
        return self.config.get('apiserver', {}).get('apis_dir', 'custom_apis')
    
    @property
    def api_keys(self) -> List[Dict[str, str]]:
        """Get API keys."""
        return self.config.get('security', {}).get('api_keys', [])
    
    @property
    def openapi_authenticate(self) -> bool:
        """Get OpenAPI authentication required flag."""
        return self.config.get('security', {}).get('openapi_authenticate', True)
    
    @property
    def max_threads(self) -> int:
        """Get maximum number of worker threads."""
        return self.config.get('processing', {}).get('max_threads', 10)
    
    @property
    def max_queue_size(self) -> int:
        """Get maximum queue size."""
        return self.config.get('processing', {}).get('max_queue_size', 100)
    
    @property
    def process_timeout_seconds(self) -> int:
        """Get process timeout in seconds."""
        return self.config.get('processing', {}).get('process_timeout_seconds', 300)
    
    @property
    def client_idle_timeout_seconds(self) -> int:
        """Get client idle timeout in seconds."""
        return self.config.get('processing', {}).get('client_idle_timeout_seconds', 300)
    
    @property
    def state_file(self) -> str:
        """Get state file path."""
        return self.config.get('processing', {}).get('state_file', 'processing/state.json')
    
    @property
    def temp_dir(self) -> str:
        """Get temporary directory path."""
        return self.config.get('processing', {}).get('temp_dir', 'processing/tmp')
    
    @property
    def resume_on_startup(self) -> bool:
        """Get resume on startup flag."""
        return self.config.get('processing', {}).get('resume_on_startup', True)
    
    @property
    def clear_temp_on_startup_without_resume(self) -> bool:
        """Get clear temp on startup without resume flag."""
        return self.config.get('processing', {}).get('clear_temp_on_startup_without_resume', True)
    
    @property
    def clear_temp_files_after_processing(self) -> bool:
        """Get clear temp files after processing flag."""
        return self.config.get('processing', {}).get('clear_temp_files_after_processing', True)
    
    @property
    def reload_on_api_dir_change(self) -> bool:
        """Get reload on API directory change flag."""
        return self.config.get('processing', {}).get('reload_on_api_dir_change', True)
    
    @property
    def reload_on_api_dir_change_interval_seconds(self) -> int:
        """Get reload on API directory change interval in seconds."""
        return self.config.get('processing', {}).get('reload_on_api_dir_change_interval_seconds', 120)
    
    @property
    def reload_on_api_file_change(self) -> bool:
        """Get reload on API file change flag."""
        return self.config.get('processing', {}).get('reload_on_api_file_change', True)
    
    @property
    def reload_on_api_file_change_interval_seconds(self) -> int:
        """Get reload on API file change interval in seconds."""
        return self.config.get('processing', {}).get('reload_on_api_file_change_interval_seconds', 120)
    
    @property
    def wait_for_processing_before_reload(self) -> bool:
        """Get wait for processing before reload flag."""
        return self.config.get('processing', {}).get('wait_for_processing_before_reload', True)

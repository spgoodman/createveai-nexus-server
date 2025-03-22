"""Configuration handling for ComfyUI API integration."""
import os
import yaml
from typing import Dict, Any, Optional

class ComfyUIConfig:
    """Configuration manager for ComfyUI API."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize configuration with parsed YAML data."""
        self.url = config_data.get('url', 'http://localhost:8188')
        self.workflows_directory = config_data.get('workflows_directory', 'workflows')
        self.default_timeout = config_data.get('default_timeout', 300)
        self.workflows = config_data.get('workflows', {})
        
        # Ensure workflows directory exists
        os.makedirs(os.path.join(os.path.dirname(__file__), self.workflows_directory), exist_ok=True)
    
    def get_workflow_config(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific workflow."""
        return self.workflows.get(workflow_name)
    
    def get_workflow_path(self, workflow_name: str) -> Optional[str]:
        """Get full path to workflow file."""
        workflow = self.get_workflow_config(workflow_name)
        if workflow and 'file' in workflow:
            return os.path.join(os.path.dirname(__file__), 
                              self.workflows_directory, 
                              workflow['file'])
        return None
    
    def get_workflow_timeout(self, workflow_name: str) -> int:
        """Get timeout for specific workflow, falling back to default."""
        workflow = self.get_workflow_config(workflow_name)
        if workflow and 'timeout' in workflow:
            return workflow['timeout']
        return self.default_timeout
    
    def get_workflow_default_params(self, workflow_name: str) -> Dict[str, Any]:
        """Get default parameters for specific workflow."""
        workflow = self.get_workflow_config(workflow_name)
        if workflow and 'default_params' in workflow:
            return workflow['default_params']
        return {}

def load_config() -> ComfyUIConfig:
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return ComfyUIConfig(config_data)
    except Exception as e:
        raise RuntimeError(f"Failed to load ComfyUI configuration: {str(e)}")

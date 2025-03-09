"""API loader for dynamically loading API modules."""

import os
import sys
import importlib
import importlib.util
import inspect
import logging
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

from ..utils import ConfigManager
from ..models import APIError, APIErrorCode
from .compatibility import CompatibilityChecker, APICompatibility

class APILoader:
    """Loader for dynamically loading API modules."""
    
    def __init__(self, config: ConfigManager, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.apis_dir = Path(config.apis_dir)
        self.compatibility_checker = CompatibilityChecker(logger)
        
        # Store file modification times for change detection
        self.api_files_mtimes = {}
        self.requirements_files = []
    
    async def load_apis(self) -> Dict[str, Dict[str, Any]]:
        """Load all API modules from the APIs directory."""
        try:
            # Ensure APIs directory exists
            if not self.apis_dir.exists() or not self.apis_dir.is_dir():
                self.logger.error(f"APIs directory '{self.apis_dir}' does not exist or is not a directory")
                return {}
            
            # Reset file tracking
            self.api_files_mtimes = {}
            self.requirements_files = []
            
            # Install requirements if present
            await self._install_requirements()
            
            # Load API modules
            api_modules = await self._load_api_modules()
            
            # Create API registry
            apis = {}
            
            for module_name, module_data in api_modules.items():
                module = module_data.get('module')
                
                # Get node class mappings from module
                node_class_mappings = getattr(module, 'NODE_CLASS_MAPPINGS', {})
                node_display_name_mappings = getattr(module, 'NODE_DISPLAY_NAME_MAPPINGS', {})
                queue_mode_mappings = getattr(module, 'API_SERVER_QUEUE_MODE', {})
                
                # Check each class for compatibility
                for class_name, cls in node_class_mappings.items():
                    # Get display name
                    display_name = node_display_name_mappings.get(class_name, class_name)
                    
                    # Convert to valid endpoint name
                    endpoint_name = self._class_name_to_endpoint(class_name)
                    
                    # Create full API path
                    if module_name == "__main__":
                        api_path = endpoint_name
                    else:
                        api_path = f"{module_name}/{endpoint_name}"
                    
                    # Check compatibility
                    compatibility = self.compatibility_checker.check_node_compatibility(cls)
                    
                    if compatibility['status'] == APICompatibility.FULLY_COMPATIBLE:
                        # Add to registry
                        queue_mode = queue_mode_mappings.get(cls, False)
                        
                        apis[api_path] = {
                            'class': cls,
                            'class_name': class_name,
                            'display_name': display_name,
                            'module': module,
                            'module_name': module_name,
                            'queue_mode': queue_mode,
                            'compatibility': compatibility,
                            'description': getattr(cls, '__doc__', None),
                            'category': getattr(cls, 'CATEGORY', None)
                        }
                    else:
                        self.logger.warning(
                            f"API {class_name} in module {module_name} is not compatible: "
                            f"{compatibility.get('reason', 'Unknown reason')}"
                        )
            
            self.logger.info(f"Loaded {len(apis)} APIs from {len(api_modules)} modules")
            return apis
            
        except Exception as e:
            self.logger.error(f"Failed to load APIs: {str(e)}")
            return {}
    
    async def _load_api_modules(self) -> Dict[str, Dict[str, Any]]:
        """Load Python modules from APIs directory."""
        modules = {}
        
        # Add APIs directory to Python path
        sys.path.append(str(self.apis_dir))
        
        # Find all Python files
        for file_path in self.apis_dir.rglob("*.py"):
            # Skip if filename starts with underscore
            if file_path.name.startswith("_"):
                continue
            
            # Get relative path and module name
            rel_path = file_path.relative_to(self.apis_dir)
            module_name = str(rel_path.with_suffix('')).replace(os.path.sep, '.')
            
            # Track file modification time
            self.api_files_mtimes[str(file_path)] = file_path.stat().st_mtime
            
            try:
                # Import module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None or spec.loader is None:
                    self.logger.warning(f"Failed to load module {module_name} from {file_path}")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Add to registry
                modules[module_name] = {
                    'module': module,
                    'file_path': file_path
                }
                
            except Exception as e:
                self.logger.error(f"Failed to load module {module_name}: {str(e)}")
        
        # Handle __init__.py files and packages
        package_dirs = set()
        for file_path in self.apis_dir.rglob("__init__.py"):
            package_dir = file_path.parent
            package_dirs.add(package_dir)
            
            # Track file modification time
            self.api_files_mtimes[str(file_path)] = file_path.stat().st_mtime
            
            # Get package name
            rel_path = package_dir.relative_to(self.apis_dir)
            package_name = str(rel_path).replace(os.path.sep, '.')
            
            try:
                # Import package
                module = importlib.import_module(package_name)
                
                # Add to registry
                modules[package_name] = {
                    'module': module,
                    'file_path': file_path
                }
                
            except Exception as e:
                self.logger.error(f"Failed to load package {package_name}: {str(e)}")
        
        return modules
    
    async def _install_requirements(self):
        """Install requirements from requirements.txt files."""
        try:
            for req_file in self.apis_dir.rglob("requirements.txt"):
                self.requirements_files.append(req_file)
                
                try:
                    # Run pip install
                    process = await asyncio.create_subprocess_exec(
                        sys.executable, "-m", "pip", "install", "-r", str(req_file),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        self.logger.error(f"Failed to install requirements from {req_file}: {stderr.decode()}")
                    else:
                        self.logger.info(f"Installed requirements from {req_file}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to install requirements from {req_file}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Failed to install requirements: {str(e)}")
    
    async def check_for_changes(self) -> bool:
        """Check if any API files have changed."""
        try:
            # Check API files
            for file_path, mtime in list(self.api_files_mtimes.items()):
                path = Path(file_path)
                if not path.exists():
                    return True
                
                if path.stat().st_mtime > mtime:
                    return True
            
            # Check for new files
            for file_path in self.apis_dir.rglob("*.py"):
                if str(file_path) not in self.api_files_mtimes:
                    return True
            
            # Check for new requirements
            for req_file in self.apis_dir.rglob("requirements.txt"):
                if req_file not in self.requirements_files:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check for changes: {str(e)}")
            return False
    
    def _class_name_to_endpoint(self, class_name: str) -> str:
        """Convert class name to valid endpoint name."""
        # Remove spaces and special characters
        endpoint = ''.join(c if c.isalnum() else '' for c in class_name)
        
        # Ensure first character is lowercase
        if endpoint and endpoint[0].isupper():
            endpoint = endpoint[0].lower() + endpoint[1:]
        
        return endpoint

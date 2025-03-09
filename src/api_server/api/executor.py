"""API executor for executing API endpoints."""

import inspect
import logging
from typing import Dict, Any, List, Tuple, Optional

from ..models import APIError, APIErrorCode
from .converter import TypeConverter

class APIExecutor:
    """Executor for API endpoints."""
    
    def __init__(self, apis: Dict[str, Dict[str, Any]], logger: logging.Logger):
        self.apis = apis
        self.logger = logger
        self.converter = TypeConverter(logger)
    
    async def execute_api(self, api_path: str, data: dict) -> dict:
        """Execute API endpoint."""
        try:
            # Find API
            api_info = self.apis.get(api_path)
            if not api_info:
                raise APIError(
                    APIErrorCode.NOT_FOUND,
                    f"API endpoint {api_path} not found"
                )
            
            # Create instance
            cls = api_info['class']
            instance = cls()
            
            # Get input types
            input_types = self._get_input_types(cls)
            
            # Get function to execute
            function_name = getattr(cls, 'FUNCTION')
            func = getattr(instance, function_name)
            
            # Prepare arguments
            args, kwargs = await self._prepare_arguments(data, input_types)
            
            # Execute function
            try:
                result = func(*args, **kwargs)
                
                # If result is tuple, convert to dict using RETURN_NAMES
                if isinstance(result, tuple):
                    result_dict = {}
                    return_names = getattr(cls, 'RETURN_NAMES', None)
                    
                    for i, value in enumerate(result):
                        if return_names and i < len(return_names):
                            name = return_names[i]
                        else:
                            name = f"output_{i}"
                        
                        result_dict[name] = value
                    
                    result = result_dict
                
                # Process result
                processed_result = await self._process_result(result, cls)
                return processed_result
                
            except Exception as e:
                self.logger.error(f"Error executing API {api_path}: {str(e)}")
                raise APIError(
                    APIErrorCode.API_ERROR,
                    f"Error executing API: {str(e)}"
                )
        
        except APIError:
            raise
        except Exception as e:
            self.logger.error(f"Error processing API {api_path}: {str(e)}")
            raise APIError(
                APIErrorCode.API_ERROR,
                f"Error processing API: {str(e)}"
            )
    
    def _get_input_types(self, cls) -> Dict[str, Dict[str, Any]]:
        """Get input types for class."""
        try:
            input_types_method = getattr(cls, 'INPUT_TYPES')
            if callable(input_types_method):
                input_types = input_types_method()
            else:
                input_types = input_types_method
                
            return input_types
        except Exception as e:
            self.logger.error(f"Error getting input types: {str(e)}")
            return {}
    
    async def _prepare_arguments(self, data: dict, input_types: Dict[str, Dict[str, Any]]) -> Tuple[List[Any], Dict[str, Any]]:
        """Prepare arguments for function call."""
        args = []
        kwargs = {}
        
        # Process required arguments
        for field, type_info in input_types.get('required', {}).items():
            if field not in data:
                raise APIError(
                    APIErrorCode.INVALID_INPUT,
                    f"Missing required field: {field}"
                )
            
            value = data[field]
            
            # Convert if needed
            if isinstance(type_info, tuple) and len(type_info) > 0:
                type_name = type_info[0]
                
                # Check if value is base64 string for file types
                if type_name in ["IMAGE", "VIDEO", "FILE"] and isinstance(value, str):
                    value = await self.converter.convert_from_base64(value, type_name)
            
            kwargs[field] = value
        
        # Process optional arguments
        for field, type_info in input_types.get('optional', {}).items():
            if field in data:
                value = data[field]
                
                # Convert if needed
                if isinstance(type_info, tuple) and len(type_info) > 0:
                    type_name = type_info[0]
                    
                    # Check if value is base64 string for file types
                    if type_name in ["IMAGE", "VIDEO", "FILE"] and isinstance(value, str):
                        value = await self.converter.convert_from_base64(value, type_name)
                
                kwargs[field] = value
        
        return args, kwargs
    
    async def _process_result(self, result: Any, cls) -> dict:
        """Process result of function call."""
        # If result is already a dict, process each value
        if isinstance(result, dict):
            processed_result = {}
            
            # Get return types if available
            return_types = getattr(cls, 'RETURN_TYPES', None)
            return_names = getattr(cls, 'RETURN_NAMES', None)
            
            for key, value in result.items():
                # Find type for this key
                type_name = None
                if return_names and return_types:
                    try:
                        index = return_names.index(key)
                        if index < len(return_types):
                            type_name = return_types[index]
                    except ValueError:
                        pass
                
                # Convert if needed
                if type_name in ["IMAGE", "VIDEO", "FILE"]:
                    processed_result[key] = await self.converter.convert_to_base64(value, type_name)
                else:
                    processed_result[key] = value
            
            return processed_result
        
        # Otherwise, return result as is
        return result

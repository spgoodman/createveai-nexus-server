"""API compatibility checker for ComfyUI nodes."""

from enum import Enum
from typing import Dict, Any, Set
import logging

class APICompatibility(Enum):
    """API compatibility status."""
    FULLY_COMPATIBLE = "fully_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"

class CompatibilityChecker:
    """Compatibility checker for ComfyUI nodes."""
    
    # Supported data types that can be converted to/from JSON
    SUPPORTED_TYPES = {
        "STRING", "NUMBER", "FLOAT", "INTEGER", 
        "IMAGE", "VIDEO", "FILE", "BOOLEAN",
        "DICT", "LIST"
    }
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def check_node_compatibility(self, cls) -> Dict[str, Any]:
        """Checks if a ComfyUI node can be exposed as an API."""
        try:
            # Check basic structure
            if not hasattr(cls, 'INPUT_TYPES') or not hasattr(cls, 'RETURN_TYPES'):
                return {
                    'status': APICompatibility.INCOMPATIBLE,
                    'reason': 'Missing required attributes (INPUT_TYPES or RETURN_TYPES)'
                }
            
            # Check function
            if not hasattr(cls, 'FUNCTION'):
                return {
                    'status': APICompatibility.INCOMPATIBLE,
                    'reason': 'Missing FUNCTION attribute'
                }
            
            # Validate input types
            input_compatibility = self._check_input_types(cls)
            if not input_compatibility['compatible']:
                return {
                    'status': APICompatibility.INCOMPATIBLE,
                    'reason': f"Incompatible inputs: {input_compatibility['reason']}"
                }
            
            # Validate output types
            output_compatibility = self._check_output_types(cls)
            if not output_compatibility['compatible']:
                return {
                    'status': APICompatibility.INCOMPATIBLE,
                    'reason': f"Incompatible outputs: {output_compatibility['reason']}"
                }
            
            # Check dependencies
            try:
                function_name = getattr(cls, 'FUNCTION')
                if not hasattr(cls, function_name) or not callable(getattr(cls, function_name)):
                    return {
                        'status': APICompatibility.INCOMPATIBLE,
                        'reason': f"Function {function_name} not found or not callable"
                    }
            except Exception as e:
                return {
                    'status': APICompatibility.INCOMPATIBLE,
                    'reason': f"Function validation error: {str(e)}"
                }
            
            return {
                'status': APICompatibility.FULLY_COMPATIBLE,
                'convertible_inputs': input_compatibility.get('convertible', set()),
                'convertible_outputs': output_compatibility.get('convertible', set())
            }
            
        except Exception as e:
            return {
                'status': APICompatibility.INCOMPATIBLE,
                'reason': f"Validation error: {str(e)}"
            }
    
    def _check_input_types(self, cls) -> Dict[str, Any]:
        """Validates input types and identifies convertible ones."""
        try:
            input_types_method = getattr(cls, 'INPUT_TYPES')
            if callable(input_types_method):
                input_types = input_types_method()
            else:
                input_types = input_types_method
                
            convertible = set()
            
            for section in ['required', 'optional']:
                for field, type_info in input_types.get(section, {}).items():
                    if isinstance(type_info, tuple) and len(type_info) > 0:
                        type_name = type_info[0]
                        if isinstance(type_name, str) and type_name not in self.SUPPORTED_TYPES and type_name not in ["IMAGE", "VIDEO", "FILE"]:
                            return {
                                'compatible': False,
                                'reason': f"Unsupported type {type_name} for {field}"
                            }
                        if type_name in ['IMAGE', 'VIDEO', 'FILE']:
                            convertible.add(field)
                            
            return {
                'compatible': True,
                'convertible': convertible
            }
        except Exception as e:
            return {
                'compatible': False,
                'reason': f"Input types validation error: {str(e)}"
            }
    
    def _check_output_types(self, cls) -> Dict[str, Any]:
        """Validates output types and identifies convertible ones."""
        try:
            return_types = getattr(cls, 'RETURN_TYPES')
            convertible = set()
            
            if isinstance(return_types, tuple):
                for i, type_name in enumerate(return_types):
                    if type_name not in self.SUPPORTED_TYPES and type_name not in ["IMAGE", "VIDEO", "FILE"]:
                        return {
                            'compatible': False,
                            'reason': f"Unsupported return type {type_name} at position {i}"
                        }
                    if type_name in ['IMAGE', 'VIDEO', 'FILE']:
                        # Get return name if available
                        if hasattr(cls, 'RETURN_NAMES') and isinstance(cls.RETURN_NAMES, tuple) and i < len(cls.RETURN_NAMES):
                            convertible.add(cls.RETURN_NAMES[i])
                        else:
                            convertible.add(f"output_{i}")
                            
                return {
                    'compatible': True,
                    'convertible': convertible
                }
            else:
                return {
                    'compatible': False,
                    'reason': "RETURN_TYPES must be a tuple"
                }
        except Exception as e:
            return {
                'compatible': False,
                'reason': f"Output types validation error: {str(e)}"
            }

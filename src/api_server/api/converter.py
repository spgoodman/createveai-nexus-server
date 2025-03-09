"""Type conversion utilities for API inputs/outputs."""

import os
import base64
import logging
import uuid
from ..models import APIError, APIErrorCode

class TypeConverter:
    """Type converter for API inputs/outputs."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def convert_from_base64(self, value: str, type_name: str):
        """Convert base64 string to appropriate type."""
        try:
            # Decode base64
            binary_data = base64.b64decode(value)
            
            if type_name == "IMAGE":
                # Convert to image
                import numpy as np
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(binary_data))
                return np.array(image)
                
            elif type_name == "VIDEO":
                # Save to temporary file and return path
                temp_file = f"temp_{uuid.uuid4()}.mp4"
                with open(temp_file, "wb") as f:
                    f.write(binary_data)
                return temp_file
                
            elif type_name == "FILE":
                # Save to temporary file and return path
                temp_file = f"temp_{uuid.uuid4()}.bin"
                with open(temp_file, "wb") as f:
                    f.write(binary_data)
                return temp_file
                
            else:
                raise APIError(
                    APIErrorCode.API_ERROR,
                    f"Unsupported type for base64 conversion: {type_name}"
                )
                
        except APIError:
            raise
        except Exception as e:
            raise APIError(
                APIErrorCode.API_ERROR,
                f"Failed to convert from base64: {str(e)}"
            )
    
    async def convert_to_base64(self, value, type_name: str) -> str:
        """Convert value to base64 string."""
        try:
            if type_name == "IMAGE":
                # Convert numpy array to base64
                import numpy as np
                from PIL import Image
                import io
                
                if isinstance(value, np.ndarray):
                    image = Image.fromarray(value)
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    return base64.b64encode(buffer.getvalue()).decode("utf-8")
                else:
                    raise APIError(
                        APIErrorCode.API_ERROR,
                        f"Expected numpy array for IMAGE conversion, got {type(value)}"
                    )
                    
            elif type_name in ["VIDEO", "FILE"]:
                # Read file and convert to base64
                if isinstance(value, str) and os.path.exists(value):
                    with open(value, "rb") as f:
                        return base64.b64encode(f.read()).decode("utf-8")
                else:
                    raise APIError(
                        APIErrorCode.API_ERROR,
                        f"Expected file path for {type_name} conversion, got {type(value)}"
                    )
                    
            else:
                raise APIError(
                    APIErrorCode.API_ERROR,
                    f"Unsupported type for base64 conversion: {type_name}"
                )
                
        except APIError:
            raise
        except Exception as e:
            raise APIError(
                APIErrorCode.API_ERROR,
                f"Failed to convert to base64: {str(e)}"
            )

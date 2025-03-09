import requests
import json
import base64
from PIL import Image
import io

# API server configuration
api_base_url = "http://10.152.0.5:43080/api"
api_key = "sk-apiservertest1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def create_simple_image():
    """Create a very simple solid color image"""
    # Create a small solid blue image
    img = Image.new('RGB', (100, 100), color=(0, 0, 255))
    
    # Save to BytesIO
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    
    # Convert to base64 - just the raw base64 without data URL prefix
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('ascii')
    
    return img_base64  # Return raw base64 data without the data URL prefix

def test_thumbnail_generator():
    """Test the thumbnail generator API with a simple image"""
    print("Testing Thumbnail Generator API with a simple image...")
    
    # Create test image
    test_image = create_simple_image()
    print(f"Created test image with base64 length: {len(test_image)}")
    
    # Save source image for debugging
    with open("source_image.jpg", "wb") as f:
        f.write(base64.b64decode(test_image))
    print("Source image saved to source_image.jpg for verification")
    
    # Prepare request
    api_url = f"{api_base_url}/image_processing/thumbnailGenerator"
    payload = {
        "image": test_image,
        "width": 50,
        "height": 50,
        "maintain_aspect_ratio": True
    }
    
    # Make the request
    try:
        print(f"Sending request to {api_url}...")
        response = requests.post(api_url, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Thumbnail generated successfully!")
            
            # Save result if available
            if "thumbnail" in result:
                thumbnail_data = result["thumbnail"]
                
                # The response might be raw base64 or might have data URL prefix
                if thumbnail_data.startswith("data:image"):
                    _, base64_data = thumbnail_data.split(',', 1)
                else:
                    base64_data = thumbnail_data
                
                img_data = base64.b64decode(base64_data)
                
                # Save to file
                with open("simple_thumbnail.jpg", "wb") as f:
                    f.write(img_data)
                print("Saved thumbnail to simple_thumbnail.jpg")
            else:
                print("Response does not contain 'thumbnail' field")
                print(json.dumps(result, indent=2))
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_image_resizer():
    """Test the image resizer API with a simple image"""
    print("\nTesting Image Resizer API with a simple image...")
    
    # Create test image
    test_image = create_simple_image()
    
    # Prepare request
    api_url = f"{api_base_url}/image_processing/imageResizer"
    payload = {
        "image": test_image,
        "width": 200,
        "height": 200,
        "maintain_aspect_ratio": True,
        "resampling_method": "LANCZOS"
    }
    
    # Make the request
    try:
        print(f"Sending request to {api_url}...")
        response = requests.post(api_url, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Image resized successfully!")
            
            # Save result if available
            if "resized_image" in result:
                resized_data = result["resized_image"]
                
                # The response might be raw base64 or might have data URL prefix
                if resized_data.startswith("data:image"):
                    _, base64_data = resized_data.split(',', 1)
                else:
                    base64_data = resized_data
                
                img_data = base64.b64decode(base64_data)
                
                # Save to file
                with open("resized_image.jpg", "wb") as f:
                    f.write(img_data)
                print("Saved resized image to resized_image.jpg")
            else:
                print("Response does not contain 'resized_image' field")
                print(json.dumps(result, indent=2))
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

# Run the tests
if __name__ == "__main__":
    test_thumbnail_generator()
    test_image_resizer()

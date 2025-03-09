import requests
import json
import base64
import os
from PIL import Image
import io

# Define the API server base URL and credentials
api_base_url = "http://10.152.0.5:43080/api"
api_key = "sk-apiservertest1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def print_response(response):
    """Print the response in a readable format"""
    print(f"Status Code: {response.status_code}")
    print("Response:")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)
    print("\n" + "-"*50 + "\n")

def create_test_image():
    """Create a simple test image"""
    # Create a simple color gradient image
    width, height = 500, 300
    img = Image.new('RGB', (width, height))
    
    for x in range(width):
        for y in range(height):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (x + y) / (width + height))
            img.putpixel((x, y), (r, g, b))
    
    # Save to a BytesIO object
    byte_io = io.BytesIO()
    img.save(byte_io, format='JPEG', quality=95)
    byte_io.seek(0)
    
    # Encode as base64
    encoded = base64.b64encode(byte_io.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded}"

def test_text_analyzer():
    """Test the text analyzer API"""
    print("Testing Text Analyzer API:")
    api_url = f"{api_base_url}/text_processing/textAnalyzer"
    
    payload = {
        "text": "This is a test message. It's a great day! I'm very happy with the results."
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        print_response(response)
    except Exception as e:
        print(f"Error: {str(e)}")

def test_text_summarizer():
    """Test the text summarizer API with queue"""
    print("Testing Text Summarizer API (Queue Mode):")
    api_url = f"{api_base_url}/text_processing/textSummarizer"
    
    payload = {
        "text": "This is the first sentence about testing. This is a second sentence about APIs. This is a third sentence about summarization techniques. This is a fourth sentence about natural language processing. This is a fifth sentence about text analysis.",
        "summary_length": 2
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        print_response(response)
        
        result = response.json()
        
        # If we got a queue_id, check the status
        if "queue_id" in result:
            queue_id = result["queue_id"]
            print(f"Received queue_id: {queue_id}")
            print("Checking queue status...")
            
            # Check queue status
            queue_url = f"{api_url}/queue"
            queue_check_payload = {"queue_id": queue_id}
            
            # Wait for the result
            import time
            for i in range(10):  # Try 10 times
                time.sleep(2)  # Wait 2 seconds between checks
                queue_response = requests.post(queue_url, headers=headers, json=queue_check_payload)
                
                if queue_response.status_code != 200:
                    print(f"Error checking queue: {queue_response.text}")
                    break
                    
                queue_result = queue_response.json()
                
                if "queue_id" in queue_result:
                    print(f"Still processing... (attempt {i+1})")
                else:
                    print("Processing complete!")
                    print(json.dumps(queue_result, indent=2))
                    break
            else:
                print("Max attempts reached, summary might take longer to process")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_thumbnail_generator():
    """Test the thumbnail generator API"""
    print("Testing Thumbnail Generator API:")
    api_url = f"{api_base_url}/image_processing/thumbnailGenerator"
    
    # Create test image
    test_image = create_test_image()
    print(f"Created test image (base64 length: {len(test_image)})")
    
    payload = {
        "image": test_image,
        "width": 100,
        "height": 100,
        "maintain_aspect_ratio": True,
        "quality": 90,
        "format": "JPEG"
    }
    
    try:
        print("Sending request to thumbnail generator...")
        response = requests.post(api_url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response: [base64 image data not printed for brevity]")
            # Save the thumbnail to a file to verify
            result = response.json()
            if "thumbnail" in result:
                thumbnail_data = result["thumbnail"]
                if isinstance(thumbnail_data, str) and thumbnail_data.startswith("data:image"):
                    # Split off the data URL prefix
                    _, base64_data = thumbnail_data.split(',', 1)
                    img_data = base64.b64decode(base64_data)
                    
                    # Save to file
                    with open("thumbnail_test.jpg", "wb") as f:
                        f.write(img_data)
                    print("Thumbnail saved to thumbnail_test.jpg")
                else:
                    print("Unexpected thumbnail format")
            else:
                print("No thumbnail in response")
                print(json.dumps(result, indent=2))
        else:
            print(f"Error response: {response.text}")
        print("\n" + "-"*50 + "\n")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_image_resizer():
    """Test the image resizer API"""
    print("Testing Image Resizer API:")
    api_url = f"{api_base_url}/image_processing/imageResizer"
    
    # Create test image
    test_image = create_test_image()
    
    payload = {
        "image": test_image,
        "width": 200,
        "height": 200,
        "maintain_aspect_ratio": True,
        "resampling_method": "LANCZOS"
    }
    
    try:
        print("Sending request to image resizer...")
        response = requests.post(api_url, headers=headers, json=payload)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response: [base64 image data not printed for brevity]")
            # Save the resized image to a file to verify
            result = response.json()
            if "resized_image" in result:
                resized_data = result["resized_image"]
                if isinstance(resized_data, str) and resized_data.startswith("data:image"):
                    # Split off the data URL prefix
                    _, base64_data = resized_data.split(',', 1)
                    img_data = base64.b64decode(base64_data)
                    
                    # Save to file
                    with open("resized_test.jpg", "wb") as f:
                        f.write(img_data)
                    print("Resized image saved to resized_test.jpg")
                else:
                    print("Unexpected image format")
            else:
                print("No resized image in response")
                print(json.dumps(result, indent=2))
        else:
            print(f"Error response: {response.text}")
        print("\n" + "-"*50 + "\n")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test all APIs
    test_text_analyzer()
    test_text_summarizer()
    test_thumbnail_generator()
    test_image_resizer()

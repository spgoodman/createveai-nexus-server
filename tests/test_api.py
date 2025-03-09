import requests
import json

# Define the API endpoint and credentials
api_url = "http://localhost:43080/api/text_processing/textAnalyzer"
api_key = "sk-apiservertest1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Prepare the payload
payload = {
    "text": "This is a test message. It's a great day! I'm very happy with the results."
}

# Make the request
try:
    response = requests.post(api_url, headers=headers, json=payload)
    
    # Print the status code and response
    print(f"Status Code: {response.status_code}")
    print("Response:")
    
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

# Test the text summarizer endpoint (which should use the queue)
summarizer_url = "http://localhost:43080/api/text_processing/textSummarizer"
summarizer_payload = {
    "text": "This is the first sentence about testing. This is a second sentence about APIs. This is a third sentence about summarization techniques. This is a fourth sentence about natural language processing. This is a fifth sentence about text analysis.",
    "summary_length": 2
}

print("\nTesting Text Summarizer (Queue Mode):")
try:
    response = requests.post(summarizer_url, headers=headers, json=summarizer_payload)
    
    print(f"Status Code: {response.status_code}")
    print("Response:")
    
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
        
        # If we got a queue_id, check the status
        if "queue_id" in result:
            queue_id = result["queue_id"]
            print(f"\nReceived queue_id: {queue_id}")
            print("Checking queue status...")
            
            # Check queue status
            queue_url = f"{summarizer_url}/queue"
            queue_check_payload = {"queue_id": queue_id}
            
            # Wait for the result
            import time
            for _ in range(5):  # Try 5 times
                time.sleep(2)  # Wait 2 seconds between checks
                queue_response = requests.post(queue_url, headers=headers, json=queue_check_payload)
                queue_result = queue_response.json()
                
                if "queue_id" in queue_result:
                    print("Still processing...")
                else:
                    print("Processing complete!")
                    print(json.dumps(queue_result, indent=2))
                    break
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

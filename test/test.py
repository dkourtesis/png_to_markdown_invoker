import requests
import json
from datetime import datetime

def generate_payload(bucket, file_name):
    return {
        "context": {
            "eventId": "1234567890",
            "timestamp": datetime.now().isoformat() + "Z",
            "eventType": "google.storage.object.finalize",
            "resource": {
                "service": "storage.googleapis.com",
                "name": f"projects/_/buckets/{bucket}/objects/{file_name}"
            }
        },
        "data": {
            "bucket": bucket,
            "name": file_name
        }
    }

def test_function(bucket, file_name):
    payload = generate_payload(bucket, file_name)
    response = requests.post(
        "http://localhost:8080",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

# Test with different scenarios
test_function("sonnetpdfs", "80ed2cbebe229236/png/page001.png")


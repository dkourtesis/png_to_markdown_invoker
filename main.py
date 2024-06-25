import functions_framework
import requests
import os
import re
import json
from google.cloud import storage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Initialize Google Cloud Storage client
storage_client = storage.Client()

@functions_framework.cloud_event
def png_to_markdown_invoker(cloud_event):
    """Triggered by a change to a Cloud Storage bucket."""
    data = cloud_event.data

    file_name = data["name"]
    print(f"Processing file: {file_name}")

    # Validate file name pattern
    if not re.match(r'^[a-f0-9]{16}/png/page\d{3}\.png$', file_name):
        print(f"Invalid file name pattern: {file_name}")
        return

    # Construct the full GCS URI
    bucket_name = os.environ.get("STORAGE_BUCKET_NAME")
    gcs_uri = f"https://storage.googleapis.com/{bucket_name}/{file_name}"

    # Call image2md function
    try:
        result = call_image2md(gcs_uri)
        print(f"Successfully processed {file_name}")
        
        # Save the result to the bucket
        # save_result_to_bucket(result, file_name)
        
    except Exception as e:
        print(f"Error processing {file_name}: {str(e)}")
        raise

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60), retry=retry_if_exception_type(requests.RequestException))
def call_image2md(image_url):
    image2md_url = os.environ.get("IMAGE2MD_FUNCTION_URL")
    if not image2md_url:
        raise ValueError("IMAGE2MD_FUNCTION_URL environment variable is not set")

    print(f"Calling image2md function for {image_url}")
    response = requests.get(
        image2md_url,
        params={'image_url': image_url},
        timeout=540  # 9 minutes timeout
    )
    response.raise_for_status()
    return response.json()  # Parse the JSON response

def save_result_to_bucket(result, original_file_name):
    bucket_name = os.environ.get("STORAGE_BUCKET_NAME")
    bucket = storage_client.bucket(bucket_name)
    
    # Extract document ID and page number from the original file name
    parts = original_file_name.split('/')
    document_id = parts[0]
    page_number = parts[2].split('.')[0]
    
    # Save the full JSON result
    json_blob = bucket.blob(f"{document_id}/json/{page_number}.json")
    json_blob.upload_from_string(json.dumps(result), content_type='application/json')
    
    # Save the extracted narrative as markdown
    md_blob = bucket.blob(f"{document_id}/md/{page_number}.md")
    md_blob.upload_from_string(result['extracted_narrative'], content_type='text/markdown')

    print(f"Saved results for {original_file_name}")

import functions_framework
from google.cloud import storage
import json
import os
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Initialize Google Cloud Storage client
storage_client = storage.Client()

@functions_framework.cloud_event
def png_to_markdown_invoker(cloud_event):
    """Triggered by a change to a Cloud Storage bucket."""
    data = cloud_event.data

    file_name = data["name"]
    print(f"Processing file: {file_name}")

    # Construct the full GCS URI
    bucket_name = data["bucket"]
    gcs_uri = f"https://storage.googleapis.com/{bucket_name}/{file_name}"

    # Check if the current file is the first page (ends with page001.png)
    if file_name.endswith("page001.png"):
        try:
            save_markdown_file_targetlist_to_bucket(gcs_uri)
        except Exception as e:
            print(f"Error creating target list: {str(e)}")
            # Continue processing even if target list creation fails

    # Call image2md function
    try:
        result = call_image2md(gcs_uri)
        print(f"Successfully processed {file_name}")
        
    except Exception as e:
        print(f"Error processing {file_name}: {str(e)}")
        raise

def save_markdown_file_targetlist_to_bucket(gcs_uri):
    bucket_name = os.environ.get("STORAGE_BUCKET_NAME")
    bucket = storage_client.bucket(bucket_name)
    
    print(f"Bucket name: {bucket_name}")
    print(f"Full GCS URI: {gcs_uri}")
    
    # Extract document ID from the gcs_uri
    document_id = gcs_uri.split('/')[4]
    print(f"Extracted document ID: {document_id}")
    
    # Construct the metadata file path
    metadata_file_path = f"{document_id}/process/"
    
    # List all blobs in the process directory
    process_blobs = list(bucket.list_blobs(prefix=metadata_file_path))
    
    if not process_blobs:
        print(f"Error: No files found in {metadata_file_path}")
        return
    
    # Find the latest pdf2images file
    pdf2images_blobs = [blob for blob in process_blobs if 'pdf2images_' in blob.name]
    if not pdf2images_blobs:
        print(f"Error: No pdf2images file found in {metadata_file_path}")
        return
    
    latest_metadata_blob = max(pdf2images_blobs, key=lambda x: x.name)
    print(f"Latest metadata file found: {latest_metadata_blob.name}")
    
    try:
        # Read the metadata file
        metadata_content = json.loads(latest_metadata_blob.download_as_text())
        total_pages = metadata_content.get('total_pages')
        
        if not total_pages:
            print("Error: 'total_pages' not found in metadata file")
            print(f"Metadata file content: {metadata_content}")
            return
        
        print(f"Total pages found in metadata: {total_pages}")
        
        # Create the list of target URLs
        markdown_file_target_list = [
            f"https://storage.googleapis.com/{bucket_name}/{document_id}/md/page{str(i).zfill(3)}.md"
            for i in range(1, total_pages + 1)
        ]
        
        # Prepare the output JSON
        output_json = {
            "processing_start_time": datetime.now().isoformat(),
            "total_pages": total_pages,
            "markdown_file_target_list": markdown_file_target_list
        }
        
        # Save the output JSON
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = f"{document_id}/process/png_to_markdown_invoker_{current_time}.json"
        output_blob = bucket.blob(output_file_path)
        output_blob.upload_from_string(json.dumps(output_json, indent=2, ensure_ascii=False), content_type='application/json')
        
        print(f"Saved markdown file target list to {output_file_path}")
        
    except Exception as e:
        print(f"An error occurred while processing the metadata file: {str(e)}")
        import traceback
        print(traceback.format_exc())

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

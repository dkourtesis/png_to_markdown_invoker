# PNG to Markdown Invoker

This Google Cloud Function is triggered when a new PNG file is uploaded to a specified Google Cloud Storage bucket. It processes the PNG file by calling an image-to-markdown conversion function and saves the results.

## Project Structure

- `main.py`: The main Python script containing the Cloud Function code.
- `requirements.txt`: Lists all Python dependencies required for the project.
- `.env`: Contains environment variables for local development (not to be committed to version control).
- `.env.yaml`: Specifies environment variables for deployment to Google Cloud Platform.
- `.gcloudignore`: Tells Google Cloud what files to ignore when deploying the function.
- `venv/`: Virtual environment directory (generated, not to be committed).

## Setup Instructions

### Setting up the project in VS Code

1. Open the project folder in VS Code.
2. Open a new terminal in VS Code (Terminal > New Terminal).
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```
     .\venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```
5. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
6. To deactivate the virtual environment when you're done:
   ```
   deactivate
   ```

Note: In case dependencies VS Code cannot find some dependencies, despite you are sure you have them installed, and they show up when running pip list, make sure the correct interpreter has been selected. Ctrl+Shift+P -> Python: Select Interpreter -> Enter interpreter path -> Find / Browse your file system to find a Python interpreter -> venv/Scrips/Python.exe

### Testing the Function Locally

1. Ensure your virtual environment is activated.
2. Set up your Google Cloud credentials:
   - Download your service account key JSON file.
   - Set the GOOGLE_APPLICATION_CREDENTIALS environment variable:
     - Windows PowerShell:
       ```
       $env:GOOGLE_APPLICATION_CREDENTIALS="path\to\your\service-account-key.json"
       ```
     - Linux/macOS:
       ```
       export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
       ```
3. Run the Functions Framework:
   ```
   functions-framework --target png_to_markdown_invoker --signature-type cloudevent
   ```
4. In another terminal, send a test POST request:

   - Windows PowerShell:
     ```powershell
     Invoke-WebRequest -Uri "http://localhost:8080/" `
       -Method POST `
       -Headers @{"Content-Type"="application/json"} `
       -Body '{"context": {"eventId":"1234567890","timestamp":"2023-04-23T07:00:00Z","eventType":"google.storage.object.finalize","resource":{"service":"storage.googleapis.com","name":"projects/_/buckets/sonnetpdfs/objects/3c64b0ab04ce0d54/png/page010.png"}},"data": {"bucket": "sonnetpdfs","name": "3c64b0ab04ce0d54/png/page010.png"}}'
     ```

   - Linux/macOS (using curl):
     ```bash
     curl -X POST http://localhost:8080/ \
       -H "Content-Type: application/json" \
       -d '{"context": {"eventId":"1234567890","timestamp":"2023-04-23T07:00:00Z","eventType":"google.storage.object.finalize","resource":{"service":"storage.googleapis.com","name":"projects/_/buckets/sonnetpdfs/objects/3c64b0ab04ce0d54/png/page010.png"}},"data": {"bucket": "sonnetpdfs","name": "3c64b0ab04ce0d54/png/page010.png"}}'
     ```

These commands will send a simulated Cloud Storage event to your locally running function, allowing you to test its behavior.

### Deploying the Function to GCP

1. Ensure you have the Google Cloud SDK installed and configured.
2. Open a terminal and navigate to your project directory.
3. Deploy the function using the following command:
   ```
   gcloud functions deploy png_to_markdown_invoker `
   --runtime python312 `
   --region us-central1 `
   --trigger-event google.storage.object.finalize `
   --trigger-resource sonnetpdfs `
   --entry-point png_to_markdown_invoker `
   --env-vars-file .env.yaml `
   --project experiments-422206
   ```
4. Wait for the deployment to complete. GCP will provide a URL for your deployed function.

Remember to replace any placeholder values (like project IDs or bucket names) with your actual values before deploying.

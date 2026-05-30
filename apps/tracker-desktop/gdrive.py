import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Define the highly restrictive scope you selected
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Your provided dummy credentials structured for the Google OAuth library
CLIENT_CONFIG = {
    "installed": {
        "client_id": "YOUR-CLIENT-ID-HERE",
        "client_secret": "YOUR-CLIENT-SECRET-HERE",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
}

def get_gdrive_service():
    """Handles authentication and returns the Google Drive API client service."""
    creds = None
    # 'token.json' stores the user's access and refresh tokens after the first login
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            # This opens a local browser window for authentication
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def create_folder(service, folder_name):
    """Creates a dedicated folder. Since this app creates it, it can manage it under drive.file."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"📁 Folder Created! Name: '{folder_name}' | ID: {folder.get('id')}")
    return folder.get('id')

def upload_file(service, local_file_path, target_folder_id=None):
    """Uploads a local file to the specified Google Drive folder."""
    filename = os.path.basename(local_file_path)
    file_metadata = {'name': filename}
    
    if target_folder_id:
        file_metadata['parents'] = [target_folder_id]
        
    media = MediaFileUpload(local_file_path, mimetype='video/mp4', resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    
    print(f"📤 Upload Complete! File: '{file.get('name')}' | ID: {file.get('id')}")
    return file.get('id')

def list_files(service):
    """Lists files that this application has access to under drive.file scope."""
    print("\n🔍 Fetching visible files...")
    results = service.files().list(
        pageSize=10, 
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print('No files found (or app doesn\'t have access to existing ones).')
    else:
        print('Files:')
        for item in items:
            print(f" - {item['name']} ({item['id']}) [{item['mimeType']}]")

def download_file(service, file_id, destination_path):
    """Downloads a file by its Google Drive File ID."""
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    print(f"\n📥 Downloading file ID {file_id}...")
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Progress: {int(status.progress() * 100)}%")
        
    # Save bytes to local file
    fh.seek(0)
    with open(destination_path, 'wb') as f:
        f.write(fh.read())
    print(f"💾 File downloaded locally to: {destination_path}")

# --- Execution Flow Example ---
if __name__ == '__main__':
    # 1. Initialize Service (Will prompt browser login on the very first run)
    drive_service = get_gdrive_service()
    
    # Create a dummy file locally to test the system
    test_filename = "sample_interview.mp4"
    with open(test_filename, "wb") as f:
        f.write(b"Dummy video packet data structure stream")

    # 2. Setup your app-owned isolated folder
    folder_id = create_folder(drive_service, "AI_Interviews_Vault")
    
    # 3. Upload file into that brand new folder
    uploaded_file_id = upload_file(drive_service, test_filename, target_folder_id=folder_id)
    
    # 4. View / List files (You will notice only the folder and file we created show up)
    list_files(drive_service)
    
    # 5. Download the file back to verify integrity
    download_file(drive_service, uploaded_file_id, "downloaded_interview_test.mp4")
    
    # Clean up local root test file
    if os.path.exists(test_filename):
        os.remove(test_filename)
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    """Get credentials from environment variables"""
    creds_json = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["http://localhost"]
        }
    }
 # Write temporary credentials file
    with open('credentials.json', 'w') as f:
        json.dump(creds_json, f)

    # Rest of your credential logic
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

def find_or_create_folder(service,folder_name,parent_id=None):
    """Find or create a folder in Google Drive"""
    # Search for the folder
     # Search query
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    response = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute() 
    
    if response.get('files'):
        return response['files'][0]['id']
    
    else:
        # Create the folder if it doesn't exist
        file_metadata = {
            'name':folder_name,
            'mimeType':'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        file = service.files().create(
        body=file_metadata,
        fields='id'
        ).execute()
        return file.get('id')
    
def upload_picture(picture_path,folder_name=None,parent_folder_name="FM_BOT"):
    """Upload a picture to Google Drive"""
    try:
        creds = get_credentials()
        service = build('drive','v3',credentials=creds)
        
        # Find or create the folder
        folder_id = find_or_create_folder(service,parent_folder_name)
        if folder_name:
            file_metadata = {
                'name':folder_name,
                'mimeType':'application/vnd.google-apps.folder',
                'parents':[folder_id]
            }

            folder = service.files().create(
                body=file_metadata,
                fields = 'id'
            ).execute()
            target_folder_id = folder.get('id')
        else:
            target_folder_id = folder_id

        file_metadata = {
            'name':os.path.basename(picture_path),
            'parents':[target_folder_id]
        }
        # Upload the picture
        media = MediaFileUpload(
            picture_path,
            mimetype='image/jpeg',
            resumable=True
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()

        return {
            'file_id':file.get('id'),
            'file_name':file.get('name'),
            'file_link':file.get('webViewLink'),
            'folder_name': folder_name if folder_name else parent_folder_name
        } 
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
    
def get_image_files(directory):
    """Get all image files from a directory"""
    image_extensions = ['.jpg','.jpeg','.png','.gif','.bmp','.tiff']
    image_files = []

    for file in os.listdir(directory):
        if file.lower().endswith(tuple(image_extensions)):
            image_files.append(os.path.join(directory,file))
    return image_files




def main():
    picture_path = '/Users/deardevx/Documents/my_stufF/bot/ai_telegram/pictures'
    image_files = get_image_files(picture_path)

    # Get credentials and build service once
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    # First create the parent folder (FM_BOT)
    parent_folder_id = find_or_create_folder(service, "FM_BOT")
    
    # Create the target folder inside FM_BOT
    folder_metadata = {
        'name': 'deardevx',  # You can change this name to whatever you want
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()
    target_folder_id = folder.get('id')
    
    # Upload all images to this folder
    results = []
    for picture_path in image_files:
        try:
            file_metadata = {
                'name': os.path.basename(picture_path),
                'parents': [target_folder_id]
            }
            
            media = MediaFileUpload(
                picture_path,
                mimetype='image/jpeg',
                resumable=True
            )

            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()

            result = {
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'file_link': file.get('webViewLink')
            }
            
            results.append(result)
            print(f"Uploaded: {result['file_name']}")
        except HttpError as error:
            print(f"Failed to upload {picture_path}: {error}")
    
    print(f"\nTotal files uploaded: {len(results)}")

     
if __name__ == '__main__':
    main()